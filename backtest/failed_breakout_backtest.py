"""
Failed-breakout (sweep & reclaim) test at 1H high-volume rejection zones.

Rules were fixed BEFORE looking at results:
  Zone      : 1H candle volume >= 2x 20-bar avg, wick >= 40% of range; zone = the wick.
  Breakout  : first close beyond the far side of the zone by 0.3 x 1H ATR (as breakout_backtest.py).
  Failure   : within `win_h` hours after the breakout, a candle closes back beyond the zone's
              ORIGINAL side (price was above a zone, broke below it, then closes back above the
              zone top -> LONG; mirror for SHORT).
  Entry     : close of the reclaim candle.
  Stop      : beyond the extreme of the failed breakout (lowest low / highest high since the break)
              + 0.3 x entry-timeframe ATR.
  Target    : rr x risk, spread 0.30 $, stop first if both hit in one candle, time exit 16 hours.
  Controls  : identical rules on 3 random zones per real zone (shifted 1-3 1H ATR).
  Dedupe    : one signal per candle per direction (overlapping zones = one trade).
  Pass bar  : positive on BOTH feeds (OANDA, COMEX), in BOTH halves of the 10 months, and better
              than the random-zone version.

Usage: python3 failed_breakout_backtest.py > failed_breakout_results.txt
"""
import os
import random

from breakout_backtest import fmt, stats
from volume_zones_backtest import CFG, atr, generate, load

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
SPREAD = 0.30


def run(eb, hb, rr=2.0, win_h=6, brk=0.3, per_hour=1, seed=21):
    A1, AE = atr(hb), atr(eb)
    zones = [z for z in generate(hb, A1, dict(CFG, vol_k=2.0, wick=0.4)) if z[3] == "REJ"]
    idx = {b[0]: i for i, b in enumerate(eb)}
    rnd = random.Random(seed)
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
            side, brk_at, d = 0, None, 0
            for j in range(i0, min(len(eb), i0 + 24 * 15 * per_hour)):
                c, pc = eb[j][4], eb[j - 1][4]
                if side == 0:
                    side = 1 if pc > tp else -1 if pc < bt else 0
                if side == 1 and c < bt - brk * a:
                    brk_at, d = j, 1          # broke DOWN; a reclaim would be a LONG
                    break
                if side == -1 and c > tp + brk * a:
                    brk_at, d = j, -1         # broke UP; a reclaim would be a SHORT
                    break
                if c > tp:
                    side = 1
                elif c < bt:
                    side = -1
            if brk_at is None:
                continue
            sig = None
            ext = eb[brk_at][3] if d == 1 else eb[brk_at][2]
            for j in range(brk_at + 1, min(len(eb), brk_at + 1 + win_h * per_hour)):
                _, o, h, l, c, _ = eb[j]
                ext = min(ext, l) if d == 1 else max(ext, h)
                if (d == 1 and c > tp) or (d == -1 and c < bt):
                    sig = j
                    break
            if sig is None:
                continue
            j = sig
            entry = eb[j][4]
            stop = ext - 0.3 * AE[j] if d == 1 else ext + 0.3 * AE[j]
            risk = abs(entry - stop)
            if risk <= 0:
                continue
            tgt = entry + d * rr * risk
            r = None
            for k in range(j + 1, min(len(eb), j + 1 + 16 * per_hour)):
                _, _, hh, ll, _, _ = eb[k]
                if (d == 1 and ll <= stop) or (d == -1 and hh >= stop):
                    r = -1.0
                    break
                if (d == 1 and hh >= tgt) or (d == -1 and ll <= tgt):
                    r = rr
                    break
            if r is None:
                r = d * (eb[min(len(eb) - 1, j + 16 * per_hour)][4] - entry) / risk
            out.append(dict(ctl=ctl, r=r - SPREAD / risk, risk=risk, time=eb[j][0], dir=d,
                            entry=entry, stop=stop, tgt=tgt))
    # one signal per candle per direction (overlapping zones reclaimed on the same candle = one trade)
    seen, uniq = set(), []
    for t in out:
        key = (t["ctl"], t["time"], t["dir"])
        if key not in seen:
            seen.add(key)
            uniq.append(t)
    return uniq


SAMPLES = [
    ("H1 OANDA 1H (10 months)", "xauusd_1h.csv", "xauusd_1h.csv", 1),
    ("H2 COMEX GC1! 1H (10 months)", "gc1_1h.csv", "gc1_1h.csv", 1),
    ("B  OANDA 15m entries (2.5 months)", "xauusd_15m.csv", "xauusd_1h.csv", 4),
    ("A  OANDA 5m entries (4 weeks)", "xauusd_5m.csv", "xauusd_1h.csv", 12),
    ("C  COMEX GC1! 5m entries (4 weeks)", "gc1_5m.csv", "gc1_1h.csv", 12),
]

def export_trades(path):
    """Every OANDA 1H signal with the indicator defaults (2R), for review."""
    import csv
    import datetime as dt
    eb = load(os.path.join(D, "xauusd_1h.csv"))
    tr = [t for t in run(eb, eb, rr=2.0, per_hour=1) if not t["ctl"]]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "signal", "entry", "stop", "target", "risk_$", "result_R"])
        for t in sorted(tr, key=lambda x: x["time"]):
            w.writerow([dt.datetime.utcfromtimestamp(t["time"]).strftime("%Y-%m-%d %H:%M"),
                        "BUY" if t["dir"] == 1 else "SELL", round(t["entry"], 2), round(t["stop"], 2),
                        round(t["tgt"], 2), round(t["risk"], 2), round(t["r"], 2)])
    return tr


if __name__ == "__main__":
    export_trades(os.path.join(HERE, "failed_breakout_trades_oanda_1h.csv"))
    for label, ef, hf, ph in SAMPLES:
        eb, hb = load(os.path.join(D, ef)), load(os.path.join(D, hf))
        print(f"\n==================== {label}")
        for rr in (1.0, 1.5, 2.0):
            tr = run(eb, hb, rr=rr, per_hour=ph)
            R = [t for t in tr if not t["ctl"]]
            C = [t for t in tr if t["ctl"]]
            print(f"  {rr}R  real   {fmt(stats(R))}")
            print(f"        random {fmt(stats(C))}")
            if R:
                half = sorted(t["time"] for t in R)[len(R) // 2]
                print(f"        1st half {fmt(stats([t for t in R if t['time'] < half]))}")
                print(f"        2nd half {fmt(stats([t for t in R if t['time'] >= half]))}")
                print(f"        longs    {fmt(stats([t for t in R if t['dir'] == 1]))}")
                print(f"        shorts   {fmt(stats([t for t in R if t['dir'] == -1]))}")
