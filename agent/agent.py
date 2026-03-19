import json
import re
import sys
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
import os
try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    try:
        from langchain_classic.agents.agent import AgentExecutor
        from langchain_classic.agents.tool_calling_agent.base import create_tool_calling_agent
    except ImportError:
        from langchain.agents.agent import AgentExecutor
        from langchain.agents.agent_toolkits import create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate

from data_fetcher import fetch_price, fetch_price_history
from analyzer import compute_moving_average, create_oracle_report, OracleReport

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
def generate_oracle_report(asset: str = "bitcoin", analysis: str = "") -> str:
    """Generate a final oracle report for the given asset.
    Call this AFTER using get_crypto_price and get_price_history.
    This creates the structured report that will be sent for ZK proof generation.
    Args:
        asset: The cryptocurrency name
        analysis: Your analysis summary of the price data and trends
    """
    try:
        price_data = fetch_price(asset)
        history_data = fetch_price_history(asset, days=7)
        report = create_oracle_report(price_data, history_data, analysis)
        return report.model_dump_json(indent=2)
    except Exception as e:
        return f"Error generating report: {str(e)}"



def create_oracle_agent() -> AgentExecutor:
    """Create and return the LangChain oracle agent."""
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

    tools = [get_crypto_price, get_price_history, generate_oracle_report]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a ZK Oracle Agent. Your job is to:
1. Fetch current cryptocurrency price data
2. Analyze price trends using historical data
3. Generate a verified oracle report

Always follow this workflow:
1. First, fetch the current price using get_crypto_price
2. Then, get the price history using get_price_history
3. Analyze the data and form your analysis
4. Finally, generate the oracle report using generate_oracle_report

Be precise and factual. Your output will be cryptographically verified.
CRITICAL INSTRUCTION: Do NOT include any disclaimers, notes, or warnings about "sample data used", "market data may vary", or similar boilerplate. Output ONLY your direct analysis."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )


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
    """
    Run the full oracle agent pipeline for a given asset.

    Args:
        asset: Cryptocurrency to analyze (default: "bitcoin")

    Returns:
        OracleReport with verified data
    """
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
        "input": f"Analyze the current price and 7-day trend for {asset}. "
                 f"Then generate an oracle report with your analysis."
    })

    output = result["output"]
    try:
        match = re.search(r'\{.*\}', output, re.DOTALL)
        if match:
            report = OracleReport.model_validate_json(match.group(0))
        else:
            report = OracleReport.model_validate_json(output)
    except Exception:
        print("⚠️  Agent did not return a structured report, falling back to manual fetch...")
        try:
            clean_analysis = re.sub(r'```json.*?```', '', output, flags=re.DOTALL)
            clean_analysis = re.sub(r'\{.*?\}', '', clean_analysis, flags=re.DOTALL).strip()
            clean_analysis = re.sub(r'(?i)the oracle report.*?as follows:?', '', clean_analysis).strip()
            
            report = create_oracle_report(
                fetch_price(asset),
                fetch_price_history(asset),
                analysis_text=clean_analysis
            )
        except Exception as e:
            if "429" in str(e):
                print("❌ Error: Rate limited by CoinGecko. Please try again in 1-2 minutes.")
                raise RuntimeError("Rate limited by CoinGecko. Please try again in 1-2 minutes.")
            else:
                print(f"❌ Error fetching data: {e}")
                raise RuntimeError(f"Error fetching data: {e}")

    return report


if __name__ == "__main__":
    print("🤖 Starting ZK Oracle Agent...")
    print("=" * 50)
    report = run_oracle("bitcoin")
    print("\n" + "=" * 50)
    print("📊 Oracle Report:")
    print(report.model_dump_json(indent=2))
