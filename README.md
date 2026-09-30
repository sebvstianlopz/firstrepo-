# firstrepo-
A indictor built for Pine Script based on High Volume areas, Reactions, SMT's and FVGs. Letting it spot potential trading scenarios using all these confluences and giving "buy" or "sell" signals in real time

## XAUUSD Reaction Zones (Pine Script v6)

`pinescript/xauusd_reaction_zones.pine` — TradingView indicator for XAUUSD (5m and 1H) that marks
every common reaction area: swing pivots, order blocks, fair value gaps, higher-timeframe pivots,
previous day/week high & low, Asia/London/NY session highs & lows, and round numbers.

It includes a live backtest table comparing each zone type's reaction rate to **random control zones**
of the same size, so you can see whether a zone type has a real edge on your chart.

### Offline backtest

`backtest/reaction_zones_backtest.py` mirrors the indicator logic in plain Python (no dependencies)
using OANDA:XAUUSD data in `data/` (1H: Nov 2025 – Sep 2026, 5m: Sep 2026, 5000 bars each).

```
cd backtest && python3 reaction_zones_backtest.py > results.txt
```

Summary (see `backtest/results.txt`):
- Raw zone touches react 49–54% of the time, about the same as random control zones.
- A rejection close (wick into the zone, close back outside) raises the reaction rate to about 70%,
  but random levels rise by the same amount, so the candle carries the signal, not the level.
- Rejection-candle trades at 1R/2R average about 0R before spread, for real and random zones alike.
- Order blocks were the only type to beat random on both timeframes (about +3%), and the result is not statistically significant.

## XAUUSD High-Volume Rejection Zones (1H) — current version

`pinescript/xauusd_hv_rejection_zones.pine` marks a zone when a 1H candle has volume ≥ 2× its
20-bar average and a wick ≥ 40% of its range. The zone is the wick. Zones are deleted when broken.

Backtest (`backtest/volume_zones_backtest.py`, results in `backtest/volume_results.txt`):
- First-retest reaction rate is 58.6% for these zones vs 52.3% for random zones of the same size.
  They beat random in both halves of the data.
- At 1.5× volume there is no edge, so the volume filter is what makes the difference.
- Continuation-origin zones, absorption candles, the previous-day POC and flipped (broken) zones
  did not beat random, so they are not included.
- A limit entry at the zone edge is about break-even (+0.04R at 1R), while random zones lose -0.12R.
  Use the zones as higher-probability areas, not as stand-alone entries.

## XAUUSD High-Volume Zones (5m) — current version

`pinescript/xauusd_hv_zones_5m.pine` is for the 5m chart and draws two layers:
- **1H zones:** the tested 1H high-volume rejection zones, taken from closed 1H candles so they don't repaint.
- **5m zones:** candles with volume ≥ 2× the average for the same time of day and a wick ≥ 40%.
  These are unproven.

5m study (`python3 backtest/volume_zones_backtest.py --5m`, results in `backtest/volume_results_5m.txt`),
run on about 4 weeks of 5m data from OANDA tick volume and COMEX GC1! futures volume:
- No 5m volume-zone idea beat random zones in both halves of the data or on both feeds.
- Time-of-day volume rejection zones scored +9% vs random on OANDA and -2% on COMEX.
- On 5m, the spread (~$0.30) costs about 10% of a typical stop.
- The live table on the chart measures both layers against random zones on TradingView's longer history.

### 5m entry signals inside 1H zones

The 5m indicator also marks BUY and SELL signals once price makes its first retest of a fresh 1H zone:
- **Rejection:** a 5m candle closes back out of the zone.
- **BOS:** a 5m close breaks the latest swing high or low.
- **Trades:** the stop goes beyond the 5m swing (or beyond the 1H zone) and the target is 2R.
  Every signal is tracked as a trade in the table, next to the same signals taken on random zones.
- **Logic check:** `python3 backtest/entry_signals_5m.py` (results in `backtest/entry_signals_5m_results.txt`)
  only has about 4 weeks of 5m data (12–17 trades per trigger). That confirms the logic but is not
  evidence of an edge.

### Strategy backtest of the 5m entry signals

`python3 backtest/strategy_backtest.py` → `backtest/strategy_results.txt`, trade list in `backtest/strategy_trades.csv`.

Samples: OANDA 5m (4 weeks), OANDA 15m entries as a proxy (2.5 months), and COMEX GC1! 5m (4 weeks).
With the indicator defaults (swing stop, 2R target, spread included) there were 108 trades.
The win rate was 25.9% and the average was -0.30R per trade; break-even at 2R needs a win rate of about 34%.
All 18 combinations of trigger, stop and target lost money, and random zones did as well or better.
**The entry signals should not be traded as a stand-alone strategy.**

### Breakout test and Strategy Tester version

`python3 backtest/breakout_backtest.py` → `backtest/breakout_results.txt`. This trades the first close
through a 1H zone in the break direction. With a candle stop and a 2R target, spread included:
- OANDA 1H, 10 months: 201 trades, 37.8% win, -0.06R per trade.
- COMEX 1H, 10 months: 244 trades, 38.1% win, -0.06R per trade.
- Breakouts through random levels made +0.16R and +0.09R per trade.

**Breakouts through high-volume zones fail more often than breakouts through random levels.**
The zones slow price down, but neither bouncing off them nor breaking through them is profitable
on its own.

`pinescript/xauusd_hv_zone_strategy.pine` is a `strategy()` version for TradingView's Strategy Tester.
It has four modes: Bounce - rejection, Bounce - BOS, Bounce - both, and Breakout. Position size is
risk-based, and the $0.30 spread is modelled as commission.

## XAUUSD HV Zones + Signals — current recommended indicator

`pinescript/xauusd_hv_signals.pine` shows the 1H high-volume zones plus **failed-breakout signals**.
A signal fires when price closes through a zone and then, within 6 hours, closes back on the
original side of it. The trade goes in the reclaim direction, with the stop beyond the sweep and a 2R target.
A results table on the chart tracks every signal as a trade (win rate, average R, total R, drawdown),
so no Strategy Tester is needed.

Backtest (`python3 backtest/failed_breakout_backtest.py`, results in `backtest/failed_breakout_results.txt`,
trade list in `backtest/failed_breakout_trades_oanda_1h.csv`), spread included, 2R target:
- OANDA 1H, 10 months: 64 trades, 50.0% win, -0.02R per trade.
- COMEX 1H, 10 months: 67 trades, 50.7% win, +0.12R per trade.
- Both feeds lost in the first half and made money in the second.

This is the best of the five signal ideas tested (bounce/rejection, bounce/BOS, breakout,
failed breakout, 5m zones), but it is not a proven edge.
