"""
Local backtest harness for the eth-pnl-fixed entry.

The bounty publishes the metric (net PnL after maker/taker fees and
size-scaled slippage) but not the sandbox's exact cost constants, so this
harness uses a transparent, deliberately conservative cost model and
reports results across several cost regimes:

  - Execution: the target decided at the close of bar t is executed at the
    open of bar t+1 (in bars.csv open[t+1] == close[t], so no gap).
  - Fee: 0.10% taker fee on traded notional, charged on every position
    change and on the final close-out.
  - Slippage: slippage fraction = participation, where participation =
    traded notional / that bar's traded value (volume x open), capped at
    1%. Account size for participation is a parameter (EQUITY0); regimes
    shown: $1k (gentle), $10k (base), $50k (harsh).

PnL is compounded equity return in percent. Max drawdown is peak-to-trough
on the same equity curve. Splits: H1 = bars 0-719, H2 = bars 720-1439,
each re-run standalone (flat start), plus the full 1,440 bars.

Usage: python3 backtest.py [bars.csv]
"""

import csv
import sys

from strategy import positions

FEE = 0.0010
SLIP_CAP = 0.01


def run(pos, opens, closes, vols, lo=0, hi=None, fee=FEE, equity0=10_000.0, slip_k=1.0):
    hi = len(closes) if hi is None else hi
    eq = 1.0
    peak = 1.0
    maxdd = 0.0
    trades = 0
    held = 0.0
    for t in range(lo, hi):
        if t > lo:
            prev = pos[t - 1]
            old = pos[t - 2] if t - 2 >= lo else 0.0
            d = prev - old
            if abs(d) > 1e-12:
                trades += 1
                part = abs(d) * eq * equity0 / max(vols[t] * opens[t], 1.0)
                eq *= 1 - abs(d) * (fee + min(slip_k * part, SLIP_CAP))
            held = prev
        eq *= 1 + held * (closes[t] / opens[t] - 1)
        peak = max(peak, eq)
        maxdd = max(maxdd, 1 - eq / peak)
    if abs(held) > 1e-12:
        eq *= 1 - abs(held) * fee
    return (eq - 1) * 100, maxdd * 100, trades


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "bars.csv"
    with open(path) as f:
        rows = list(csv.DictReader(f))
    opens = [float(r["open"]) for r in rows]
    closes = [float(r["close"]) for r in rows]
    vols = [float(r["volume"]) for r in rows]
    n = len(closes)
    pos = positions(closes)

    def fmt(label, res):
        print(f"{label:22s} net {res[0]:+6.2f}%  maxDD {res[1]:5.2f}%  trades {res[2]}")

    fmt("full (base $10k)", run(pos, opens, closes, vols))
    fmt("H1 bars 0-719", run(pos, opens, closes, vols, 0, n // 2))
    fmt("H2 bars 720-1439", run(pos, opens, closes, vols, n // 2, n))
    fmt("full (gentle $1k)", run(pos, opens, closes, vols, equity0=1_000.0))
    fmt("full (harsh $50k)", run(pos, opens, closes, vols, equity0=50_000.0))
    fmt("full (2x fees)", run(pos, opens, closes, vols, fee=FEE * 2))
    fmt("full (zero costs)", run(pos, opens, closes, vols, fee=0.0, equity0=0.0, slip_k=0.0))


if __name__ == "__main__":
    main()
