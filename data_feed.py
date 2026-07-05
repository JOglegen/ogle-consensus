"""
data_feed.py — pulls daily OHLCV candles.

Primary:  Coinbase Exchange public API (no API key needed)
Fallback: local CSV file (data/sample_btc.csv for offline testing)
Stock:    yfinance (optional, for running on AAPL/ETFs instead of BTC)

Coinbase endpoint: https://api.exchange.coinbase.com/products/BTC-USD/candles
Returns: [[time, low, high, open, close, volume], ...]
"""

from __future__ import annotations
import csv
import datetime
import time
from pathlib import Path
from typing import List, Optional

import requests

from models import Bar

COINBASE_URL = "https://api.exchange.coinbase.com/products/{symbol}/candles"
GRANULARITY  = 86400   # 1 day in seconds
MAX_CANDLES  = 300      # Coinbase returns max 300 per request


def fetch_coinbase(symbol: str = "BTC-USD", limit: int = 200) -> List[Bar]:
    """
    Fetch up to `limit` daily candles from Coinbase's public API.
    No API key required.
    """
    end   = int(time.time())
    start = end - (limit + 10) * GRANULARITY

    params = {"granularity": GRANULARITY, "start": start, "end": end}
    url    = COINBASE_URL.format(symbol=symbol)

    r = requests.get(url, params=params, timeout=15)
    if not r.ok:
        raise RuntimeError(f"Coinbase API error {r.status_code}: {r.text[:120]}")

    # Response: [[time, low, high, open, close, volume], ...] newest first
    raw = sorted(r.json(), key=lambda c: c[0])  # sort oldest → newest
    bars = [Bar(open=c[3], high=c[2], low=c[1], close=c[4], volume=c[5])
            for c in raw]
    return bars[-limit:]


def fetch_csv(path: str = "data/sample_btc.csv", limit: int = 200) -> List[Bar]:
    """Load candles from a local CSV file (date,open,high,low,close,volume)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    bars = []
    with open(p) as f:
        for row in csv.DictReader(f):
            bars.append(Bar(
                open=float(row["open"]), high=float(row["high"]),
                low=float(row["low"]),   close=float(row["close"]),
                volume=float(row["volume"]),
            ))
    return bars[-limit:]


def fetch_yfinance(symbol: str = "BTC-USD", limit: int = 200) -> List[Bar]:
    """Fetch candles via yfinance (works for stocks and BTC-USD)."""
    import yfinance as yf
    start = (datetime.date.today() - datetime.timedelta(days=limit + 10)).isoformat()
    df = yf.download(symbol, start=start, auto_adjust=True, progress=False)
    df = df.dropna()
    bars = [Bar(open=float(r["Open"]), high=float(r["High"]),
                low=float(r["Low"]),   close=float(r["Close"]),
                volume=float(r["Volume"]))
            for _, r in df.iterrows()]
    return bars[-limit:]


def load_bars(symbol: str = "BTC-USD", limit: int = 200,
              source: str = "auto") -> List[Bar]:
    """
    Load bars from the best available source.

    source: "coinbase" | "csv" | "yfinance" | "auto"
    auto tries Coinbase first, falls back to CSV.
    """
    if source == "coinbase" or source == "auto":
        try:
            bars = fetch_coinbase(symbol, limit)
            print(f"[data] Coinbase: {len(bars)} bars for {symbol}")
            return bars
        except Exception as e:
            if source == "coinbase":
                raise
            print(f"[data] Coinbase failed ({e}), trying CSV fallback…")

    if source == "csv" or source == "auto":
        csv_path = f"data/sample_{symbol.replace('-','').lower()[:3]}.csv"
        try:
            bars = fetch_csv(csv_path, limit)
            print(f"[data] CSV ({csv_path}): {len(bars)} bars")
            return bars
        except FileNotFoundError:
            # Try generic path
            try:
                bars = fetch_csv("data/sample_btc.csv", limit)
                print(f"[data] CSV (sample_btc.csv): {len(bars)} bars")
                return bars
            except FileNotFoundError:
                if source == "csv":
                    raise

    if source == "yfinance":
        bars = fetch_yfinance(symbol, limit)
        print(f"[data] yfinance: {len(bars)} bars for {symbol}")
        return bars

    raise RuntimeError(f"Could not load bars for {symbol} from source={source}")
