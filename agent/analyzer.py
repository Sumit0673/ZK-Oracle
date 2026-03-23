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


def compute_rsi(prices: List[List[float]], window: int = 14) -> float:
    """Calculate Relative Strength Index (RSI)."""
    if not prices or len(prices) <= window:
        return 50.0  # Neutral default if not enough data
        
    closes = [p[1] for p in prices]
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change >= 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))
            
    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window
    
    for i in range(window, len(gains)):
        avg_gain = (avg_gain * (window - 1) + gains[i]) / window
        avg_loss = (avg_loss * (window - 1) + losses[i]) / window
        
    if avg_loss == 0:
        return 100.0
        
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


def compute_ema(prices: List[float], days: int) -> List[float]:
    """Helper for MACD: Exponential Moving Average."""
    k = 2 / (days + 1)
    ema = [prices[0]]
    for price in prices[1:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema


def compute_macd(prices: List[List[float]], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    if not prices or len(prices) <= slow + signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        
    closes = [p[1] for p in prices]
    ema_fast = compute_ema(closes, fast)
    ema_slow = compute_ema(closes, slow)
    
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    
    valid_macd = macd_line[slow-1:]
    if len(valid_macd) < signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        
    signal_line = compute_ema(valid_macd, signal)
    
    current_macd = macd_line[-1]
    current_signal = signal_line[-1]
    
    return {
        "macd": round(current_macd, 2),
        "signal": round(current_signal, 2),
        "histogram": round(current_macd - current_signal, 2)
    }


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
    rsi = compute_rsi(mock_prices, window=5)
    print(f"Mock moving average: ${avg:,.2f}")
    print(f"Mock RSI: {rsi}")
