"""
backtest.py — bar-by-bar paper backtest of the consensus engine.

At each bar: run all 13 models on history up to that point,
record the signal, simulate a paper trade if BUY/SELL fires,
track the equity curve. No look-ahead.

Usage:
  python backtest.py                      # BTC-USD from Coinbase
  python backtest.py --source csv         # offline with sample data
  python backtest.py --buy-threshold 7    # stricter consensus
"""

import argparse
import csv
import sys
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(description="OGLE consensus backtest")
    p.add_argument("--symbol",        default="BTC-USD")
    p.add_argument("--source",        default="auto",
                   choices=["auto","coinbase","csv","yfinance"])
    p.add_argument("--bars",          type=int, default=300)
    p.add_argument("--buy-threshold", type=int, default=6, dest="buy_threshold")
    p.add_argument("--equity",        type=float, default=10_000)
    p.add_argument("--output",        default="backtest_results.csv")
    args = p.parse_args(argv)

    from data_feed import load_bars
    from consensus import ConsensusEngine, ConsensusConfig
    from models import Bar

    print(f"\n{'═'*60}")
    print(f"  OGLE Backtest  |  {args.symbol}  |  threshold: {args.buy_threshold}/13")
    print(f"{'═'*60}\n")

    all_bars = load_bars(args.symbol, args.bars, args.source)
    min_bars = 55

    cfg    = ConsensusConfig(buy_threshold=args.buy_threshold,
                              sell_threshold=args.buy_threshold)
    engine = ConsensusEngine(cfg)

    equity      = args.equity
    position    = None   # {"entry": float, "size_usd": float, "entry_bar": int}
    trades      = []
    equity_curve = []
    rows        = []

    for i in range(min_bars, len(all_bars)):
        history = all_bars[:i + 1]
        bar     = all_bars[i]
        sig     = engine.analyse(history, args.symbol)

        # Exit open position on SELL signal or after 20 bars
        if position:
            hold = i - position["entry_bar"]
            exit_price = None
            reason     = None
            if sig.direction == "SELL":
                exit_price = bar.close; reason = "signal"
            elif hold >= 20:
                exit_price = bar.close; reason = "timeout"

            if exit_price:
                pl_pct  = (exit_price - position["entry"]) / position["entry"]
                pl_usd  = position["size_usd"] * pl_pct
                equity += pl_usd
                trades.append({"entry": position["entry"], "exit": exit_price,
                                "pl_pct": pl_pct, "pl_usd": pl_usd,
                                "reason": reason, "hold_bars": hold})
                position = None

        # Enter on BUY signal if flat
        if not position and sig.direction == "BUY":
            size_usd = equity * sig.kelly_size
            if size_usd > 10:
                position = {"entry": bar.close, "size_usd": size_usd,
                            "entry_bar": i}

        equity_curve.append(equity)
        rows.append({"bar": i, "date": i, "price": bar.close,
                     "signal": sig.direction, "equity": round(equity, 2)})

    # Close any open position at end
    if position:
        last = all_bars[-1].close
        pl_pct = (last - position["entry"]) / position["entry"]
        pl_usd = position["size_usd"] * pl_pct
        equity += pl_usd
        trades.append({"entry": position["entry"], "exit": last,
                       "pl_pct": pl_pct, "pl_usd": pl_usd,
                       "reason": "end", "hold_bars": len(all_bars) - position["entry_bar"]})

    # ── metrics ──────────────────────────────────────────────────────────────
    n       = len(trades)
    wins    = [t for t in trades if t["pl_pct"] > 0]
    losses  = [t for t in trades if t["pl_pct"] <= 0]
    win_rt  = len(wins) / n * 100 if n else 0
    avg_win = sum(t["pl_pct"] for t in wins) / len(wins) * 100 if wins else 0
    avg_los = sum(t["pl_pct"] for t in losses) / len(losses) * 100 if losses else 0
    pf      = (sum(t["pl_usd"] for t in wins) /
               abs(sum(t["pl_usd"] for t in losses))) if losses else float("inf")
    total_r = (equity - args.equity) / args.equity * 100

    # Max drawdown
    peak = args.equity
    max_dd = 0.0
    for e in equity_curve:
        peak = max(peak, e)
        dd = (peak - e) / peak
        max_dd = max(max_dd, dd)

    print(f"  Trades      : {n}")
    print(f"  Win rate    : {win_rt:.1f}%")
    print(f"  Avg win     : {avg_win:+.2f}%")
    print(f"  Avg loss    : {avg_los:+.2f}%")
    print(f"  Profit factor: {pf:.2f}" if pf < 99 else "  Profit factor: ∞")
    print(f"  Total return: {total_r:+.1f}%")
    print(f"  Max drawdown: {max_dd*100:.1f}%")
    print(f"  Final equity: ${equity:,.2f}  (started ${args.equity:,.0f})")
    print()

    if n < 20:
        print("  ⚠  Fewer than 20 trades — results not statistically meaningful.")
        print("     Lower buy_threshold or use more bars.")

    # Save
    out = Path(args.output)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["bar","date","price","signal","equity"])
        w.writeheader(); w.writerows(rows)
    print(f"  Results saved → {out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
