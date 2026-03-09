"""
ZK Oracle — Data Analyzer
===========================
Analyzes price data and computes metrics (like moving averages).
Produces a deterministic, hashable output — critical for ZK proofs!

LEARNING NOTES:
- Deterministic output is KEY for ZK: same input → same output every time
- We avoid floating point issues by rounding to 8 decimal places
- The OracleReport is a Pydantic model for type safety & serialization
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone


class OracleReport(BaseModel):
    """
    The final output of the AI agent's analysis.
    This gets sent to the Rust ZK prover.

    Must match the OracleReport struct in circuits/methods/guest/src/main.rs!
    """
    asset: str = Field(description="Cryptocurrency name, e.g., 'bitcoin'")
    price_usd: float = Field(description="Current price in USD")
    moving_average: float = Field(description="Simple moving average")
    source: str = Field(description="Data source URL")
    timestamp: int = Field(description="UNIX timestamp of data fetch")
    analysis: str = Field(description="AI agent's analysis summary")


def compute_moving_average(prices: List[List[float]], window: int = 7) -> float:
    """
    Compute a simple moving average from price history.

    Args:
        prices: List of [timestamp_ms, price] pairs from CoinGecko
        window: Number of data points to average (default: last 7)

    Returns:
        The simple moving average, rounded to 8 decimal places
    """
    if not prices or len(prices) == 0:
        return 0.0

    # Take the last `window` prices
    recent_prices = [p[1] for p in prices[-window:]]
    avg = sum(recent_prices) / len(recent_prices)

    # Round for determinism (floating point can vary across platforms)
    return round(avg, 8)


def create_oracle_report(
    price_data: dict,
    history_data: dict,
    analysis_text: str = "",
) -> OracleReport:
    """
    Combine price data, history, and AI analysis into an OracleReport.

    Args:
        price_data: Output from data_fetcher.fetch_price()
        history_data: Output from data_fetcher.fetch_price_history()
        analysis_text: AI agent's analysis summary

    Returns:
        OracleReport ready for ZK proof generation
    """
    moving_avg = compute_moving_average(history_data["prices"])

    return OracleReport(
        asset=price_data["asset"],
        price_usd=round(price_data["price"], 8),
        moving_average=moving_avg,
        source=price_data["source"],
        timestamp=price_data["timestamp"],
        analysis=analysis_text or f"{price_data['asset']} is at ${price_data['price']:,.2f}",
    )


if __name__ == "__main__":
    # Quick test with mock data
    mock_prices = [[i * 86400000, 60000 + i * 100] for i in range(10)]
    avg = compute_moving_average(mock_prices, window=5)
    print(f"Mock moving average: ${avg:,.2f}")
