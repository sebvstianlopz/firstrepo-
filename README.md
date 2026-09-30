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
