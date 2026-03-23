import requests
import urllib3
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# --- API Sources (tried in order, falls back if unavailable) ---
BINANCE_BASE   = "https://api.binance.com/api/v3"
KRAKEN_BASE    = "https://api.kraken.com/0/public"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

VERIFY_SSL = False

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "ZK-Oracle/1.0", "Accept": "application/json"}

# Mapping from friendly asset names to exchange-specific symbols
BINANCE_SYMBOLS = {"bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "solana": "SOLUSDT"}
KRAKEN_PAIRS    = {"bitcoin": "XBTUSD",  "ethereum": "ETHUSD",  "solana": "SOLUSD"}
COINGECKO_IDS   = {"bitcoin": "bitcoin", "ethereum": "ethereum", "solana": "solana"}


# ─── Mock Data Fallback ─────────────────────────────────────────────────────
def get_mock_news(asset: str) -> dict:
    print(f"⚠️  Using mock news data for {asset}.")
    sentiments = ["Bullish", "Bearish", "Neutral"]
    weight = [0.5, 0.2, 0.3] if asset.lower() == "bitcoin" else [0.3, 0.3, 0.4]
    
    sentiment = random.choices(sentiments, weights=weight)[0]
    
    headlines_dict = {
        "Bullish": [f"{asset.title()} sees massive institutional adoption", f"New technological breakthrough scales {asset.title()} network", f"{asset.title()} ETF flows reach all time high", f"Major country announces {asset.title()} integration", f"Whales accumulating {asset.title()} at record pace"],
        "Bearish": [f"Regulatory concerns hit {asset.title()} markets", f"Macroeconomic factors drag down {asset.title()} price", f"Large exchange moves {asset.title()} to cold storage sparking panic", f"Tighter monetary policy hurts {asset.title()}", f"{asset.title()} faces severe network congestion causing high fees"],
        "Neutral": [f"{asset.title()} market trading sideways amid uncertainty", f"{asset.title()} network upgrade goes smoothly without price impact", f"{asset.title()} dominance remains steady", f"Market awaits next major catalyst for {asset.title()}", f"{asset.title()} miners hold steady despite difficulty adjustment"]
    }
    
    return {
        "asset": asset,
        "sentiment": sentiment,
        "headlines": [{"title": h, "link": "https://example.com/news"} for h in random.sample(headlines_dict[sentiment], 5)],
        "source": "Mock News Engine",
        "timestamp": int(datetime.now(timezone.utc).timestamp())
    }

def get_mock_price(asset: str) -> dict:
    if asset.lower() not in ["bitcoin", "ethereum", "solana"]:
        raise ValueError("Asset not found")
    print(f"⚠️  All price APIs unavailable. Using mock data for {asset}.")
    base_prices = {"bitcoin": 71700.0, "ethereum": 3900.0, "solana": 145.0}
    price = base_prices.get(asset.lower(), 100.0) * (1 + random.uniform(-0.005, 0.005))
    return {
        "asset": asset,
        "price": round(price, 2),
        "change_24h": round(random.uniform(-3.0, 3.0), 2),
        "currency": "usd",
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "source": "Mock Data (Fallback)",
    }

def get_mock_history(asset: str, days: int) -> dict:
    if asset.lower() not in ["bitcoin", "ethereum", "solana"]:
        raise ValueError("Asset not found")
    print(f"⚠️  All history APIs unavailable. Using mock data for {asset}.")
    base_prices = {"bitcoin": 71700.0, "ethereum": 3900.0, "solana": 145.0}
    current_price = base_prices.get(asset.lower(), 100.0)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    prices = []
    for i in range(days, 0, -1):
        ts = now_ms - (i * 86_400_000)
        prices.append([ts, round(current_price, 2)])
        current_price *= (1 + random.uniform(-0.02, 0.02))
    return {"asset": asset, "prices": prices, "days": days}


# ─── fetch_price ─────────────────────────────────────────────────────────────
def _price_from_binance(asset: str, currency: str) -> dict:
    symbol = BINANCE_SYMBOLS.get(asset.lower())
    if not symbol:
        raise ValueError(f"No Binance symbol for {asset}")
    # Binance: real-time last price
    ticker = requests.get(
        f"{BINANCE_BASE}/ticker/24hr",
        params={"symbol": symbol},
        headers=HEADERS, timeout=5, verify=VERIFY_SSL
    ).json()
    # Kline for a more stable "last" price
    price_r = requests.get(
        f"{BINANCE_BASE}/ticker/price",
        params={"symbol": symbol},
        headers=HEADERS, timeout=5, verify=VERIFY_SSL
    ).json()
    return {
        "asset": asset,
        "price": float(price_r["price"]),
        "change_24h": float(ticker["priceChangePercent"]),
        "currency": currency,
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "source": "Binance",
    }

def _price_from_kraken(asset: str, currency: str) -> dict:
    pair = KRAKEN_PAIRS.get(asset.lower())
    if not pair:
        raise ValueError(f"No Kraken pair for {asset}")
    data = requests.get(
        f"{KRAKEN_BASE}/Ticker",
        params={"pair": pair},
        headers=HEADERS, timeout=5, verify=VERIFY_SSL
    ).json()
    if data.get("error"):
        raise ValueError(data["error"])
    result = list(data["result"].values())[0]
    price = float(result["c"][0])          # last trade price
    open_  = float(result["o"])            # 24h open
    change_24h = ((price - open_) / open_) * 100
    return {
        "asset": asset,
        "price": price,
        "change_24h": round(change_24h, 2),
        "currency": currency,
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "source": "Kraken",
    }

def _price_from_coingecko(asset: str, currency: str) -> dict:
    asset_id = COINGECKO_IDS.get(asset.lower(), asset.lower())
    data = requests.get(
        f"{COINGECKO_BASE}/simple/price",
        params={"ids": asset_id, "vs_currencies": currency, "include_24hr_change": "true"},
        headers=HEADERS, timeout=5, verify=VERIFY_SSL
    ).json()
    if asset_id not in data:
        raise ValueError("Asset not found in CoinGecko response")
    coin = data[asset_id]
    return {
        "asset": asset,
        "price": float(coin[currency]),
        "change_24h": float(coin.get(f"{currency}_24h_change", 0.0)),
        "currency": currency,
        "timestamp": int(datetime.now(timezone.utc).timestamp()),
        "source": "CoinGecko",
    }

def fetch_price(asset: str = "bitcoin", currency: str = "usd") -> dict:
    """Try Binance → Kraken → CoinGecko → mock for real-time price."""
    for source_fn, name in [
        (_price_from_binance,   "Binance"),
        (_price_from_kraken,    "Kraken"),
        (_price_from_coingecko, "CoinGecko"),
    ]:
        try:
            result = source_fn(asset, currency)
            return result
        except Exception:
            continue
    return get_mock_price(asset)


# ─── fetch_price_history ─────────────────────────────────────────────────────
def _history_from_binance(asset: str, days: int) -> dict:
    symbol = BINANCE_SYMBOLS.get(asset.lower())
    if not symbol:
        raise ValueError(f"No Binance symbol for {asset}")
    klines = requests.get(
        f"{BINANCE_BASE}/klines",
        params={"symbol": symbol, "interval": "1d", "limit": days},
        headers=HEADERS, timeout=5, verify=VERIFY_SSL
    ).json()
    if not klines or isinstance(klines, dict):
        raise ValueError("Bad klines response")
    prices = [[int(k[0]), float(k[4])] for k in klines]  # [open_time, close_price]
    return {"asset": asset, "prices": prices, "days": len(prices)}

def _history_from_coingecko(asset: str, days: int) -> dict:
    asset_id = COINGECKO_IDS.get(asset.lower(), asset.lower())
    data = requests.get(
        f"{COINGECKO_BASE}/coins/{asset_id}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
        headers=HEADERS, timeout=5, verify=VERIFY_SSL
    ).json()
    if "prices" not in data or not data["prices"]:
        raise ValueError("No price data from CoinGecko")
    prices = [[int(ts), float(px)] for ts, px in data["prices"]]
    return {"asset": asset, "prices": prices, "days": len(prices)}

def fetch_price_history(asset: str = "bitcoin", days: int = 7) -> dict:
    """Try Binance → CoinGecko → mock for historical daily prices."""
    for source_fn, name in [
        (_history_from_binance,   "Binance"),
        (_history_from_coingecko, "CoinGecko"),
    ]:
        try:
            return source_fn(asset, days)
        except Exception:
            continue
    return get_mock_history(asset, days)


# ─── fetch_news ─────────────────────────────────────────────────────────────
def fetch_news(asset: str = "bitcoin") -> dict:
    """Fetch 5 latest headlines from Google News RSS for the given asset."""
    url = f"https://news.google.com/rss/search?q={asset}+when:1d&hl=en-US&gl=US&ceid=US:en"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 ZK-Oracle"}, timeout=5, verify=VERIFY_SSL)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        all_items = root.findall('.//item')
        
        headlines = []
        for item in all_items:
            title = item.find('title')
            link = item.find('link')
            if title is not None and title.text:
                headlines.append({
                    "title": title.text,
                    "link": link.text if link is not None else url
                })
                
        # Prioritize asset-specific headlines
        asset_lower = asset.lower()
        asset_headlines = [h for h in headlines if asset_lower in h["title"].lower()]
        
        # Fill the rest with general top news
        # We use a set of titles to avoid duplicates efficiently
        seen_titles = {h["title"] for h in asset_headlines}
        remaining_headlines = [h for h in headlines if h["title"] not in seen_titles]
        
        final_headlines = (asset_headlines + remaining_headlines)[:5]
        
        if len(final_headlines) == 0:
            return get_mock_news(asset)
            
        return {
            "asset": asset,
            "sentiment": "Pending LLM Analysis",
            "headlines": final_headlines,
            "source": "Google News RSS",
            "timestamp": int(datetime.now(timezone.utc).timestamp())
        }
    except Exception as e:
        print(f"⚠️  RSS fetch failed: {e}. Falling back to mock data.")
        return get_mock_news(asset)


# ─── CLI test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching Bitcoin price...")
    result = fetch_price("bitcoin")
    print(f"  Source: {result['source']}")
    print(f"  Price:  ${result['price']:,.2f}")
    print(f"  24h Change: {result['change_24h']:.2f}%")

    print("\nFetching 7-day history...")
    history = fetch_price_history("bitcoin", days=7)
    print(f"  Source: Binance/CoinGecko")
    print(f"  Got {len(history['prices'])} days of data")
    if history["prices"]:
        print(f"  First close: ${history['prices'][0][1]:,.2f}")
        print(f"  Latest close: ${history['prices'][-1][1]:,.2f}")

    print("\nFetching News & Sentiment...")
    news = fetch_news("bitcoin")
    print(f"  Sentiment: {news['sentiment']}")
    for i, item in enumerate(news['headlines']):
        print(f"  Headline {i+1}: {item['title']}")
        print(f"  Link: {item['link']}")
