"""
main.py — single consensus scan.

Loads candles, runs all 13 models, prints the vote ballot,
appends the signal to signals.csv.

Usage:
  python main.py                    # live BTC-USD from Coinbase
  python main.py --symbol ETH-USD   # different asset
  python main.py --source csv       # use local sample data (no internet)
  python main.py --source yfinance --symbol AAPL  # stocks via yfinance
"""

import argparse
import csv
import os
import sys
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(description="OGLE AI Consensus Bot")
    p.add_argument("--symbol",  default="BTC-USD")
    p.add_argument("--source",  default="auto",
                   choices=["auto", "coinbase", "csv", "yfinance"])
    p.add_argument("--bars",    type=int, default=200)
    p.add_argument("--buy-threshold",  type=int, default=6, dest="buy_threshold")
    p.add_argument("--sell-threshold", type=int, default=6, dest="sell_threshold")
    p.add_argument("--output",  default="signals.csv")
    args = p.parse_args(argv)

    print(f"\n{'━'*60}")
    print(f"  OGLE AI Consensus Bot v2")
    print(f"  {args.symbol}  |  source: {args.source}  |  models: 13")
    print(f"{'━'*60}\n")

    from data_feed import load_bars
    from consensus import ConsensusEngine, ConsensusConfig

    bars = load_bars(args.symbol, args.bars, args.source)
    print(f"  Loaded {len(bars)} bars  |  latest close: ${bars[-1].close:,.2f}\n")

    cfg    = ConsensusConfig(buy_threshold=args.buy_threshold,
                              sell_threshold=args.sell_threshold)
    engine = ConsensusEngine(cfg)
    signal = engine.analyse(bars, symbol=args.symbol)

    engine.print_ballot(signal)

    # Append to signals.csv
    out  = Path(args.output)
    new  = not out.exists()
    with open(out, "a", newline="") as f:
        fields = ["timestamp","symbol","direction","buy_votes","sell_votes",
                  "hold_votes","score","confidence","kelly_size","price"]
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow({k: getattr(signal, k) for k in fields})

    print(f"  Signal saved → {out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
