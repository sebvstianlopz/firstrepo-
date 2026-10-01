"""
Liquidity-sweep backtest for XAUUSD (rules fixed before looking at results).

Liquidity pools (levels where stops sit)
  SWING : confirmed swing highs / lows of the chart timeframe (pivot 5 left / 5 right)
  PD    : previous trading-day high / low (day rolls at 17:00 New York)
  PW    : previous week high / low
  ASIA  : Asia session high / low (00:00-07:00 UTC), live until the next Asia session
A level is "consumed" the first time price trades beyond it - only the FIRST sweep counts.

Sweep signal (reversal)
  Sell-side sweep (BUY):  low trades below a low-level and the candle CLOSES back above it.
  Buy-side sweep (SELL):  high trades above a high-level and the candle CLOSES back below it.
  Variant "reclaim3": if the breach candle closes beyond, a close back inside within 3 candles also counts.
  Variant "mss"     : after a reclaim3 sweep, wait up to 12 candles for a close beyond the last minor swing
                      (pivot 2/2) on the other side = market structure shift; enter on that close.
  Sweep depth must be <= 1.5 x ATR (deeper = real breakout, not a sweep).
Trade
  Entry = signal close.  Stop = sweep extreme -/+ 0.3 x ATR.  Target = rr x risk.
  Spread 0.30 $.  Stop first if both hit in one candle.  Time exit after 16 hours.
  One signal per candle per direction.
Controls
  The same rules on random levels (each real level shifted 1-3 ATR up or down).

Samples: OANDA 1H & COMEX 1H (10 months), OANDA 15m (2.5 months), OANDA & COMEX 5m (4 weeks).

Usage: python3 liquidity_sweep_backtest.py > liquidity_sweep_results.txt
"""
import datetime as dt
import os
import random
from zoneinfo import ZoneInfo

from breakout_backtest import fmt, stats
from volume_zones_backtest import atr, load

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
NY = ZoneInfo("America/New_York")
SPREAD = 0.30


def tday(t):
    return (dt.datetime.fromtimestamp(t, NY) + dt.timedelta(hours=7)).date()


def build_levels(bars, A, piv=5):
    """List of (ready_bar, price, is_high, kind)."""
    lv = []
    n = len(bars)
    for i in range(2 * piv, n):
        p = i - piv
        hs = [bars[k][2] for k in range(p - piv, i + 1)]
        ls = [bars[k][3] for k in range(p - piv, i + 1)]
        if bars[p][2] == max(hs) and hs.count(bars[p][2]) == 1:
            lv.append((i + 1, bars[p][2], True, "SWING"))
        if bars[p][3] == min(ls) and ls.count(bars[p][3]) == 1:
            lv.append((i + 1, bars[p][3], False, "SWING"))
    # previous day / week, Asia session
    dh = dl = wh = wl = ah = al = None
    for i in range(1, n):
        t = bars[i][0]
        d0, d1 = tday(bars[i - 1][0]), tday(t)
        if d1 != d0:
            if dh is not None:
                lv.append((i, dh, True, "PD"))
                lv.append((i, dl, False, "PD"))
            dh, dl = bars[i][2], bars[i][3]
            if d1.isocalendar()[:2] != d0.isocalendar()[:2]:
                if wh is not None:
                    lv.append((i, wh, True, "PW"))
                    lv.append((i, wl, False, "PW"))
                wh, wl = bars[i][2], bars[i][3]
        dh = bars[i][2] if dh is None else max(dh, bars[i][2])
        dl = bars[i][3] if dl is None else min(dl, bars[i][3])
        wh = bars[i][2] if wh is None else max(wh, bars[i][2])
        wl = bars[i][3] if wl is None else min(wl, bars[i][3])
        hr = dt.datetime.fromtimestamp(t, dt.timezone.utc).hour
        hr0 = dt.datetime.fromtimestamp(bars[i - 1][0], dt.timezone.utc).hour
        in_asia, was_asia = hr < 7, hr0 < 7
        if in_asia and not was_asia:
            ah, al = bars[i][2], bars[i][3]
        elif in_asia:
            ah, al = max(ah if ah else bars[i][2], bars[i][2]), min(al if al else bars[i][3], bars[i][3])
        elif was_asia and ah is not None:
            lv.append((i, ah, True, "ASIA"))
            lv.append((i, al, False, "ASIA"))
    return lv


def minor_pivots(bars, k=2):
    ph, pl = {}, {}
    for i in range(2 * k, len(bars)):
        p = i - k
        hs = [bars[x][2] for x in range(p - k, i + 1)]
        ls = [bars[x][3] for x in range(p - k, i + 1)]
        if bars[p][2] == max(hs) and hs.count(bars[p][2]) == 1:
            ph[i] = bars[p][2]
        if bars[p][3] == min(ls) and ls.count(bars[p][3]) == 1:
            pl[i] = bars[p][3]
    return ph, pl


def run(bars, rr=2.0, per_hour=1, variant="wick", seed=17, max_age_h=24 * 10, mss_bars=12):
    A = atr(bars)
    n = len(bars)
    rnd = random.Random(seed)
    levels = build_levels(bars, A)
    sigs = []
    for (i0, price, is_high, kind) in levels:
        cands = [(price, False)]
        for _ in range(3):
            cands.append((price + rnd.choice((-1, 1)) * rnd.uniform(1, 3) * A[i0 - 1], True))
        for (lv, ctl) in cands:
            # level must be on the correct side of price when it becomes active
            c0 = bars[i0 - 1][4]
            if (is_high and c0 >= lv) or (not is_high and c0 <= lv):
                continue
            for j in range(i0, min(n, i0 + max_age_h * per_hour)):
                _, o, h, l, c, _ = bars[j]
                a = A[j]
                if is_high and h > lv:
                    depth = h - lv
                    ext = h
                    hit = None
                    if c < lv:
                        hit = j
                    elif variant in ("reclaim3", "mss"):
                        for k in range(j + 1, min(n, j + 4)):
                            ext = max(ext, bars[k][2])
                            if bars[k][4] < lv:
                                hit = k
                                break
                    if hit is not None and (ext - lv) <= 1.5 * A[hit]:
                        sigs.append((hit, -1, ext, kind, ctl))
                    break
                if not is_high and l < lv:
                    ext = l
                    hit = None
                    if c > lv:
                        hit = j
                    elif variant in ("reclaim3", "mss"):
                        for k in range(j + 1, min(n, j + 4)):
                            ext = min(ext, bars[k][3])
                            if bars[k][4] > lv:
                                hit = k
                                break
                    if hit is not None and (lv - ext) <= 1.5 * A[hit]:
                        sigs.append((hit, 1, ext, kind, ctl))
                    break
    if variant == "mss":
        # convert each reclaim3 sweep into an MSS entry (or drop it)
        ph, pl = minor_pivots(bars)
        conv = []
        for (j, d, ext, kind, ctl) in sigs:
            src = ph if d == 1 else pl
            lvl = None
            for k in range(j, max(0, j - 200), -1):
                if k in src:
                    lvl = src[k]
                    break
            if lvl is None:
                continue
            for k in range(j, min(n, j + mss_bars + 1)):
                ext = min(ext, bars[k][3]) if d == 1 else max(ext, bars[k][2])
                if (d == 1 and bars[k][4] < ext) or (d == -1 and bars[k][4] > ext):
                    break
                if (d == 1 and bars[k][4] > lvl) or (d == -1 and bars[k][4] < lvl):
                    conv.append((k, d, ext, kind, ctl))
                    break
        sigs = conv
    # one signal per candle per direction (separately for real / control)
    seen, uniq = set(), []
    for s in sorted(sigs):
        key = (s[0], s[1], s[4])
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    out = []
    for (j, d, ext, kind, ctl) in uniq:
        entry = bars[j][4]
        stop = ext - 0.3 * A[j] if d == 1 else ext + 0.3 * A[j]
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        tgt = entry + d * rr * risk
        r = None
        for k in range(j + 1, min(n, j + 1 + 16 * per_hour)):
            _, _, hh, ll, _, _ = bars[k]
            if (d == 1 and ll <= stop) or (d == -1 and hh >= stop):
                r = -1.0
                break
            if (d == 1 and hh >= tgt) or (d == -1 and ll <= tgt):
                r = rr
                break
        if r is None:
            r = d * (bars[min(n - 1, j + 16 * per_hour)][4] - entry) / risk
        out.append(dict(ctl=ctl, r=r - SPREAD / risk, risk=risk, time=bars[j][0], dir=d, kind=kind,
                        entry=entry, stop=stop, tgt=tgt))
    return out


SAMPLES = [
    ("H1 OANDA 1H (10 months)", "xauusd_1h.csv", 1),
    ("H2 COMEX GC1! 1H (10 months)", "gc1_1h.csv", 1),
    ("B  OANDA 15m (2.5 months)", "xauusd_15m.csv", 4),
    ("A  OANDA 5m (4 weeks)", "xauusd_5m.csv", 12),
    ("C  COMEX GC1! 5m (4 weeks)", "gc1_5m.csv", 12),
]

if __name__ == "__main__":
    for label, f, ph in SAMPLES:
        bars = load(os.path.join(D, f))
        print(f"\n==================== {label}")
        for variant in ("wick", "reclaim3", "mss"):
            for rr in (1.0, 2.0):
                tr = run(bars, rr=rr, per_hour=ph, variant=variant)
                R = [t for t in tr if not t["ctl"]]
                C = [t for t in tr if t["ctl"]]
                print(f"  {variant:<8} {rr}R  ALL real   {fmt(stats(R))}")
                print(f"  {'':<8} {'':4} ALL random {fmt(stats(C))}")
                if R:
                    half = sorted(t["time"] for t in R)[len(R) // 2]
                    print(f"  {'':<8} {'':4} 1st half   {fmt(stats([t for t in R if t['time'] < half]))}")
                    print(f"  {'':<8} {'':4} 2nd half   {fmt(stats([t for t in R if t['time'] >= half]))}")
                for kind in ("SWING", "PD", "PW", "ASIA"):
                    Rk = [t for t in R if t["kind"] == kind]
                    Ck = [t for t in C if t["kind"] == kind]
                    if Rk:
                        print(f"  {'':<8} {'':4} {kind:<5} real {fmt(stats(Rk))}   | random avg "
                              f"{(sum(t['r'] for t in Ck) / len(Ck)) if Ck else float('nan'):+.2f}R")
