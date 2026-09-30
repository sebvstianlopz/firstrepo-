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
