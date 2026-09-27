# Trading rules

These are the owner's rules. The strategy code must follow them exactly and must not add new signals.
Lines marked **(interpretation)** are how the code reads a rule where the wording left room; the owner
should confirm or correct them.

## 1. Time
- Trades are only opened during the New York session, **09:00–11:59 New York time**.

## 2. High volume area (HVA) reaction
- Price must react to a high volume area. A high volume area is either:
  - **a higher-timeframe FVG** (default: 15-minute), or
  - **a break-of-structure level**, meaning a swing high or low that price later closed through.
- **(interpretation)** "Reacting" means a 1-minute candle touches the area during 09:00–11:59.

## 3. SMT divergence
- There must be a **bullish SMT** (for longs) or a **bearish SMT** (for shorts) between the traded
  market and its partner (NQ vs ES, or NAS100 vs SPX500).
  - Bullish SMT: at a swing low, one market makes a lower low and the other does not.
  - Bearish SMT: at a swing high, one market makes a higher high and the other does not.
- **(interpretation)** The SMT must come within 30 one-minute bars after the HVA touch.

## 4. 1-minute FVG inversion (the trigger)
- A 1-minute fair value gap must be inverted:
  - Long: a candle closes above the top of a bearish 1-minute FVG.
  - Short: a candle closes below the bottom of a bullish 1-minute FVG.
- **(interpretation)** The inversion must come within 30 one-minute bars after the SMT. The trade is
  entered when that candle closes.

## 5. Risk (placeholder — NOT yet approved by the owner)
- Stop-loss: just past the SMT swing (below the swing low for longs, above the swing high for shorts).
- Target: 2 × the risk.
- Size: 1 contract.
- Any open trade is closed at 15:55 New York time.

## 6. Process
- Every strategy change is backtested in TradingView before it counts as done.
- Everything is written in Pine Script (version 6).
