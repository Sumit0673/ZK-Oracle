from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone


class OracleReport(BaseModel):

    asset: str = Field(description="Cryptocurrency name, e.g., 'bitcoin'")
    price_usd: float = Field(description="Current price in USD")
    moving_average: float = Field(description="Simple moving average")
    source: str = Field(description="Data source URL")
    timestamp: int = Field(description="UNIX timestamp of data fetch")
    analysis: str = Field(description="AI agent's analysis summary")


def compute_moving_average(prices: List[List[float]], window: int = 7) -> float:

    if not prices or len(prices) == 0:
        return 0.0

    recent_prices = [p[1] for p in prices[-window:]]
    avg = sum(recent_prices) / len(recent_prices)

    return round(avg, 8)


def create_oracle_report(
    price_data: dict,
    history_data: dict,
    analysis_text: str = "",
) -> OracleReport:

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
    mock_prices = [[i * 86400000, 60000 + i * 100] for i in range(10)]
    avg = compute_moving_average(mock_prices, window=5)
    print(f"Mock moving average: ${avg:,.2f}")
