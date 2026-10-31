# NQ Confluence

A TradingView (Pine Script v6) indicator and matching strategy for **NQ / MNQ futures on the 1-minute chart**. Each bar is scored on five confirmations, using ES for SMT and higher timeframes for context:

| # | Confirmation | Default source |
|---|---|---|
| 1 | High-volume reaction | 1m volume vs its 20-bar average |
| 2 | Respects a Fair Value Gap or Inverse FVG | 15m and 5m FVGs |
| 3 | SMT divergence with ES | 1m swings, NQ vs `CME_MINI:ES1!` |
| 4 | Liquidity sweep | Previous day, Asia, London and 5m swing highs/lows |
| 5 | Follows the trend | 1H market structure |

Signals come in two tiers. Both only fire inside the **NY kill zones** (09:30–11:30 and 13:30–15:30 ET):

| Signal | Looks like | Rule (defaults) |
|---|---|---|
| **BUY / SELL** (strong) | Large green / red label with the score, e.g. `BUY 4/5` | Score ≥ **4 of 5**, **sweep and trend required**, 10-bar cooldown, max 6 a day |
| **buy / sell** (weak) | Small faded triangle marked `buy` / `sell` | Score ≥ **3 of 5**, ignores the "Require …" toggles and the daily cap, own 10-bar cooldown |

A bar never shows both tiers. Hover a strong label to see which confirmations passed and the suggested SL/TP. The weak triangles can be restyled or hidden under Settings → Style, or switched off with **Show weak buy / sell signals**.

| File | What it is |
|---|---|
| `NQ_Confluence.pine` | Indicator: zones, sweeps, SMT lines, BUY/SELL signals, entry/SL/TP lines, confirmation table, alerts |
| `NQ_Confluence_Strategy.pine` | Same detection logic plus orders, for the Strategy Tester |

Both files contain an identical `=== SHARED LOGIC ===` block. If you change detection in one file, copy the whole block to the other.

## Setup

1. Open TradingView, then Pine Editor, then New, and paste `NQ_Confluence.pine`. Save it and click **Add to chart**.
2. Use a **1-minute** chart of `NQ1!` or `MNQ1!`. The table shows "Use a 1m chart" if the timeframe is higher than the FVG timeframe B setting.
3. For alerts: Create alert, set the condition to **NQ Confluence** and choose **"Any alert() function call"**. That message includes direction, score, price, SL and TP, and fires for both tiers (weak ones are marked "(weak)"). To alert on just one kind, pick one of the four named conditions instead: **BUY**, **SELL**, **Weak buy** or **Weak sell**.
4. For backtesting, add `NQ_Confluence_Strategy.pine` the same way and open **Strategy Tester**.

Futures volume is real exchange volume, which confirmation #1 needs. CFD feeds (NAS100) only provide tick volume.

## How each confirmation is defined

All logic runs **once per closed bar**. Higher-timeframe data comes only from **closed** higher-timeframe bars (`expr[1]` with `lookahead_on`). Signals therefore don't repaint, and the table shows the state as of the last closed bar.

**1 · Volume reaction.** Volume ≥ `1.8 ×` its 20-bar SMA, and the bar is a reaction bar in the signal's direction. For a long, that means either a lower wick ≥ 40% of the range with a close in the upper half, or a bullish body ≥ 60% of the range. You can optionally require that volume also beats the average for that same minute of day over the last N sessions. The flag stays valid for 3 bars.

**2 · FVG / IFVG.** Gaps are detected when each 15m and 5m bar closes:
- Bullish gap: `low > high[2]`. Bearish gap: `high < low[2]`. Gaps smaller than 8 ticks are ignored.
- When a 1m bar **closes through** a gap's far side, the gap flips into an **IFVG** in the opposite direction (dashed box). If an IFVG is broken as well, it's removed.
- A long counts as "respect" when the 1m low trades into a bullish FVG or IFVG and the bar closes back above the zone's midpoint. Shorts mirror this.
- The flag stays valid for 3 bars.

**3 · SMT with ES.** Each new 1m NQ swing low (pivot length 5) becomes the anchor, and the matching ES low is taken from the same window. Bullish SMT means one market takes out its anchor low and the other doesn't. Bearish SMT is the same with swing highs. The flag lasts 20 bars, or until both markets have taken their level.

**4 · Liquidity sweep.** These levels are tracked:
- previous day high/low
- Asia (20:00–00:00 ET) high/low and London (02:00–05:00 ET) high/low
- 5m swing highs/lows
- 1m swings (optional, off by default because they make sweeps very common)

A bullish sweep means price trades below a sell-side level, then closes back above it within 3 bars. The sweep's extreme is stored as the stop reference. A level is used up once price trades through it. The flag stays valid for 15 bars. The ✕ marker's tooltip names the level that was swept.

**5 · Trend.** This is 1H market structure. The bias turns bullish when a 1H close breaks the last 1H swing high, and bearish when one breaks the last swing low. It can optionally also require the 1H close to be on the right side of the 1H EMA(50).

## Stops and targets

- **Stop:** beyond the sweep extreme plus a 4-tick buffer. You can switch to the FVG's far side instead. Without either, the stop falls back to the 10-bar extreme.
- **Target:** `2.0 R`.
- **Skip if stop is wider than:** an optional filter that drops signals whose stop is wider than a set number of points.

The strategy enters at market after the signal bar closes. Once filled, it re-anchors the targets to the real fill price. Other strategy settings:
- optionally takes 50% at 1R and moves the stop to break-even (needs 2+ contracts)
- trades only strong BUY/SELL signals unless **Also trade weak signals** is on
- goes flat outside 09:30–15:55 ET
- trades at most 3 times a day
- defaults: 1 contract, $2.00 commission per contract and 1 tick of slippage. Set the commission to about $0.50 for MNQ.

## Tuning for win rate

Win rate and profit factor pull against each other, so watch both in the Strategy Tester:

- **Higher win rate:**
  - set `Minimum score` to 5
  - require FVG and/or SMT too
  - lower `rr` (e.g. 1.0–1.5)
  - turn on the time-of-day volume filter
  - keep only kill zone 1
- **More signals:**
  - set `Minimum score` to 3
  - allow chart-timeframe FVGs and swings
  - lengthen the "stays valid" windows
- Use **Bar Replay** to confirm signals never appear or disappear after their bar closes.
- Intraday history on TradingView is limited, so check results across several months with Deep Backtesting (if your plan has it) before trusting a number.

This is a tool for finding confluence, not a promise of profit. Test it on a simulator first.
