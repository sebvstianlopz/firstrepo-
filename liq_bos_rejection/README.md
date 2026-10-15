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

## v2: Gold Scalper (current version)

`liq_bos_rejection.pine` has been rewritten for daily scalping:
- **More zones:** every 1H swing high/low plus BOS level, BOS origin and sweep zones. Zones last 48 h and can be
  used up to 3 times each.
- **Two-step signal:** a 5m rejection *setup* (diamond: wick into the zone, close past its middle, above-average volume,
  and in the direction of the 1H bias), then **BUY / SELL** when a candle closes beyond the setup candle within 3 candles.
- **Scalp trade:** stop beyond the zone or wick, target 1R, closed after 2 h. The results table tracks every trade.

`backtest_v2.py` and `results_v2.txt`: 384 settings were tested on the first 60% of OANDA 5m only. The chosen settings
were then checked unchanged on the rest of the data, and the entry and stop styles were compared:

| Confirmation entry + zone stop, 1R | Signals/day | Fail % | Avg per trade |
|---|---|---|---|
| OANDA 5m | 1.9 | 44% | +0.00R |
| COMEX 5m | 2.1 | 38% | +0.17R |
| OANDA 15m | 1.0 | 47% | +0.02R |
| Same entry, no zones | 2–6 | 48–54% | -0.03 to -0.08R |

The zones and the confirmation entry both help, but the result is break-even to slightly positive on 3–11 weeks of data.
This is not a proven money maker.
