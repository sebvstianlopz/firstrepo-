"""
5-minute Liquidity Sweep + MSS study: which features give a low failure rate (an "A+" tier)?
(for pinescript/xauusd_liquidity_sweeps_5m.pine)

Signal (same as the 1H indicator): a level is swept (wick through, close back within 3 candles,
depth <= 1.5 ATR), then within 12 candles a close beyond the last minor swing (pivot 2/2) = MSS.
Entry = MSS close, stop = sweep extreme +- 0.3 ATR, exit 2R with break-even at +1R (also 1R shown),
spread 0.30 $, time exit 16 h, one signal per candle per direction.

Liquidity levels: 5m swings (pivot 5), 1H swings (pivot 5 on closed 1H candles), PDH/PDL, PWH/PWL, Asia H/L.

Quality features (fixed BEFORE looking at results):
  KEY   the swept level is higher-timeframe liquidity: 1H swing, PDH/PDL or PWH/PWL
  FAST  MSS within 6 candles of the sweep
  VOL   sweep candle volume >= 1.5 x its 20-candle average
  DISP  MSS candle body >= 1.0 x ATR (displacement)
  TREND trade in the direction of the 1H trend (last closed 1H close vs 1H EMA50)
  SESS  signal between 07:00 and 17:00 UTC
"Failure" = losing trade (break-even exits are not failures).

Samples: OANDA 5m and COMEX GC1! 5m (Sep 3 - Oct 14 2026), OANDA 15m (Jul 16 - Oct 14 2026, proxy).
Usage: python3 sweep_5m_backtest.py > sweep_5m_results.txt
"""
import datetime as dt
import itertools
import os

from liquidity_sweep_backtest import build_levels, minor_pivots
from sweep_filters_backtest import ema, outcome, summarize
from volume_zones_backtest import atr, load, sma

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
FEATS = ["KEY", "FAST", "VOL", "DISP", "TREND", "SESS"]


def resample(bars, secs):
    """Aggregate (t, o, h, l, c, v) bars into `secs` buckets aligned to UTC."""
    out = []
    for b in bars:
        k = b[0] - b[0] % secs
        if out and out[-1][0] == k:
            t, o, h, l, c, v = out[-1]
            out[-1] = (t, o, max(h, b[2]), min(l, b[3]), b[4], v + b[5])
        else:
            out.append((k, b[1], b[2], b[3], b[4], b[5]))
    return out


def htf_context(bars):
    """1H swing levels (ready after the confirming 1H candle closes) and 1H trend per entry bar."""
    h = resample(bars, 3600)
    idx_by_t = {b[0]: i for i, b in enumerate(bars)}
    levels = []
    for i in range(10, len(h)):
        p = i - 5
        hs = [x[2] for x in h[p - 5:i + 1]]
        ls = [x[3] for x in h[p - 5:i + 1]]
        ready = h[i][0] + 3600
        j = next((idx_by_t[t] for t in range(ready, ready + 4 * 3600, 300) if t in idx_by_t), None)
        if j is None:
            continue
        if h[p][2] == max(hs) and hs.count(h[p][2]) == 1:
            levels.append((j, h[p][2], True, "HTF"))
        if h[p][3] == min(ls) and ls.count(h[p][3]) == 1:
            levels.append((j, h[p][3], False, "HTF"))
    e = ema([x[4] for x in h], 50)
    # trend known for an entry bar = last CLOSED 1H candle
    trend, hi = [], 0
    for b in bars:
        while hi + 1 < len(h) and h[hi + 1][0] + 3600 <= b[0]:
            hi += 1
        closed = hi if h[hi][0] + 3600 <= b[0] else hi - 1
        trend.append(0 if closed < 50 else (1 if h[closed][4] > e[closed] else -1))
    return levels, trend


def signals(bars, per_hour):
    n = len(bars)
    A = atr(bars)
    V = sma([b[5] for b in bars], 20)
    ph, pl = minor_pivots(bars)
    hlev, trend = htf_context(bars)
    sigs = {}
    for (i0, lv, is_high, kind) in build_levels(bars, A) + hlev:
        c0 = bars[i0 - 1][4]
        if (is_high and c0 >= lv) or (not is_high and c0 <= lv):
            continue
        for j in range(i0, min(n, i0 + 240 * per_hour)):
            _, o, h, l, c, v = bars[j]
            if not ((is_high and h > lv) or (not is_high and l < lv)):
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
            mlv = next((src[k] for k in range(hit, max(0, hit - 200), -1) if k in src), None)
            if mlv is None:
                break
            for k in range(hit, min(n, hit + 13)):
                ext = min(ext, bars[k][3]) if d == 1 else max(ext, bars[k][2])
                if (d == 1 and bars[k][4] > mlv) or (d == -1 and bars[k][4] < mlv):
                    entry = bars[k][4]
                    feat = dict(
                        KEY=kind in ("HTF", "PD", "PW"),
                        FAST=(k - hit) <= 6,
                        VOL=V[j - 1] > 0 and bars[j][5] >= 1.5 * V[j - 1],
                        DISP=abs(bars[k][4] - bars[k][1]) >= 1.0 * A[k],
                        TREND=trend[k] == d,
                        SESS=7 <= dt.datetime.fromtimestamp(bars[k][0], dt.timezone.utc).hour < 17,
                    )
                    s = dict(bar=k, dir=d, entry=entry,
                             stop=ext - 0.3 * A[k] if d == 1 else ext + 0.3 * A[k],
                             feat=feat, time=bars[k][0], kind=kind)
                    key = (k, d)
                    score = sum(feat.values())
                    if key not in sigs or score > sum(sigs[key]["feat"].values()):
                        sigs[key] = s
                    break
            break
    return sorted(sigs.values(), key=lambda s: s["bar"])


SAMPLES = [("OANDA 5m", "xauusd_5m.csv", 12), ("COMEX 5m", "gc1_5m.csv", 12), ("OANDA 15m", "xauusd_15m.csv", 4)]


def report(data, name, pred, exits=(("2R+BE", 2.0, True),)):
    print(f"  {name}")
    for ename, rr, be in exits:
        for label, (bars, ph, sg) in data.items():
            rs = [r for r in (outcome(bars, s, rr, be, ph) for s in sg if pred(s["feat"])) if r is not None]
            half = len(rs) // 2
            f1 = 100 * sum(r < -0.05 for r in rs[:half]) / half if half else float("nan")
            f2 = 100 * sum(r < -0.05 for r in rs[half:]) / (len(rs) - half) if len(rs) - half else float("nan")
            print(f"    {ename:<6}{label:<10} {summarize(rs)}   fail halves {f1:4.0f}% / {f2:4.0f}%")


if __name__ == "__main__":
    data = {}
    for label, f, ph in SAMPLES:
        bars = load(os.path.join(D, f))
        data[label] = (bars, ph, signals(bars, ph))
    print("######## single features")
    report(data, "none (all signals)", lambda f: True, (("1R", 1.0, False), ("2R+BE", 2.0, True)))
    for ft in FEATS:
        report(data, ft, lambda f, ft=ft: f[ft])
    print("\n######## pairs")
    for a, b in itertools.combinations(FEATS, 2):
        report(data, f"{a}+{b}", lambda f, a=a, b=b: f[a] and f[b])
