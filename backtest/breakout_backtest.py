"""
Breakout-continuation test for the 1H high-volume rejection zones.

Idea: the bounce entries lost money and did worse than random zones, so maybe price tends to
push THROUGH these zones. Here we trade the break instead of the bounce.

1H zone   : 1H candle volume >= 2x 20-bar avg, wick >= 40% of range; zone = the wick.
Breakout  : the first entry-timeframe candle that CLOSES beyond the far side of the zone by
            `brk` x 1H ATR (price was above the zone -> closes below it = SHORT, and vice versa).
            Only the first break of each zone, within 15 days.
Entry     : close of the breakout candle.
Stop      : "zone"   = back on the other side of the zone (+0.3 x 1H ATR)
            "candle" = beyond the breakout candle's extreme (+0.3 x entry-TF ATR)
Target    : rr x risk.  Spread 0.30 $ per trade.  Stop first if both hit in one candle.
            Time exit after 16 hours.
Controls  : the same rules on 3 random zones per real zone (same size, shifted 1-3 1H ATR).

Samples   : H1  OANDA 1H zones, 1H entries, 10 months
            H2  COMEX GC1! 1H zones, 1H entries, 10 months
            B   OANDA 15m entries (2.5 months)
            A   OANDA 5m entries (4 weeks)
            C   COMEX GC1! 5m entries (4 weeks)

Usage: python3 breakout_backtest.py > breakout_results.txt
"""
import datetime as dt
import os
import random

from volume_zones_backtest import CFG, atr, generate, load

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
SPREAD = 0.30


def run(eb, hb, rr=2.0, stop_mode="candle", brk=0.3, per_hour=1, seed=9):
    A1, AE = atr(hb), atr(eb)
    zones = [z for z in generate(hb, A1, dict(CFG, vol_k=2.0, wick=0.4)) if z[3] == "REJ"]
    idx = {b[0]: i for i, b in enumerate(eb)}
    rnd = random.Random(seed)
    max_bars = 16 * per_hour
    out = []
    for (hi, top, bot, _, _) in zones:
        t_ready = hb[hi][0] + 3600
        if t_ready not in idx:
            continue
        a = A1[hi]
        cands = [(top, bot, False)]
        for _ in range(3):
            off = rnd.choice((-1, 1)) * rnd.uniform(1, 3) * a
            cands.append((top + off, bot + off, True))
        for (tp, bt, ctl) in cands:
            i0 = idx[t_ready]
            side, sig = 0, None
            for j in range(i0, min(len(eb), i0 + 24 * 15 * per_hour)):
                c = eb[j][4]
                pc = eb[j - 1][4]
                if side == 0:
                    side = 1 if pc > tp else -1 if pc < bt else 0
                if side == 1 and c < bt - brk * a:
                    sig = (j, -1)
                    break
                if side == -1 and c > tp + brk * a:
                    sig = (j, 1)
                    break
                if c > tp:
                    side = 1
                elif c < bt:
                    side = -1
            if not sig:
                continue
            j, d = sig
            _, o, h, l, c, _ = eb[j]
            entry = c
            if stop_mode == "zone":
                stop = bt - 0.3 * a if d == 1 else tp + 0.3 * a
            else:
                stop = l - 0.3 * AE[j] if d == 1 else h + 0.3 * AE[j]
            risk = abs(entry - stop)
            if risk <= 0:
                continue
            tgt = entry + d * rr * risk
            r = None
            for k in range(j + 1, min(len(eb), j + 1 + max_bars)):
                _, _, hh, ll, _, _ = eb[k]
                if (d == 1 and ll <= stop) or (d == -1 and hh >= stop):
                    r = -1.0
                    break
                if (d == 1 and hh >= tgt) or (d == -1 and ll <= tgt):
                    r = rr
                    break
            if r is None:
                r = d * (eb[min(len(eb) - 1, j + max_bars)][4] - entry) / risk
            out.append(dict(ctl=ctl, r=r - SPREAD / risk, risk=risk, time=eb[j][0], dir=d))
    return out


def stats(xs):
    if not xs:
        return None
    rs = [t["r"] for t in sorted(xs, key=lambda t: t["time"])]
    eq = peak = dd = 0.0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    gl = -sum(r for r in rs if r < 0)
    return dict(n=len(rs), win=100 * sum(r > 0 for r in rs) / len(rs), avg=sum(rs) / len(rs),
                tot=sum(rs), pf=sum(r for r in rs if r > 0) / gl if gl else float("inf"), dd=dd)


def fmt(st):
    if not st:
        return "n=0"
    return (f"n={st['n']:<4} win {st['win']:5.1f}%  avg {st['avg']:+.2f}R  total {st['tot']:+6.1f}R  "
            f"PF {st['pf']:4.2f}  maxDD {st['dd']:4.1f}R")


SAMPLES = [
    ("H1 OANDA 1H entries (10 months)", "xauusd_1h.csv", "xauusd_1h.csv", 1),
    ("H2 COMEX GC1! 1H entries (10 months)", "gc1_1h.csv", "gc1_1h.csv", 1),
    ("B  OANDA 15m entries (2.5 months)", "xauusd_15m.csv", "xauusd_1h.csv", 4),
    ("A  OANDA 5m entries (4 weeks)", "xauusd_5m.csv", "xauusd_1h.csv", 12),
    ("C  COMEX GC1! 5m entries (4 weeks)", "gc1_5m.csv", "gc1_1h.csv", 12),
]

if __name__ == "__main__":
    for label, ef, hf, ph in SAMPLES:
        eb, hb = load(os.path.join(D, ef)), load(os.path.join(D, hf))
        print(f"\n==================== {label}")
        for stop_mode in ("candle", "zone"):
            for rr in (1.0, 1.5, 2.0):
                tr = run(eb, hb, rr=rr, stop_mode=stop_mode, per_hour=ph)
                R = [t for t in tr if not t["ctl"]]
                C = [t for t in tr if t["ctl"]]
                print(f"  stop={stop_mode:<6} {rr}R  real   {fmt(stats(R))}")
                print(f"  {'':<16}random {fmt(stats(C))}")
                if label.startswith("H") and (stop_mode, rr) == ("candle", 2.0):
                    half = sorted(t["time"] for t in R)[len(R) // 2] if R else 0
                    print(f"  {'':<16}1st half {fmt(stats([t for t in R if t['time'] < half]))}")
                    print(f"  {'':<16}2nd half {fmt(stats([t for t in R if t['time'] >= half]))}")
                    print(f"  {'':<16}longs    {fmt(stats([t for t in R if t['dir'] == 1]))}")
                    print(f"  {'':<16}shorts   {fmt(stats([t for t in R if t['dir'] == -1]))}")
