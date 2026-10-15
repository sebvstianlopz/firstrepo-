"""
v2 - scalping version: more zones, repeat touches, looser rejection, scalp exits.

ZONES (from closed 1H candles)
  Swing S/R   : every confirmed 1H swing low (support) / swing high (resistance), +-0.15 x 1H ATR
  BOS level   : the broken swing level after a 1H BOS (retest zone, 0.35 x 1H ATR deep)
  BOS origin  : the last opposite 1H candle before the BOS (max 1 x 1H ATR tall)
  Sweep       : the wick area of a 1H sweep candle
  Zone life 48 h, up to 3 signals per zone, at least `cool` candles between signals on the same zone.
  A zone is cancelled when a candle closes 0.25 x 1H ATR through it.
SESSION VWAP (optional filter): VWAP that resets every trading day (22:00 UTC).

5m REJECTION (BUY at bullish zones, SELL at bearish zones)
  - candle low trades into the zone (BUY) / high into the zone (SELL)
  - close rule "outside": close back beyond the zone edge;  "half": close beyond the zone middle
  - rejection wick >= wick x candle range, candle closes in the signal direction (close > open for BUY)
  - volume >= vol x average of the previous 20 candles
  - optional: 1H bias (latest BOS / sweep direction), optional: VWAP side (BUY only above VWAP etc.)
SCALP TRADE: entry = close, stop = wick extreme -/+ 0.2 x 5m ATR, target rr x risk,
  spread 0.30 $, stop checked first, time exit after 2 hours.

Settings are chosen on the first 60 % of OANDA 5m ONLY, then checked unchanged on the last 40 %,
COMEX 5m and OANDA 15m.
"""
import csv
import itertools
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


def session_vwap(rows):
    out, pv, vv, day = [], 0.0, 0.0, None
    for t, o, h, l, c, v in rows:
        d = (t - 22 * 3600) // 86400          # trading day rolls at 22:00 UTC
        if d != day:
            pv, vv, day = 0.0, 0.0, d
        tp = (h + l + c) / 3
        pv += tp * v
        vv += v
        out.append(pv / vv if vv > 0 else c)
    return out


def hourly_zones(h1, piv, use_sr):
    A = wilder_atr(h1)
    zones, bias = [], []
    sh = sl = None
    for i in range(len(h1)):
        t, o, h, l, c, _ = h1[i]
        ready, a = t + 3600, A[i]
        if i >= 2 * piv:
            p = i - piv
            win = h1[p - piv:i + 1]
            if h1[p][2] == max(x[2] for x in win) and [x[2] for x in win].count(h1[p][2]) == 1:
                sh = h1[p][2]
                if use_sr:
                    zones.append(dict(ready=ready, top=sh + 0.15 * a, bot=sh - 0.15 * a, dir=-1, kind="Swing S/R", atr1=a))
            if h1[p][3] == min(x[3] for x in win) and [x[3] for x in win].count(h1[p][3]) == 1:
                sl = h1[p][3]
                if use_sr:
                    zones.append(dict(ready=ready, top=sl + 0.15 * a, bot=sl - 0.15 * a, dir=1, kind="Swing S/R", atr1=a))
        if sh is not None:
            if c > sh:
                zones.append(dict(ready=ready, top=sh, bot=sh - 0.35 * a, dir=1, kind="BOS level", atr1=a))
                for k in range(i - 1, max(-1, i - 11), -1):
                    if h1[k][4] < h1[k][1]:
                        top = h1[k][1]
                        zones.append(dict(ready=ready, top=top, bot=max(h1[k][3], top - a), dir=1, kind="BOS origin", atr1=a))
                        break
                bias.append((ready, 1))
                sh = None
            elif h > sh and c < sh:
                zones.append(dict(ready=ready, top=h, bot=sh, dir=-1, kind="Sweep", atr1=a))
                bias.append((ready, -1))
                sh = None
        if sl is not None:
            if c < sl:
                zones.append(dict(ready=ready, top=sl + 0.35 * a, bot=sl, dir=-1, kind="BOS level", atr1=a))
                for k in range(i - 1, max(-1, i - 11), -1):
                    if h1[k][4] > h1[k][1]:
                        bot = h1[k][1]
                        zones.append(dict(ready=ready, top=min(h1[k][2], bot + a), bot=bot, dir=-1, kind="BOS origin", atr1=a))
                        break
                bias.append((ready, -1))
                sl = None
            elif l < sl and c > sl:
                zones.append(dict(ready=ready, top=sl, bot=l, dir=1, kind="Sweep", atr1=a))
                bias.append((ready, 1))
                sl = None
    return sorted(zones, key=lambda z: z["ready"]), bias


def scalp(rows, A, i, d, per_hour, rr, entry_mode="close", stop_mode="wick", zone=None):
    _, o, h, l, c, _ = rows[i]
    stop = l - 0.2 * A[i] if d == 1 else h + 0.2 * A[i]
    if stop_mode == "zone" and zone is not None:
        stop = min(stop, zone["bot"] - 0.2 * A[i]) if d == 1 else max(stop, zone["top"] + 0.2 * A[i])
    if entry_mode == "confirm":
        # wait up to 3 candles for a close beyond the rejection candle's high (BUY) / low (SELL)
        j = None
        for k in range(i + 1, min(len(rows), i + 4)):
            if (d == 1 and rows[k][3] <= stop) or (d == -1 and rows[k][2] >= stop):
                return None                        # invalidated before confirming: no trade
            if (d == 1 and rows[k][4] > h) or (d == -1 and rows[k][4] < l):
                j = k
                break
        if j is None:
            return None
        i, c = j, rows[j][4]
    risk = abs(c - stop)
    tgt = c + d * rr * risk
    for k in range(i + 1, min(len(rows), i + 1 + 2 * per_hour)):
        _, _, hh, ll, _, _ = rows[k]
        if (d == 1 and ll <= stop) or (d == -1 and hh >= stop):
            return -1.0 - SPREAD / risk
        if (d == 1 and hh >= tgt) or (d == -1 and ll <= tgt):
            return rr - SPREAD / risk
    end = rows[min(len(rows) - 1, i + 2 * per_hour)][4]
    return d * (end - c) / risk - SPREAD / risk


def run(rows, per_hour, piv=2, use_sr=True, vol=1.3, wick=0.35, close_rule="half", use_bias=False,
        use_vwap=False, rr=1.5, cool=6, max_hits=3, life_h=48, start=0, end=None, entry_mode="close", stop_mode="wick"):
    end = len(rows) if end is None else end
    A = wilder_atr(rows)
    V = session_vwap(rows)
    vols = [r[5] for r in rows]
    zones, bias = hourly_zones(to_hourly(rows), piv, use_sr)
    life = life_h * per_hour
    zi = bi = 0
    cur_bias = 0
    live, out = [], []
    for i in range(20, end):
        t = rows[i][0]
        while zi < len(zones) and zones[zi]["ready"] <= t:
            live.append(dict(zones[zi], start=i, hits=0, last=-10 ** 9))
            zi += 1
        while bi < len(bias) and bias[bi][0] <= t:
            cur_bias = bias[bi][1]
            bi += 1
        if i < start:
            continue
        _, o, h, l, c, v = rows[i]
        rng = h - l
        avg = sum(vols[i - 20:i]) / 20
        ok_vol = avg > 0 and v >= vol * avg
        lw = (min(o, c) - l) / rng if rng > 0 else 0
        uw = (h - max(o, c)) / rng if rng > 0 else 0
        keep, fired = [], set()
        for z in live:
            if i - z["start"] > life or z["hits"] >= max_hits:
                continue
            if (z["dir"] == 1 and c < z["bot"] - 0.25 * z["atr1"]) or (z["dir"] == -1 and c > z["top"] + 0.25 * z["atr1"]):
                continue
            keep.append(z)
            d = z["dir"]
            if d in fired or i - z["last"] < cool or not ok_vol or rng <= 0:
                continue
            if use_bias and d != cur_bias:
                continue
            if use_vwap and ((d == 1 and c < V[i]) or (d == -1 and c > V[i])):
                continue
            mid = (z["top"] + z["bot"]) / 2
            edge = z["top"] if d == 1 else z["bot"]
            lvl = edge if close_rule == "outside" else mid
            if d == 1 and l <= z["top"] and c > lvl and c > o and lw >= wick:
                pass
            elif d == -1 and h >= z["bot"] and c < lvl and c < o and uw >= wick:
                pass
            else:
                continue
            r = scalp(rows, A, i, d, per_hour, rr, entry_mode, stop_mode, z)
            fired.add(d)
            z["hits"] += 1
            z["last"] = i
            if r is None:
                continue
            out.append(dict(i=i, t=t, dir=d, kind=z["kind"], r=r))
            continue
            z["hits"] += 1
            z["last"] = i
        live = keep
    return out


def run_nozone(rows, per_hour, piv=2, use_sr=True, vol=1.3, wick=0.35, close_rule="half", use_bias=False,
               use_vwap=False, rr=1.5, cool=6, entry_mode="close", **_):
    """Same rejection candle + filters, anywhere on the chart (cooldown per direction)."""
    A = wilder_atr(rows)
    V = session_vwap(rows)
    vols = [r[5] for r in rows]
    _, bias = hourly_zones(to_hourly(rows), piv, use_sr)
    bi, cur_bias, last = 0, 0, {1: -10 ** 9, -1: -10 ** 9}
    out = []
    for i in range(20, len(rows)):
        t, o, h, l, c, v = rows[i]
        while bi < len(bias) and bias[bi][0] <= t:
            cur_bias = bias[bi][1]
            bi += 1
        rng = h - l
        avg = sum(vols[i - 20:i]) / 20
        if rng <= 0 or avg <= 0 or v < vol * avg:
            continue
        for d in (1, -1):
            wk = (min(o, c) - l) / rng if d == 1 else (h - max(o, c)) / rng
            if wk < wick or (d == 1 and c <= o) or (d == -1 and c >= o) or i - last[d] < cool:
                continue
            if use_bias and d != cur_bias:
                continue
            if use_vwap and ((d == 1 and c < V[i]) or (d == -1 and c > V[i])):
                continue
            r = scalp(rows, A, i, d, per_hour, rr, entry_mode)
            last[d] = i
            if r is not None:
                out.append(dict(i=i, t=t, dir=d, kind="none", r=r))
    return out


def stats(xs, days):
    if not xs:
        return dict(n=0, perday=0, fail=float("nan"), avg=float("nan"), tot=0)
    rs = [x["r"] for x in xs]
    return dict(n=len(rs), perday=len(rs) / days, fail=100 * sum(r < 0 for r in rs) / len(rs),
                avg=sum(rs) / len(rs), tot=sum(rs))


def fmt(s):
    if s["n"] == 0:
        return "n=0"
    return f"n={s['n']:<4} {s['perday']:4.1f}/day  fail {s['fail']:5.1f}%  avg {s['avg']:+.2f}R  total {s['tot']:+6.1f}R"


def trading_days(rows, a=0, b=None):
    b = len(rows) if b is None else b
    return len({(r[0] - 22 * 3600) // 86400 for r in rows[a:b]})


SAMPLES = [("OANDA 5m", "oanda_xauusd_5m.csv", 12), ("COMEX 5m", "comex_gc1_5m.csv", 12), ("OANDA 15m", "oanda_xauusd_15m.csv", 4)]

GRID = dict(piv=[2, 3], use_sr=[True, False], vol=[1.0, 1.3, 1.8], wick=[0.35, 0.5],
            close_rule=["half", "outside"], use_bias=[False, True], use_vwap=[False, True], rr=[1.0, 1.5])

if __name__ == "__main__":
    oanda = load("oanda_xauusd_5m.csv")
    cut = int(len(oanda) * 0.6)
    dev_days = trading_days(oanda, 0, cut)
    keys = list(GRID)
    results = []
    for combo in itertools.product(*GRID.values()):
        cfg = dict(zip(keys, combo))
        s = stats(run(oanda, 12, end=cut, **cfg), dev_days)
        results.append((cfg, s))
    # selection rule (fixed in advance): at least 3 signals per day, then the best average R
    eligible = [x for x in results if x[1]["perday"] >= 3]
    eligible.sort(key=lambda x: x[1]["avg"], reverse=True)
    print(f"Development = first 60% of OANDA 5m ({dev_days} trading days). {len(results)} settings tested, "
          f"{len(eligible)} give >= 3 signals/day.\nTop 10 on development data:")
    for cfg, s in eligible[:10]:
        print("  ", fmt(s), cfg)
    best = eligible[0][0]
    print("\nCHOSEN:", best)
    print("\nUnchanged on data NOT used for the choice:")
    s = stats(run(oanda, 12, start=cut, **best), trading_days(oanda, cut))
    print(f"  OANDA 5m last 40%   {fmt(s)}")
    for label, f, ph in SAMPLES[1:]:
        rows = load(f)
        print(f"  {label:<18}  {fmt(stats(run(rows, ph, **best), trading_days(rows)))}")
    print("\nTrigger variants (chosen zone/candle settings unchanged, all data):")
    for em, sm in (("close", "wick"), ("confirm", "wick"), ("close", "zone"), ("confirm", "zone")):
        line = f"  entry={em:<8} stop={sm:<5}"
        for label, f, ph in SAMPLES:
            rows = load(f)
            st = stats(run(rows, ph, entry_mode=em, stop_mode=sm, **best), trading_days(rows))
            line += f" | {label}: n={st['n']} {st['perday']:.1f}/d fail {st['fail']:.0f}% avg {st['avg']:+.2f}R"
        print(line)
    print("\nSame candle rules and filters but NO zone required (does the zone add anything?):")
    for label, f, ph in SAMPLES:
        rows = load(f)
        print(f"  {label:<18}  {fmt(stats(run_nozone(rows, ph, **best), trading_days(rows)))}")
