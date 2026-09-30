"""
Backtest for the volume-based XAUUSD reaction zones (1H focus).

Zone ideas tested (all known at the close of the candle that creates them):
  REJ   High-volume REJECTION: volume >= k x avg volume and a long wick.
        Zone = the wick (extreme -> body edge).
  CONT  High-volume CONTINUATION: displacement candle (body >= 1 ATR, closes near
        its extreme) on volume >= k x avg. Zone = origin of the move (open -> extreme).
  ABS   ABSORPTION: volume >= k x avg but a small range (<= 0.8 ATR).
        Zone = the whole candle.
  POC   Previous-day volume Point Of Control (price with the most volume).

Every real zone gets 3 CONTROL zones of the same size shifted randomly 1-3 ATR.
Real vs control shows whether the zone location matters or it's just chance.

Tests per touch (first touch of a zone only, price entering from outside):
  react%  : price moves 1 ATR away in the bounce direction before a close 0.3 ATR
            through the far side (within `look` bars).
  trade R : limit entry at the zone edge, stop = far side + 0.3 ATR, target 1R or 2R,
            spread cost 0.30 $ per trade.
Results are split into first half / second half of the data (out-of-sample check).

Usage: python3 volume_zones_backtest.py [csv]   (default ../data/xauusd_1h.csv)
"""
import csv
import datetime as dt
import os
import random
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
NY = ZoneInfo("America/New_York")
SPREAD = 0.30


def load(path):
    with open(path) as f:
        return [(int(r["time"]), float(r["open"]), float(r["high"]), float(r["low"]),
                 float(r["close"]), float(r["volume"])) for r in csv.DictReader(f)]


def atr(bars, n=14):
    out, prev = [], None
    for i, b in enumerate(bars):
        h, l = b[2], b[3]
        tr = h - l if i == 0 else max(h - l, abs(h - bars[i - 1][4]), abs(l - bars[i - 1][4]))
        prev = tr if prev is None else (prev * (n - 1) + tr) / n
        out.append(prev)
    return out


def sma(xs, n):
    out, s = [], 0.0
    for i, x in enumerate(xs):
        s += x
        if i >= n:
            s -= xs[i - n]
        out.append(s / min(i + 1, n))
    return out


def trading_day(t):
    return (dt.datetime.fromtimestamp(t, NY) + dt.timedelta(hours=7)).date()


def clamp_zone(ext, edge, a, is_top, min_w=0.15, max_w=0.6):
    """Zone anchored at price `ext` (the extreme) reaching toward `edge`."""
    w = min(max(abs(ext - edge), min_w * a), max_w * a)
    return (ext, ext - w) if is_top else (ext + w, ext)


def generate(bars, A, cfg):
    """Return list of (bar_index_created, top, bot, kind, meta)."""
    vol = [b[5] for b in bars]
    vavg = sma(vol, cfg["vol_len"])
    zones = []
    day_vol, day_key = {}, None
    for i in range(cfg["vol_len"] + 1, len(bars)):
        t, o, h, l, c, v = bars[i]
        a = A[i]
        rng = h - l
        vr = v / vavg[i - 1] if vavg[i - 1] > 0 else 0
        k = cfg["vol_k"]
        up_w = h - max(o, c)
        dn_w = min(o, c) - l
        body = abs(c - o)
        if rng > 0 and vr >= k:
            # REJ: long wick on high volume
            if up_w >= cfg["wick"] * rng:
                zones.append((i, *clamp_zone(h, max(o, c), a, True), "REJ", vr))
            if dn_w >= cfg["wick"] * rng:
                zones.append((i, *clamp_zone(l, min(o, c), a, False), "REJ", vr))
            # CONT: displacement candle, zone at its origin
            if body >= cfg["disp"] * a:
                if c > o and (h - c) <= 0.25 * rng:
                    zones.append((i, *clamp_zone(l, o, a, False), "CONT", vr))
                if c < o and (c - l) <= 0.25 * rng:
                    zones.append((i, *clamp_zone(h, o, a, True), "CONT", vr))
            # ABS: big volume, small range
            if rng <= cfg["abs_rng"] * a:
                mid = (h + l) / 2
                half = max(rng / 2, 0.15 * a)
                zones.append((i, mid + half, mid - half, "ABS", vr))
        # POC of the previous trading day
        d = trading_day(t)
        if d != day_key:
            if day_vol:
                poc = max(day_vol, key=day_vol.get) * cfg["poc_bin"]
                zones.append((i, poc + 0.15 * a, poc - 0.15 * a, "POC", 0))
            day_vol, day_key = {}, d
        lo_b, hi_b = int(l // cfg["poc_bin"]), int(h // cfg["poc_bin"])
        share = v / (hi_b - lo_b + 1)
        for bb in range(lo_b, hi_b + 1):
            day_vol[bb] = day_vol.get(bb, 0) + share
    return zones


def evaluate(bars, A, zones, cfg, seed=11):
    """First-touch outcome for each real zone and its 3 controls."""
    rnd = random.Random(seed)
    items = []
    for (i, top, bot, kind, vr) in zones:
        items.append((i, top, bot, kind, vr, False))
        for _ in range(3):
            off = rnd.choice((-1, 1)) * rnd.uniform(1.0, 3.0) * A[i]
            items.append((i, top + off, bot + off, kind, vr, True))
    out = []
    n = len(bars)
    for (i, top, bot, kind, vr, ctl) in items:
        # find first touch: price enters from outside, within max_age bars
        j_end = min(n, i + 1 + cfg["max_age"])
        touch = None
        for j in range(i + 1, j_end):
            pc = bars[j - 1][4]
            if pc > top and bars[j][3] <= top:
                touch = (j, 1)
                break
            if pc < bot and bars[j][2] >= bot:
                touch = (j, -1)
                break
            if bot <= pc <= top:      # price sitting inside the zone -> not a clean test
                continue
        if not touch:
            continue
        j, d = touch
        a = A[i]
        _, o, h, l, c, _ = bars[j]
        rej = c > top if d == 1 else c < bot
        # reaction test
        react = 0
        for k in range(j + 1, min(n, j + 1 + cfg["look"])):
            _, _, hh, ll, cc, _ = bars[k]
            if d == 1:
                if cc < bot - 0.3 * a:
                    break
                if hh >= top + 1.0 * a:
                    react = 1
                    break
            else:
                if cc > top + 0.3 * a:
                    break
                if ll <= bot - 1.0 * a:
                    react = 1
                    break
        # limit-order trade at the zone edge
        entry = top if d == 1 else bot
        stop = bot - 0.3 * a if d == 1 else top + 0.3 * a
        risk = abs(entry - stop)
        res = {}
        for rr in (1.0, 2.0):
            tgt = entry + d * rr * risk
            r = None
            # touch bar: stop may already be hit
            if (d == 1 and l <= stop) or (d == -1 and h >= stop):
                r = -1.0
            else:
                for k in range(j + 1, min(n, j + 1 + 3 * cfg["look"])):
                    _, _, hh, ll, cc, _ = bars[k]
                    if (d == 1 and ll <= stop) or (d == -1 and hh >= stop):
                        r = -1.0
                        break
                    if (d == 1 and hh >= tgt) or (d == -1 and ll <= tgt):
                        r = rr
                        break
                if r is None:
                    cc = bars[min(n - 1, j + 3 * cfg["look"])][4]
                    r = d * (cc - entry) / risk
            res[rr] = r - SPREAD / risk
        out.append(dict(kind=kind, ctl=ctl, bar=j, react=react, rej=rej, vr=vr,
                        r1=res[1.0], r2=res[2.0], wait=j - i))
    return out


def summarize(ev, label, half):
    def stats(xs):
        if not xs:
            return "   n=0"
        n = len(xs)
        return (f"n={n:<5} react {100 * sum(e['react'] for e in xs) / n:5.1f}%  "
                f"1R {sum(e['r1'] for e in xs) / n:+.3f}  2R {sum(e['r2'] for e in xs) / n:+.3f}")
    print(f"\n--- {label}")
    for kind in sorted({e["kind"] for e in ev}):
        for part, f in (("1st half", lambda e: e["bar"] < half), ("2nd half", lambda e: e["bar"] >= half)):
            R = [e for e in ev if e["kind"] == kind and not e["ctl"] and f(e)]
            C = [e for e in ev if e["kind"] == kind and e["ctl"] and f(e)]
            print(f"{kind:<5}{part}  REAL {stats(R)}")
            print(f"{'':<5}{'':8}  RAND {stats(C)}")


CFG = dict(vol_len=20, vol_k=2.0, wick=0.5, disp=1.0, abs_rng=0.8, poc_bin=2.0,
           look=8, max_age=24 * 15)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "xauusd_1h.csv")
    bars = load(path)
    A = atr(bars)
    half = len(bars) // 2
    for k in (1.5, 2.0, 2.5):
        cfg = dict(CFG, vol_k=k)
        ev = evaluate(bars, A, generate(bars, A, cfg), cfg)
        summarize(ev, f"volume >= {k} x 20-bar average", half)
