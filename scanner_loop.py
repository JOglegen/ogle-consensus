"""
scanner_loop.py — continuous 5-minute scanner with live dashboard.

Runs in a terminal. Every 5 minutes it fetches fresh candles, runs
all 13 models, logs the signal, and prints a rolling summary.

Usage:
  python scanner_loop.py                    # BTC-USD, 5-min interval
  python scanner_loop.py --interval 60      # every 60 seconds
  python scanner_loop.py --symbol ETH-USD
  python scanner_loop.py --source csv       # offline test (instant loop)
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def dashboard(symbol, signals, current):
    clear()
    print(f"╔{'═'*58}╗")
    print(f"║   OGLE AI Consensus Bot  v2  —  {symbol:<23}║")
    print(f"╠{'═'*58}╣")

    c = current
    bar = ("🟢" * c.buy_votes + "🔴" * c.sell_votes +
           "⬜" * c.hold_votes)
    colour = "🟢 BUY " if c.direction == "BUY" else "🔴 SELL" if c.direction == "SELL" else "⬜ HOLD"
    print(f"║  Signal  : {colour}                               ║")
    print(f"║  Price   : ${c.price:>10,.2f}                              ║")
    print(f"║  Votes   : {c.buy_votes}↑ BUY  {c.sell_votes}↓ SELL  {c.hold_votes}· HOLD"
          f"                     ║")
    print(f"║  Conf    : {c.confidence*100:+.0f}%   Kelly size: {c.kelly_size*100:.1f}%"
          f"                    ║")
    print(f"║  Updated : {c.timestamp}                   ║")
    print(f"╠{'═'*58}╣")
    print(f"║  Recent signals (last 10):                           ║")

    recent = signals[-10:]
    for s in reversed(recent):
        icon = "🟢" if s["direction"] == "BUY" else "🔴" if s["direction"] == "SELL" else "⬜"
        print(f"║  {icon} {s['timestamp'][:16]}  {s['direction']:<4}  "
              f"{s['buy_votes']}↑{s['sell_votes']}↓  "
              f"${float(s['price']):>10,.2f}          ║")

    print(f"╚{'═'*58}╝")
    print(f"  Ctrl+C to stop  |  Signals logged → signals.csv")


def main(argv=None):
    p = argparse.ArgumentParser(description="OGLE consensus scanner loop")
    p.add_argument("--symbol",        default="BTC-USD")
    p.add_argument("--source",        default="auto",
                   choices=["auto","coinbase","csv","yfinance"])
    p.add_argument("--interval",      type=int, default=300,  # 5 minutes
                   help="Seconds between scans")
    p.add_argument("--bars",          type=int, default=200)
    p.add_argument("--buy-threshold", type=int, default=6, dest="buy_threshold")
    p.add_argument("--output",        default="signals.csv")
    args = p.parse_args(argv)

    from data_feed import load_bars
    from consensus import ConsensusEngine, ConsensusConfig

    cfg    = ConsensusConfig(buy_threshold=args.buy_threshold,
                              sell_threshold=args.buy_threshold)
    engine = ConsensusEngine(cfg)
    out    = Path(args.output)
    fields = ["timestamp","symbol","direction","buy_votes","sell_votes",
              "hold_votes","score","confidence","kelly_size","price"]

    # Load existing signals for the dashboard history
    history = []
    if out.exists():
        with open(out) as f:
            history = list(csv.DictReader(f))

    print(f"  OGLE Scanner starting — {args.symbol}  interval: {args.interval}s")
    print(f"  Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                bars   = load_bars(args.symbol, args.bars, args.source)
                signal = engine.analyse(bars, args.symbol)

                # Append to CSV
                new = not out.exists()
                with open(out, "a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=fields)
                    if new: w.writeheader()
                    w.writerow({k: getattr(signal, k) for k in fields})

                row = {k: getattr(signal, k) for k in fields}
                history.append(row)
                dashboard(args.symbol, history, signal)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\n  [error] {e} — retrying in {args.interval}s")

            if args.source == "csv":
                # Don't hammer the loop in offline mode
                print("\n  [offline] CSV mode — sleeping 10s then re-running")
                time.sleep(10)
            else:
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n  Scanner stopped. Signals saved to signals.csv\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
