"""
Backtest: 1H Liquidity Sweep / Break of Structure  ->  5m high-volume rejection of the zone.
Written from scratch for liq_bos_rejection.pine (rules fixed before looking at results).

1H CONTEXT (built from CLOSED 1H candles)
  Swing high / low : 1H pivot, 3 candles each side.
  Bullish BOS      : a 1H candle CLOSES above the last unbroken swing high.
  Bearish BOS      : a 1H candle CLOSES below the last unbroken swing low.
  Bullish sweep    : a 1H candle trades below the last swing low but CLOSES back above it.
  Bearish sweep    : a 1H candle trades above the last swing high but CLOSES back below it.
  Bias             : direction of the most recent 1H event.

ZONES created by each event (live 24 hours, used once)
  BOS level   : the broken swing level, retest zone = level -> 0.35 x 1H ATR beyond it (back towards origin)
  BOS origin  : the last opposite-colour 1H candle before the BOS candle (demand / supply), max 1 x 1H ATR tall
  Sweep wick  : from the swept level to the sweep extreme
  A zone is cancelled when a candle closes 0.25 x 1H ATR beyond its far side.

5m REJECTION SIGNAL (BUY at a bullish zone, SELL at a bearish zone)
  - the candle trades into the zone and CLOSES back outside it, on the bullish/bearish side
  - rejection wick >= 50 % of the candle range
  - volume >= 1.8 x average volume of the previous 20 candles
  - (default) the zone direction matches the 1H bias
TRADE (for measuring): entry = signal close, stop = wick extreme -/+ 0.2 x 5m ATR, target 2R,
  spread 0.30 $, stop checked first, time exit after 8 hours. Failure = losing trade.

Usage: python3 backtest.py > results.txt
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SPREAD = 0.30


def load(name):
    with open(os.path.join(HERE, "data", name)) as f:
        return [(int(r["time"]), float(r["open"]), float(r["high"]), float(r["low"]),
                 float(r["close"]), float(r["volume"])) for r in csv.DictReader(f)]


def wilder_atr(rows, n=14):
    out, a = [], None
    for i, (_, o, h, l, c, _) in enumerate(rows):
        tr = h - l if i == 0 else max(h - l, abs(h - rows[i - 1][4]), abs(l - rows[i - 1][4]))
        a = tr if a is None else (a * (n - 1) + tr) / n
        out.append(a)
    return out


def to_hourly(rows):
    out = []
    for t, o, h, l, c, v in rows:
        k = t - t % 3600
        if out and out[-1][0] == k:
            _, o0, h0, l0, _, v0 = out[-1]
            out[-1] = (k, o0, max(h0, h), min(l0, l), c, v0 + v)
        else:
            out.append((k, o, h, l, c, v))
    return out


def hourly_zones(h1):
    """Return list of zones: dict(ready_time, top, bot, dir, kind, atr1) and bias changes [(ready_time, dir)]."""
    A = wilder_atr(h1)
    P = 3
    zones, bias = [], []
    sh = sl = None          # (price) last unbroken swing high / low
    for i in range(len(h1)):
        t, o, h, l, c, _ = h1[i]
        ready = t + 3600     # usable once this 1H candle has closed
        a = A[i]
        # new swings confirmed at this candle (pivot centred P candles back)
        if i >= 2 * P:
            p = i - P
            win = h1[p - P:i + 1]
            if h1[p][2] == max(x[2] for x in win) and [x[2] for x in win].count(h1[p][2]) == 1:
                sh = h1[p][2]
            if h1[p][3] == min(x[3] for x in win) and [x[3] for x in win].count(h1[p][3]) == 1:
                sl = h1[p][3]
        if sh is not None:
            if c > sh:                                         # bullish BOS
                zones.append(dict(ready=ready, top=sh, bot=sh - 0.35 * a, dir=1, kind="BOS level", atr1=a))
                for k in range(i - 1, max(-1, i - 11), -1):    # last bearish candle = demand origin
                    if h1[k][4] < h1[k][1]:
                        top, bot = h1[k][1], h1[k][3]
                        zones.append(dict(ready=ready, top=top, bot=max(bot, top - a), dir=1, kind="BOS origin", atr1=a))
                        break
                bias.append((ready, 1))
                sh = None
            elif h > sh and c < sh:                            # bearish sweep of the high
                zones.append(dict(ready=ready, top=h, bot=sh, dir=-1, kind="Sweep", atr1=a))
                bias.append((ready, -1))
                sh = None
        if sl is not None:
            if c < sl:                                         # bearish BOS
                zones.append(dict(ready=ready, top=sl + 0.35 * a, bot=sl, dir=-1, kind="BOS level", atr1=a))
                for k in range(i - 1, max(-1, i - 11), -1):    # last bullish candle = supply origin
                    if h1[k][4] > h1[k][1]:
                        top, bot = h1[k][2], h1[k][1]
                        zones.append(dict(ready=ready, top=min(top, bot + a), bot=bot, dir=-1, kind="BOS origin", atr1=a))
                        break
                bias.append((ready, -1))
                sl = None
            elif l < sl and c > sl:                            # bullish sweep of the low
                zones.append(dict(ready=ready, top=sl, bot=l, dir=1, kind="Sweep", atr1=a))
                bias.append((ready, 1))
                sl = None
    return zones, bias


def is_rejection(bar, avg_vol, d, top, bot, wick_min, vol_k):
    _, o, h, l, c, v = bar
    rng = h - l
    if rng <= 0 or avg_vol <= 0 or v < vol_k * avg_vol:
        return False
    if d == 1:
        return l <= top and c > top and (min(o, c) - l) >= wick_min * rng
    return h >= bot and c < bot and (h - max(o, c)) >= wick_min * rng


def trade(rows, A, i, d, per_hour, rr=2.0):
    _, o, h, l, c, _ = rows[i]
    entry = c
    stop = l - 0.2 * A[i] if d == 1 else h + 0.2 * A[i]
    risk = abs(entry - stop)
    tgt = entry + d * rr * risk
    for k in range(i + 1, min(len(rows), i + 1 + 8 * per_hour)):
        _, _, hh, ll, _, _ = rows[k]
        if (d == 1 and ll <= stop) or (d == -1 and hh >= stop):
            return -1.0 - SPREAD / risk
        if (d == 1 and hh >= tgt) or (d == -1 and ll <= tgt):
            return rr - SPREAD / risk
    end = rows[min(len(rows) - 1, i + 8 * per_hour)][4]
    return d * (end - entry) / risk - SPREAD / risk


def run(rows, per_hour, use_bias=True, vol_k=1.8, wick_min=0.5, zones_on=True):
    A = wilder_atr(rows)
    n = len(rows)
    vols = [r[5] for r in rows]
    zones, bias = hourly_zones(to_hourly(rows))
    life = 24 * per_hour
    out, used = [], set()
    # live zones per bar
    zi = 0
    zones.sort(key=lambda z: z["ready"])
    live = []
    bi, cur_bias = 0, 0
    last_sig = {}
    for i in range(20, n):
        t = rows[i][0]
        while zi < len(zones) and zones[zi]["ready"] <= t:
            z = dict(zones[zi], start=i)
            live.append(z)
            zi += 1
        while bi < len(bias) and bias[bi][0] <= t:
            cur_bias = bias[bi][1]
            bi += 1
        avg = sum(vols[i - 20:i]) / 20
        _, o, h, l, c, v = rows[i]
        keep = []
        fired = set()
        for z in live:
            if i - z["start"] > life:
                continue
            if (z["dir"] == 1 and c < z["bot"] - 0.25 * z["atr1"]) or (z["dir"] == -1 and c > z["top"] + 0.25 * z["atr1"]):
                continue
            if z["dir"] in fired:
                keep.append(z)
                continue
            ok_bias = (not use_bias) or z["dir"] == cur_bias
            if ok_bias and is_rejection(rows[i], avg, z["dir"], z["top"], z["bot"], wick_min, vol_k):
                out.append(dict(i=i, dir=z["dir"], kind=z["kind"], r=trade(rows, A, i, z["dir"], per_hour)))
                fired.add(z["dir"])
                continue          # zone used
            keep.append(z)
        live = keep
    if not zones_on:
        # comparison: the same rejection candle with NO zone requirement (any candle, either direction)
        out = []
        for i in range(20, n - 1):
            avg = sum(vols[i - 20:i]) / 20
            _, o, h, l, c, v = rows[i]
            rng = h - l
            if rng <= 0 or v < vol_k * avg:
                continue
            if (min(o, c) - l) >= wick_min * rng and c > o:
                out.append(dict(i=i, dir=1, kind="none", r=trade(rows, A, i, 1, per_hour)))
            elif (h - max(o, c)) >= wick_min * rng and c < o:
                out.append(dict(i=i, dir=-1, kind="none", r=trade(rows, A, i, -1, per_hour)))
    return out


def summary(xs):
    if not xs:
        return "n=0"
    rs = [x["r"] for x in xs]
    n = len(rs)
    fail = 100 * sum(r < 0 for r in rs) / n
    half = n // 2
    f1 = 100 * sum(r < 0 for r in rs[:half]) / half if half else float("nan")
    f2 = 100 * sum(r < 0 for r in rs[half:]) / (n - half)
    return f"n={n:<4} fail {fail:5.1f}%  avg {sum(rs) / n:+.2f}R  total {sum(rs):+6.1f}R   fail 1st/2nd half {f1:3.0f}% / {f2:3.0f}%"


SAMPLES = [("OANDA 5m", "oanda_xauusd_5m.csv", 12), ("COMEX 5m", "comex_gc1_5m.csv", 12), ("OANDA 15m", "oanda_xauusd_15m.csv", 4)]

if __name__ == "__main__":
    for label, f, ph in SAMPLES:
        rows = load(f)
        print(f"\n===== {label}")
        base = run(rows, ph)
        print(f"  DEFAULT (bias on, volume >= 1.8x) : {summary(base)}")
        for kind in ("BOS level", "BOS origin", "Sweep"):
            print(f"     {kind:<11}                    : {summary([x for x in base if x['kind'] == kind])}")
        print(f"  bias filter OFF                    : {summary(run(rows, ph, use_bias=False))}")
        print(f"  volume >= 1.5x                     : {summary(run(rows, ph, vol_k=1.5))}")
        print(f"  volume >= 2.5x                     : {summary(run(rows, ph, vol_k=2.5))}")
        print(f"  volume filter OFF                  : {summary(run(rows, ph, vol_k=0.0))}")
        print(f"  COMPARISON: same candle, NO zone   : {summary(run(rows, ph, zones_on=False))}")
