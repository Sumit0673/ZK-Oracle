"""
ZK Oracle — Interactive Demo
==============================
Run this to test each component step-by-step with colored output.
Usage: python demo.py [--skip-agent]

This is your learning companion — it shows you exactly what each
component does, step by step, with real data.
"""

import json
import sys
import time


def print_header(step: int, title: str):
    print(f"\n{'='*60}")
    print(f"  Step {step}: {title}")
    print(f"{'='*60}\n")


def print_result(label: str, value):
    print(f"  {label}: {value}")


def main():
    skip_agent = "--skip-agent" in sys.argv

    print("\n🔮 ZK-Verified AI Oracle — Interactive Demo")
    print("=" * 60)

    # ── Step 1: Data Fetcher ──
    print_header(1, "Fetch Live Crypto Data (data_fetcher.py)")
    print("  📡 Calling CoinGecko API for Bitcoin price...\n")

    from data_fetcher import fetch_price, fetch_price_history

    try:
        price = fetch_price("bitcoin")
        print_result("  Asset", price["asset"])
        print_result("  💰 Price", f"${price['price']:,.2f}")
        print_result("  📈 24h Change", f"{price['change_24h']:.2f}%")
        print_result("  🕐 Timestamp", price["timestamp"])
        print_result("  🔗 Source", price["source"])
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("  ℹ️  CoinGecko may be rate-limiting. Wait 60s and retry.")
        return

    time.sleep(1)  # Be nice to the API

    # ── Step 2: Price History ──
    print_header(2, "Fetch Price History (data_fetcher.py)")
    print("  📊 Fetching 7-day Bitcoin price history...\n")

    try:
        history = fetch_price_history("bitcoin", days=7)
        prices = [p[1] for p in history["prices"]]
        print_result("  Data Points", len(prices))
        print_result("  📉 Min Price", f"${min(prices):,.2f}")
        print_result("  📈 Max Price", f"${max(prices):,.2f}")
        print_result("  📊 Avg Price", f"${sum(prices)/len(prices):,.2f}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return

    time.sleep(1)

    # ── Step 3: Analyzer ──
    print_header(3, "Analyze Data & Create Oracle Report (analyzer.py)")
    print("  🧮 Computing moving average & building report...\n")

    from analyzer import compute_moving_average, create_oracle_report

    ma = compute_moving_average(history["prices"], window=7)
    print_result("  Moving Average (7-pt)", f"${ma:,.2f}")

    report = create_oracle_report(
        price, history,
        analysis_text=f"Bitcoin is at ${price['price']:,.2f}, "
                      f"{'above' if price['price'] > ma else 'below'} "
                      f"its 7-day moving average of ${ma:,.2f}."
    )

    print(f"\n  📋 Oracle Report (JSON → sent to ZK prover):")
    print("  " + "-" * 50)
    report_json = json.loads(report.model_dump_json(indent=2))
    for key, value in report_json.items():
        print(f"    {key}: {value}")

    # ── Step 4: LangChain Agent ──
    if skip_agent:
        print_header(4, "LangChain Agent (SKIPPED)")
        print("  ℹ️  Use --skip-agent flag removed to test the agent")
        print("  ℹ️  Requires OPENAI_API_KEY in agent/.env")
    else:
        print_header(4, "LangChain AI Agent (agent.py)")
        print("  🤖 Starting AI agent — watch it think & call tools...\n")

        try:
            from agent import run_oracle
            agent_report = run_oracle("bitcoin")
            print(f"\n  📊 Agent's Oracle Report:")
            print("  " + "-" * 50)
            agent_json = json.loads(agent_report.model_dump_json(indent=2))
            for key, value in agent_json.items():
                print(f"    {key}: {value}")
        except Exception as e:
            print(f"  ❌ Agent error: {e}")
            print("  ℹ️  Make sure OPENAI_API_KEY is set in agent/.env")

    # ── Summary ──
    print(f"\n{'='*60}")
    print("  ✅ Demo Complete!")
    print(f"{'='*60}")
    print(f"\n  Next steps:")
    print(f"    1. Edit agent/.env with your OPENAI_API_KEY")
    print(f"    2. Run: python demo.py  (full demo with AI agent)")
    print(f"    3. Run: python -m pytest tests/ -v  (run all tests)")
    print(f"    4. Phase 3: Build the ZK circuits in Rust!\n")


if __name__ == "__main__":
    main()
