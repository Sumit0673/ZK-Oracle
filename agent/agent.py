import json
import re
import sys
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
import os
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate

from langgraph.checkpoint.memory import MemorySaver

from data_fetcher import fetch_price, fetch_price_history, fetch_news
from analyzer import compute_moving_average, compute_rsi, compute_macd, create_oracle_report, OracleReport

load_dotenv()



@tool
def get_crypto_price(asset: str = "bitcoin") -> str:
    """Fetch the current price of a cryptocurrency from CoinGecko.
    Use this to get real-time price data for any crypto asset.
    Args:
        asset: The cryptocurrency name (e.g., 'bitcoin', 'ethereum', 'solana')
    """
    try:
        data = fetch_price(asset)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error fetching price: {str(e)}"


@tool
def get_price_history(asset: str = "bitcoin", days: int = 7) -> str:
    """Fetch price history for a cryptocurrency to compute trends.
    Use this to get historical prices for moving average calculations.
    Args:
        asset: The cryptocurrency name
        days: Number of days of history (7, 14, 30, 90)
    """
    try:
        data = fetch_price_history(asset, days)
        prices = [p[1] for p in data["prices"]]
        summary = {
            "asset": asset,
            "days": days,
            "data_points": len(prices),
            "min_price": round(min(prices), 2),
            "max_price": round(max(prices), 2),
            "avg_price": round(sum(prices) / len(prices), 2),
            "latest_price": round(prices[-1], 2),
            "moving_average_7d": round(compute_moving_average(data["prices"], 7), 2),
        }
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error fetching history: {str(e)}"


@tool
def get_crypto_news(asset: str = "bitcoin") -> str:
    """Fetch current news headlines and market sentiment for a cryptocurrency.
    Use this to understand the market context before writing your analysis.
    Args:
        asset: The cryptocurrency name
    """
    try:
        data = fetch_news(asset)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error fetching news: {str(e)}"


@tool
def analyze_technical_indicators(asset: str = "bitcoin") -> str:
    """Compute advanced technical indicators (RSI and MACD) for a cryptocurrency.
    Use this to identify overbought/oversold conditions and momentum trends.
    Args:
        asset: The cryptocurrency name
    """
    try:
        data = fetch_price_history(asset, days=40)
        prices = data["prices"]
        
        rsi = compute_rsi(prices)
        macd_data = compute_macd(prices)
        
        result = {
            "asset": asset,
            "rsi_14d": rsi,
            "macd": macd_data,
            "interpretation": {
                "rsi": "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral",
                "macd": "Bullish Momentum" if macd_data["histogram"] > 0 else "Bearish Momentum"
            }
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error computing indicators: {str(e)}"


def create_oracle_agent():
    """Create and return the LangGraph oracle agent."""
    # The LLM (brain of the agent)
    # Prioritize Groq for production/cloud deployment
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        print("💡 Using Groq API (Cloud)...")
        llm = ChatGroq(
            model_name="llama-3.1-8b-instant", 
            temperature=0,
            groq_api_key=groq_api_key
        )
    else:
        print("💡 Using Ollama (Local)...")
        llm = ChatOllama(model="llama3.1", temperature=0)

    tools = [get_crypto_price, get_price_history, get_crypto_news, analyze_technical_indicators]

    system_prompt = """You are a ZK Oracle Agent. Your job is to:
1. Fetch current cryptocurrency price data
2. Get the recent news and sentiment
3. Analyze price trends using historical data, RSI, and MACD technical indicators
4. Generate a verified oracle report

Always follow this workflow:
1. Fetch the current price using get_crypto_price
2. Fetch the price history using get_price_history
3. Fetch technical analysis data using analyze_technical_indicators
4. Fetch the latest news using get_crypto_news
5. Analyze all the data (Price, Trend, Indicators, and Sentiment) and form your combined analysis. Format your analysis exactly using these uppercase tags:
[SENTIMENT]
(your sentiment analysis)
[NEWS]
(your news summary)
[TECHNICALS]
(your technical analysis)
[CONCLUSION]
(your overall conclusion)
6. Finally, YOU MUST respond by returning a raw JSON block matching this exact schema:
{
  "asset": "string",
  "price_usd": 12345.67,
  "moving_average": 12345.67,
  "source": "string",
  "timestamp": 1234567890,
  "analysis": "string containing the full tagged analysis from step 5"
}

Be precise and factual. Your output will be cryptographically verified.
CRITICAL INSTRUCTION: Do NOT include any disclaimers! Output ONLY the JSON block at the end."""

    memory = MemorySaver()
    return create_react_agent(llm, tools=tools, prompt=system_prompt, checkpointer=memory)


def check_llm_connectivity() -> bool:
    """Check if the configured LLM provider is available."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        # Simple key check for Groq
        return len(groq_api_key) > 10
    
    # Fallback to local Ollama check
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/tags")
        return response.status_code == 200
    except Exception:
        return False


def run_oracle(asset: str = "bitcoin") -> OracleReport:
    
    if not check_llm_connectivity():
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            print("❌ Error: Groq API key is invalid or not working.")
            raise RuntimeError("Groq API key is invalid or not working.")
        else:
            print("❌ Error: Cannot connect to Ollama service.")
            print("ℹ️  Make sure Ollama is running OR provide a GROQ_API_KEY in .env.")
            raise RuntimeError("Cannot connect to local Ollama. Please run 'ollama serve' or provide GROQ_API_KEY.")

    agent = create_oracle_agent()

    result = agent.invoke({
        "messages": [("user", f"Analyze the current price, 7-day trend, and news sentiment for {asset}. "
                              f"Then generate an oracle report with your combined analysis.")]
    }, config={"configurable": {"thread_id": "1"}})

    if "structured_response" in result and result["structured_response"]:
        report = result["structured_response"]
        if isinstance(report, dict):
            return OracleReport(**report)
        return report
        
    # LangGraph fallback mechanism if structured_response isn't present
    output = result["messages"][-1]
    
    if hasattr(output, "tool_calls") and len(output.tool_calls) > 0:
        return OracleReport(**output.tool_calls[0]["args"])
        
    # Parse JSON from content
    content = output.content
    try:
        # Fallback simple regex for json
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            json_str = match.group(0)
            return OracleReport.model_validate_json(json_str)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        
    raise RuntimeError(f"Agent failed to output strict structured format. Raw output: {content}")


if __name__ == "__main__":
    print("🤖 Starting ZK Oracle Agent...")
    print("=" * 50)
    report = run_oracle("bitcoin")
    print("\n" + "=" * 50)
    print("📊 Oracle Report Analysis:")
    
    analysis_text = report.analysis
    
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        
        console = Console()
        
        sections = {"SENTIMENT": "", "NEWS": "", "TECHNICALS": "", "CONCLUSION": ""}
        
        # Parse the tags robustly using regex
        import re
        parts = re.split(r'\[(SENTIMENT|NEWS|TECHNICALS|CONCLUSION)\]', analysis_text)
        if len(parts) > 1:
            for i in range(1, len(parts), 2):
                tag = parts[i]
                content = parts[i+1].strip()
                if content:
                    sections[tag] = content
        else:
            sections["CONCLUSION"] = analysis_text
                
        # Print panels
        if any(sections.values()):
            if sections["SENTIMENT"].strip():
                console.print(Panel(sections["SENTIMENT"].strip(), title="[bold cyan]Sentiment[/bold cyan]", border_style="cyan"))
            if sections["NEWS"].strip():
                console.print(Panel(sections["NEWS"].strip(), title="[bold blue]News[/bold blue]", border_style="blue"))
            if sections["TECHNICALS"].strip():
                console.print(Panel(sections["TECHNICALS"].strip(), title="[bold magenta]Price & Technicals[/bold magenta]", border_style="magenta"))
            if sections["CONCLUSION"].strip():
                console.print(Panel(sections["CONCLUSION"].strip(), title="[bold green]Overall Conclusion[/bold green]", border_style="green"))
        else:
            # Fallback if the agent didn't use tags
            console.print(Panel(analysis_text, title="[bold green]Analysis[/bold green]", border_style="green"))
            
    except ImportError:
        # Fallback if 'rich' is not installed
        print("\n--- Sentiment ---\n" + sections.get("SENTIMENT", ""))
        print("\n--- News ---\n" + sections.get("NEWS", ""))
        print("\n--- Price & Technicals ---\n" + sections.get("TECHNICALS", ""))
        print("\n--- Conclusion ---\n" + sections.get("CONCLUSION", ""))
        
    print("\n📦 Raw JSON Payload (for ZK Circuit):")
    print(report.model_dump_json(indent=2))
