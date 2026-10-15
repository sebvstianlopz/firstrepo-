# 1H Sweep / BOS + 5m Volume Rejection (XAUUSD)

New, standalone project. It does not reuse anything from the other indicators in this repository.

- `liq_bos_rejection.pine`: TradingView indicator (Pine Script v6) for the 5m chart.
  1. **1H structure:** detects a break of structure (a close beyond the last 1H swing) and a liquidity sweep
     (a wick beyond the swing and a close back inside).
  2. **Zones:** each event creates zones at the BOS level, at the BOS origin candle (demand/supply), and at the sweep wick.
  3. **5m signal:** a BUY or SELL label appears when a candle rejects a zone with a long wick, a close back out of
     the zone, and high volume (in the direction of the 1H bias by default).
  4. **Results table:** every signal is tracked on your chart.
- `backtest.py` and `results.txt`: Python test of the same rules on fresh data in `data/`
  (OANDA and COMEX 5m from 2026-09-21 to 2026-10-15, OANDA 15m from 2026-07-31 to 2026-10-15).

Result with the default rules: only 5–15 signals per sample, and 75–80% of them lost. A plain high-volume rejection
candle with no zone did better (about -0.1R per trade). The sample is too small for firm conclusions, and the rules
have not been tuned.
