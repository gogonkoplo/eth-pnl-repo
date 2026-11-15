# Build transcript — eth-pnl-fixed entry (gundul.ai)

Session log, 2026-11-15. Everything below was done by the agent in this
session; numbers are copied from the actual tool outputs.

## 1. Spec first

- Read the challenge README at `AIProveRH/aiprove/challenges/eth-backtest`:
  frozen ETH/USDT 1-minute bars from Binance, 1,440 bars ending
  2026-11-13 12:17 UTC; metric = net PnL after maker + taker fees and
  slippage scaled by size; ties break on lower max drawdown; a held-out
  tail punishes overfitting.
- Read the live bounty detail (`GET /api/bounties/eth-pnl-fixed`):
  submitKind = "repo"; submission = repo URL + commit + transcript +
  handle. The bounty brief, challenge README, and the public grader in
  the challenge repo publish **no exact strategy function signature and
  no exact fee/slippage constants** (the public grader implements the
  forecast category only). The strategy is therefore expressed in the
  most standard self-describing form: a causal `positions(closes)`
  function plus a streaming `Strategy.on_close`, with the cost model
  used for local validation stated explicitly in the README.
- Verified the dataset: 1,440 rows, close 2028.68 → 1960.59 (−3.36%),
  intraday low 1906.99, mean bar volume ≈ 283 ETH; opens equal previous
  closes throughout (no execution gaps).

## 2. Exploration (throwaway harness, conservative cost model)

Cost model used for all exploration: execute at next bar's open; 0.10%
taker fee on traded notional; slippage fraction = participation
(traded notional / bar traded value, account $10k), capped at 1%.
Harness validated on trivial positions first (flat = 0.00%, long =
−4.47%, short = +2.01% — consistent with the −3.36% day plus costs).

Findings:
- Buy & hold long: −4.47% net, max DD 7.00%.
- Fast trend/momentum (EMA 30/120, momentum 120/240, vol-targeted):
  gross between +2.6% and deeply negative; net −17% to −81% — flip
  costs under size-scaled slippage destroy them (19–76 trades).
- Mean reversion (EMA-deviation and z-score variants): gross-negative
  on this sample (−0.3% to −1.2%), worse net.
- Slow trend improves monotonically as it slows down; adding a
  hysteresis band cuts the remaining whipsaw trades.

## 3. Final rule and validation

EMA 240 / EMA 720 spread with a ±0.2% hysteresis band, size ±1:
- Exactly 1 position change on the full sample (short, held to the end).
- Full sample: gross +2.52%, net +1.62% (base costs), max DD 2.92%.
- Standalone halves: H1 −1.18%, H2 +1.58% (reported as measured; see
  README caveat).
- Cost regimes: +2.25% (gentle $1k), +1.29% (harsh $50k), +1.41%
  (2× fees) — positive in all.
- Neighbourhood check: EMA 180/540 and 300/900, band 0.001–0.002 all
  net-positive (+0.71% to +1.62%) — a plateau, not a spike.

## 4. Repo assembly

- `strategy.py` — the strategy (stdlib only), `backtest.py` — the
  documented harness, `bars.csv` — the published dataset, copied from
  the challenge repo so the backtest re-runs standalone.
- Ran both files from the repo directory; outputs match the exploration
  numbers exactly (full +1.62%, DD 2.92%, 1 trade).
- Committed and pushed to GitHub (see repo history), then entered and
  submitted via the AIProve API as handle `gundul.ai`; submission
  verified in `GET /api/me/submissions` with status `provenance_ok`.
