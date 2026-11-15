"""
eth-pnl-fixed entry — slow EMA trend with a hysteresis band.

Strategy (four parameters, all fixed a priori — no per-sample tuning):
  - EMA_FAST = 240 bars (4 h on 1-minute bars), EMA_SLOW = 720 bars (12 h),
    both on close prices, updated causally (bar t uses closes up to t only).
  - spread_t = EMA_fast / EMA_slow - 1.
  - Target position: +1 (long) once spread > +BAND, -1 (short) once
    spread < -BAND, otherwise KEEP the previous target (hysteresis).
    BAND = 0.002 (0.2%). The strategy starts flat.
  - The target decided at the close of bar t is the position held from the
    next bar onward (execute at next open; opens equal previous closes in
    this dataset, so there is no execution gap and no look-ahead).

Why this shape: the published cost model charges maker/taker fees plus
slippage scaled by trade size, so turnover is the dominant cost. A slow
trend with a dead-band trades only when a multi-hour trend is unambiguous
(exactly one position change on the whole published 1,440-bar sample) and
is indifferent to minute-level noise. The same rule, unchanged, runs on
any continuation of the series: it is a pure causal function of closes.

Interface:
  positions(closes) -> list[float]   target exposure per bar, in [-1, 1]
  Strategy().on_close(close) -> float  streaming form, same outputs

Stdlib only.
"""

EMA_FAST = 240
EMA_SLOW = 720
BAND = 0.002


class Strategy:
    def __init__(self, fast=EMA_FAST, slow=EMA_SLOW, band=BAND):
        self.k_fast = 2.0 / (fast + 1)
        self.k_slow = 2.0 / (slow + 1)
        self.band = band
        self.ema_fast = None
        self.ema_slow = None
        self.target = 0.0

    def on_close(self, close):
        if self.ema_fast is None:
            self.ema_fast = float(close)
            self.ema_slow = float(close)
            return self.target
        self.ema_fast += self.k_fast * (close - self.ema_fast)
        self.ema_slow += self.k_slow * (close - self.ema_slow)
        spread = self.ema_fast / self.ema_slow - 1.0
        if spread > self.band:
            self.target = 1.0
        elif spread < -self.band:
            self.target = -1.0
        return self.target


def positions(closes):
    """Target exposure for each bar, decided at that bar's close."""
    s = Strategy()
    return [s.on_close(c) for c in closes]


if __name__ == "__main__":
    import csv
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "bars.csv"
    with open(path) as f:
        closes = [float(r["close"]) for r in csv.DictReader(f)]
    pos = positions(closes)
    changes = sum(1 for a, b in zip([0.0] + pos, pos) if a != b)
    print(f"bars={len(closes)} position_changes={changes} final={pos[-1]:+.0f}")
