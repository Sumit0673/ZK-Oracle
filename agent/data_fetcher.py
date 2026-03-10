import requests
import urllib3
from datetime import datetime, timezone


COINGECKO_BASE = "https://api.coingecko.com/api/v3"

VERIFY_SSL = False

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def fetch_price(asset: str = "bitcoin", currency: str = "usd") -> dict:

    url = f"{COINGECKO_BASE}/simple/price"
    params = {
        "ids": asset,
        "vs_currencies": currency,
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    }

    try:
        response = requests.get(
            url, 
            params=params, 
            headers=HEADERS,
            timeout=10, 
            verify=VERIFY_SSL
        )
        response.raise_for_status()
    except requests.exceptions.SSLError:
        raise RuntimeError(
            "SSL Certificate verification failed. \n"
            "FIX 1: Run 'pip install certifi'\n"
            "FIX 2: Set VERIFY_SSL = False in agent/data_fetcher.py (Not recommended for production)"
        )
    except Exception as e:
        raise e

    data = response.json()

    if asset not in data:
        raise ValueError(f"Asset '{asset}' not found on CoinGecko")

    price_data = data[asset]
    return {
        "asset": asset,
        "price": price_data[currency],
        "change_24h": price_data.get(f"{currency}_24h_change", 0),
        "currency": currency,
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "source": f"{COINGECKO_BASE}/simple/price?ids={asset}",
    }


def fetch_price_history(asset: str = "bitcoin", days: int = 7) -> dict:
    url = f"{COINGECKO_BASE}/coins/{asset}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
    }

    response = requests.get(
        url, 
        params=params, 
        headers=HEADERS,
        timeout=15, 
        verify=VERIFY_SSL
    )
    response.raise_for_status()
    data = response.json()

    return {
        "asset": asset,
        "prices": data["prices"],
        "days": days,
    }


if __name__ == "__main__":
    print("Fetching Bitcoin price...")
    result = fetch_price("bitcoin")
    print(f"  Price: ${result['price']:,.2f}")
    print(f"  24h Change: {result['change_24h']:.2f}%")
    print(f"  Timestamp: {result['timestamp']}")
