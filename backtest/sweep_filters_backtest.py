"""
Which filters / exits lower the failure rate of the Liquidity Sweep + MSS signal?
(pinescript/xauusd_liquidity_sweeps.pine)

Base signal = liquidity_sweep_backtest.py "mss" variant (reclaim within 3 candles, depth <= 1.5 ATR,
MSS = close beyond the last minor swing (pivot 2/2) within 12 candles; stop = sweep extreme +- 0.3 ATR).

Candidate filters (fixed list, decided BEFORE looking at results):
  A     grade A: the swept level is a previous day / week high or low
  TREND trade with the 200 EMA (long only above it, short only below it)
  SESS  signal between 07:00 and 17:00 UTC (London + New York)
  FAST  MSS within 6 candles of the sweep
  TIGHT stop distance <= 2 x ATR
  VOL   sweep candle volume >= 1.5 x its 20-candle average
Exits:
  1R / 1.5R / 2R targets, and "2R+BE" = 2R target with the stop moved to entry after +1R.
"Failure" = the trade lost money (full stop, or a losing time exit). Break-even exits are not failures.

Usage: python3 sweep_filters_backtest.py > sweep_filters_results.txt
"""
import datetime as dt
import os

from liquidity_sweep_backtest import build_levels, minor_pivots
from volume_zones_backtest import atr, load, sma

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
SPREAD = 0.30
OOS_START = 1790744400 + 3600   # first bar after the data used for the original indicator (2026-09-30)


def ema(xs, n):
    k, out, e = 2 / (n + 1), [], None
    for x in xs:
        e = x if e is None else e + k * (x - e)
        out.append(e)
    return out


def signals(bars, per_hour):
    """All sweep + MSS signals with features (real levels only, one per candle per direction)."""
    n = len(bars)
    A = atr(bars)
    E = ema([b[4] for b in bars], 200)
    V = sma([b[5] for b in bars], 20)
    ph, pl = minor_pivots(bars)
    sigs = {}
    for (i0, lv, is_high, kind) in build_levels(bars, A):
        c0 = bars[i0 - 1][4]
        if (is_high and c0 >= lv) or (not is_high and c0 <= lv):
            continue
        for j in range(i0, min(n, i0 + 240 * per_hour)):
            _, o, h, l, c, v = bars[j]
            breach = (is_high and h > lv) or (not is_high and l < lv)
            if not breach:
                continue
            d = -1 if is_high else 1
            ext = h if is_high else l
            hit = j if (is_high and c < lv) or (not is_high and c > lv) else None
            if hit is None:
                for k in range(j + 1, min(n, j + 4)):
                    ext = max(ext, bars[k][2]) if is_high else min(ext, bars[k][3])
                    if (is_high and bars[k][4] < lv) or (not is_high and bars[k][4] > lv):
                        hit = k
                        break
            if hit is None or abs(ext - lv) > 1.5 * A[hit]:
                break
            src = ph if d == 1 else pl
            mlv = None
            for k in range(hit, max(0, hit - 200), -1):
                if k in src:
                    mlv = src[k]
                    break
            if mlv is None:
                break
            for k in range(hit, min(n, hit + 13)):
                ext = min(ext, bars[k][3]) if d == 1 else max(ext, bars[k][2])
                if (d == 1 and bars[k][4] > mlv) or (d == -1 and bars[k][4] < mlv):
                    key = (k, d)
                    entry = bars[k][4]
                    stop = ext - 0.3 * A[k] if d == 1 else ext + 0.3 * A[k]
                    vr = bars[j][5] / V[j - 1] if j > 0 and V[j - 1] > 0 else 0
                    feat = dict(
                        A=kind in ("PD", "PW"),
                        TREND=(entry > E[k]) if d == 1 else (entry < E[k]),
                        SESS=7 <= dt.datetime.fromtimestamp(bars[k][0], dt.timezone.utc).hour < 17,
                        FAST=(k - hit) <= 6,
                        TIGHT=abs(entry - stop) <= 2.0 * A[k],
                        VOL=vr >= 1.5,
                    )
                    if key not in sigs or (feat["A"] and not sigs[key]["feat"]["A"]):
                        sigs[key] = dict(bar=k, dir=d, entry=entry, stop=stop, feat=feat, time=bars[k][0])
                    break
            break
    return sorted(sigs.values(), key=lambda s: s["bar"])


def outcome(bars, s, rr, be, per_hour):
    n = len(bars)
    d, entry, stop = s["dir"], s["entry"], s["stop"]
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    tgt = entry + d * rr * risk
    cur_stop, moved = stop, False
    r = None
    for k in range(s["bar"] + 1, min(n, s["bar"] + 1 + 16 * per_hour)):
        _, _, h, l, _, _ = bars[k]
        if (d == 1 and l <= cur_stop) or (d == -1 and h >= cur_stop):
            r = 0.0 if moved else -1.0
            break
        if (d == 1 and h >= tgt) or (d == -1 and l <= tgt):
            r = rr
            break
        if be and not moved and ((d == 1 and h >= entry + risk) or (d == -1 and l <= entry - risk)):
            cur_stop, moved = entry, True
    if r is None:
        r = d * (bars[min(n - 1, s["bar"] + 16 * per_hour)][4] - entry) / risk
    return r - SPREAD / risk


def summarize(rs):
    if not rs:
        return "n=0"
    n = len(rs)
    fail = sum(r < -0.05 for r in rs)
    eq = peak = dd = 0.0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    return f"n={n:<4} fail {100 * fail / n:5.1f}%  win {100 * sum(r > 0.05 for r in rs) / n:5.1f}%  avg {sum(rs) / n:+.2f}R  total {sum(rs):+6.1f}R  maxDD {dd:4.1f}R"


SAMPLES = [
    ("OANDA 1H", "xauusd_1h.csv", 1),
    ("COMEX 1H", "gc1_1h.csv", 1),
    ("OANDA 15m", "xauusd_15m.csv", 4),
    ("OANDA 5m", "xauusd_5m.csv", 12),
]
FILTERS = ["none", "A", "TREND", "SESS", "FAST", "TIGHT", "VOL"]
EXITS = [("1R", 1.0, False), ("1.5R", 1.5, False), ("2R", 2.0, False), ("2R+BE", 2.0, True)]

if __name__ == "__main__":
    data = {}
    for label, f, ph in SAMPLES:
        bars = load(os.path.join(D, f))
        data[label] = (bars, ph, signals(bars, ph))
    for ename, rr, be in EXITS:
        print(f"\n######## exit {ename}")
        for flt in FILTERS:
            print(f"  filter {flt}")
            for label, (bars, ph, sg) in data.items():
                xs = [s for s in sg if flt == "none" or s["feat"][flt]]
                rs = [r for r in (outcome(bars, s, rr, be, ph) for s in xs) if r is not None]
                half = len(rs) // 2
                h1 = sum(rs[:half]) / half if half else float("nan")
                h2 = sum(rs[half:]) / (len(rs) - half) if len(rs) - half else float("nan")
                print(f"    {label:<10} {summarize(rs)}   halves {h1:+.2f} / {h2:+.2f}")
