# Chart examples

Screenshots of setups on TradingView. Every one is Nasdaq 100 (OANDA NAS100USD, 1-minute) on the
left and S&P 500 (FXCM SPX500, 1-minute) on the right.

> **These are observations, not rules.** The trading rules live in `docs/rules.md`. Nothing here
> becomes a strategy signal until the owner confirms it there.

## Indicators on the charts
- **S&D Profile [TFO]**, with sessions 20:00–03:00 (Asia), 03:00–08:30 (London) and 08:30–16:00 (New York).
  It draws the session high/low lines, the "Seek & Destroy Profile" stats table and the large session watermark.
- **SMT lines**: divergence between NAS100 and SPX500 at a swing high or low.
- **FVG boxes**: 1m and 3m fair value gaps.
- **Purple box with a dashed yellow line**: the move after the SMT. A red box below it on 16 Sep.
- **Hidden (eye crossed out)**: EMA 50 and Order Block Detector [LuxAlgo].
- Volume in ticks.

## Examples

| File | Date / time (NY) | Direction | What happens |
|---|---|---|---|
| `2026-09-16-bullish-smt-a.webp` | 16 Sep, ~09:05–09:45 | Up | NAS100 makes a higher low (rising SMT line) at the lows. Around 09:45 a sharp rally (purple box) leaves a 1m FVG near 29,150–29,180. Price reaches ~29,230 and breaks above the New York High line (~29,177). |
| `2026-09-16-bullish-smt-b.webp` | 16 Sep | Up | The same setup at a different moment (the live prices differ). |
| `undated-bearish-smt.webp` | date not visible, ~10:10–11:00 | Down | NAS100 makes a lower high while SPX500 makes a higher high (bearish SMT). Around 11:00 price drops through a 1m FVG, from ~29,500 to ~29,380 by 11:25. At the low there is a bullish 1m FVG and a second SMT, and price bounces. |
| `2026-09-08-bullish-smt.webp` | 8 Sep, ~09:50–10:05 | Up | Price falls through a 1m FVG and a 3m FVG. The SMT lines at the lows go in opposite directions (NAS line rising, SPX line falling), which is bullish divergence. The low is ~29,480 around 10:05, then price rallies to ~29,545. |

## The pattern these examples share
1. Price goes to a swing high or low during the New York morning (roughly 09:00–11:00).
2. NAS100 and SPX500 disagree there (**SMT divergence**).
3. A strong move in the other direction follows and leaves a **1m FVG**.
4. Price keeps moving that way.

## Still to decide before any of this can be coded
- **Entry**: at the SMT, when the FVG forms, or when price comes back into the FVG?
- **Stop-loss**: under/over the SMT swing, or the red box? How many points?
- **Target / exit**: session high/low, fixed R-multiple, or an opposite FVG?
- **Allowed times**: only New York 08:30–16:00, or also London?
- **Role of the other tools**: do volume, the Seek & Destroy warnings, EMA 50 or order blocks filter trades?
- **Which instrument to trade**: NQ, ES or both, and what size?
