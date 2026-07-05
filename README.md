# OGLE AI Consensus Bot v2

A paper-trading consensus engine. Multiple independent models vote before
any trade fires. No single indicator can trigger an entry — consensus is
required.

**Paper trading only. Do not risk real money until the backtest shows
consistent results over hundreds of signals.**

## Quick start

```bash
pip install -r requirements.txt
python main.py --source csv     # offline test (no internet needed)
python main.py                  # live BTC-USD from Coinbase
```

## The 13 models

Each measures a different dimension — they are genuinely independent:

| # | Model | What it measures |
|---|-------|-----------------|
| 1 | MA50 cross | Price vs 50-day trend |
| 2 | MACD | Momentum direction |
| 3 | RSI(14) | Overbought / oversold |
| 4 | Bollinger %B | Price vs volatility bands |
| 5 | Stochastic %K | Cycle position |
| 6 | Rate of Change | 10-day momentum |
| 7 | Trend slope | Linear regression drift |
| 8 | Volume surge | Unusual volume with direction |
| 9 | Volume trend | Accumulation vs distribution |
| 10 | ATR regime | Is market calm or chaotic |
| 11 | Range position | 20-day high/low placement |
| 12 | Candle pattern | Bullish/bearish body |
| 13 | Z-score | Mean reversion distance |

## Consensus threshold

Default: **6 of 13** must vote BUY to fire a BUY signal.

Change it:
```bash
python main.py --buy-threshold 8    # stricter — fewer trades, higher quality
python main.py --buy-threshold 5    # looser — more trades, more noise
```

## Run backtest

```bash
python backtest.py                   # tests on available historical bars
python backtest.py --source csv      # offline with sample data
python backtest.py --buy-threshold 7 # test a stricter threshold
```

## Run 5-minute scanner

```bash
python scanner_loop.py               # runs live, prints dashboard every 5 min
python scanner_loop.py --interval 60 # every 60 seconds
```

Signals are logged to `signals.csv` automatically.

## Run on stocks instead of BTC

```bash
python main.py --source yfinance --symbol AAPL
python main.py --source yfinance --symbol QQQ
```

## Files

```
models.py        — 13 independent voting models
consensus.py     — vote aggregation + Kelly position sizing
data_feed.py     — Coinbase live data / CSV fallback / yfinance
main.py          — single scan
backtest.py      — historical bar-by-bar test
scanner_loop.py  — continuous 5-minute scan with dashboard
data/
  sample_btc.csv — 365 days of synthetic BTC for offline testing
signals.csv      — generated output (created on first run)
```

## Position sizing: Kelly criterion

The bot uses **half-Kelly** sizing — the theoretically optimal fraction
of equity to risk, then halved for safety. It scales with confidence:
stronger consensus = larger suggested position.

This is a **suggestion only**. On a $1,000 paper account with default
settings, most signals will suggest risking $20–$80 per trade.

## Next steps (in order)

1. Run offline with sample data, confirm it works
2. Run live scans for 2–4 weeks, watch the signals
3. Run the backtest and check the profit factor and win rate
4. Only after consistent results: consider a paper brokerage connection
5. Only after that: consider real money

Do not skip steps.
