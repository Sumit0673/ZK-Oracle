"""
ZK Oracle — Agent Tests
========================
Step-by-step tests for each agent component.
Run with: python -m pytest tests/ -v
Or test individually: python tests/test_agent.py
"""

import sys
import os
import json
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher import fetch_price, fetch_price_history
from analyzer import compute_moving_average, create_oracle_report, OracleReport


# ─── Step 1: Test Data Fetcher ───────────────────────────────────────

class TestDataFetcher:
    """Tests for the CoinGecko data fetching module."""

    def test_fetch_bitcoin_price(self):
        """Can we fetch a live Bitcoin price?"""
        result = fetch_price("bitcoin")

        assert "asset" in result
        assert result["asset"] == "bitcoin"
        assert result["price"] > 0
        assert result["timestamp"] > 0
        assert "coingecko" in result["source"]
        print(f"  ✅ Bitcoin price: ${result['price']:,.2f}")

    def test_fetch_ethereum_price(self):
        """Can we fetch a live Ethereum price?"""
        result = fetch_price("ethereum")

        assert result["asset"] == "ethereum"
        assert result["price"] > 0
        print(f"  ✅ Ethereum price: ${result['price']:,.2f}")

    def test_fetch_invalid_asset(self):
        """Does it fail gracefully for invalid assets?"""
        with pytest.raises(ValueError, match="not found"):
            fetch_price("not-a-real-coin-xyz")

    def test_fetch_price_history(self):
        """Can we fetch 7-day price history?"""
        result = fetch_price_history("bitcoin", days=7)

        assert result["asset"] == "bitcoin"
        assert result["days"] == 7
        assert len(result["prices"]) > 0

        # Each price point should be [timestamp_ms, price]
        first_point = result["prices"][0]
        assert len(first_point) == 2
        assert first_point[1] > 0
        print(f"  ✅ Got {len(result['prices'])} price points")


# ─── Step 2: Test Analyzer ───────────────────────────────────────────

class TestAnalyzer:
    """Tests for the data analysis module."""

    def test_moving_average_basic(self):
        """Does moving average compute correctly with mock data?"""
        # Mock prices: $100, $200, $300, $400, $500
        mock_prices = [[i, (i + 1) * 100] for i in range(5)]
        avg = compute_moving_average(mock_prices, window=5)

        assert avg == 300.0  # (100+200+300+400+500) / 5
        print(f"  ✅ Moving average: ${avg}")

    def test_moving_average_window(self):
        """Does the window parameter work correctly?"""
        mock_prices = [[i, (i + 1) * 100] for i in range(10)]
        avg_3 = compute_moving_average(mock_prices, window=3)

        # Last 3 prices: $800, $900, $1000
        assert avg_3 == round((800 + 900 + 1000) / 3, 8)
        print(f"  ✅ Window=3 average: ${avg_3}")

    def test_moving_average_empty(self):
        """Does it handle empty price lists?"""
        assert compute_moving_average([], window=5) == 0.0
        assert compute_moving_average(None, window=5) == 0.0

    def test_oracle_report_creation(self):
        """Can we create a valid OracleReport from mock data?"""
        price_data = {
            "asset": "bitcoin",
            "price": 67000.50,
            "source": "https://api.coingecko.com/test",
            "timestamp": 1700000000,
        }
        history_data = {
            "prices": [[i * 86400000, 65000 + i * 200] for i in range(10)]
        }

        report = create_oracle_report(price_data, history_data, "Test analysis")

        assert isinstance(report, OracleReport)
        assert report.asset == "bitcoin"
        assert report.price_usd == 67000.5
        assert report.moving_average > 0
        assert report.analysis == "Test analysis"
        print(f"  ✅ Report: {report.asset} @ ${report.price_usd:,.2f}")

    def test_oracle_report_json_serialization(self):
        """Can the report serialize to JSON (needed for Rust bridge)?"""
        report = OracleReport(
            asset="bitcoin",
            price_usd=67000.0,
            moving_average=65000.0,
            source="test",
            timestamp=1700000000,
            analysis="Test",
        )

        json_str = report.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["asset"] == "bitcoin"
        assert parsed["price_usd"] == 67000.0
        print(f"  ✅ JSON serialization works ({len(json_str)} bytes)")


# ─── Step 3: Test Live Pipeline (Data Fetcher + Analyzer) ────────────

class TestLivePipeline:
    """Integration tests using live CoinGecko data."""

    def test_full_report_from_live_data(self):
        """Can we create an OracleReport from live API data?"""
        price_data = fetch_price("bitcoin")
        history_data = fetch_price_history("bitcoin", days=7)
        report = create_oracle_report(
            price_data, history_data,
            analysis_text="Live test report"
        )

        assert report.price_usd > 0
        assert report.moving_average > 0
        assert report.timestamp > 0

        print(f"\n  📊 Live Oracle Report:")
        print(f"     Asset:    {report.asset}")
        print(f"     Price:    ${report.price_usd:,.2f}")
        print(f"     MA(7d):   ${report.moving_average:,.2f}")
        print(f"     Source:   {report.source}")


# ─── Run directly ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ZK Oracle Agent — Component Tests")
    print("=" * 60)

    # Run pytest with verbose output
    exit_code = pytest.main([__file__, "-v", "--tb=short", "-s"])
    sys.exit(exit_code)
