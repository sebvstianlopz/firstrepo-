"""
5m entry signals inside fresh 1H high-volume rejection zones (mirrors xauusd_hv_zones_5m.pine).

1H zone : 1H candle volume >= 2x 20-bar avg and wick >= 40% of range; zone = the wick.
Arming  : first retest of the fresh zone on 5m (price enters from outside).
Triggers within `sig_win` 5m bars after arming (each trigger at most once per zone, scored separately):
  REJ  5m candle trades into the zone and closes back outside it, in the bounce direction
       (long: low <= top, close > top, close > open).
  BOS  5m close breaks the most recent 5m swing high (long) / swing low (short), pivot 2/2.
Trade   : entry = signal close, stop = "zone": zone far side -/+ 0.3 x 1H ATR
          or "swing": beyond the extreme since arming -/+ 0.3 x 5m ATR; target = rr x risk,
          spread 0.30 $, stop first if both hit in one candle, time exit after `max_bars`.
Controls: the same rules on random 1H zones shifted 1-3 1H ATR.

NOTE: the 5m data covers ~4 weeks, so only a handful of 1H zones can be tested.
This checks the logic; it is NOT enough data to prove an edge.
"""
import os
import random

from volume_zones_backtest import CFG, atr, generate, load

HERE = os.path.dirname(os.path.abspath(__file__))
SPREAD = 0.30


def pivots(bars, left=2, right=2):
    """Pivot highs / lows keyed by the bar index at which they are CONFIRMED."""
    ph, pl = {}, {}
    for i in range(left + right, len(bars)):
        p = i - right
        hs = [bars[k][2] for k in range(p - left, i + 1)]
        ls = [bars[k][3] for k in range(p - left, i + 1)]
        if bars[p][2] == max(hs) and hs.count(bars[p][2]) == 1:
            ph[i] = bars[p][2]
        if bars[p][3] == min(ls) and ls.count(bars[p][3]) == 1:
            pl[i] = bars[p][3]
    return ph, pl


_A5 = {}


def atr5_cache(m5):
    if id(m5) not in _A5:
        _A5[id(m5)] = atr(m5)
    return _A5[id(m5)]


def run(m5, h1, rr=2.0, sig_win=24, max_chase=1.0, brk=0.3, max_bars=192, seed=3, stop_mode="zone"):
    A1 = atr(h1)
    cfg = dict(CFG, vol_k=2.0, wick=0.4)
    zones = [z for z in generate(h1, A1, cfg) if z[3] == "REJ"]
    ph, pl = pivots(m5)
    idx = {b[0]: i for i, b in enumerate(m5)}
    rnd = random.Random(seed)
    trades = []
    for (hi, top, bot, _, vr) in zones:
        t_ready = h1[hi][0] + 3600
        if t_ready not in idx:
            continue
        a = A1[hi]
        cands = [(top, bot, False)]
        for _ in range(3):
            off = rnd.choice((-1, 1)) * rnd.uniform(1, 3) * a
            cands.append((top + off, bot + off, True))
        for (tp, bt, ctl) in cands:
            i0 = idx[t_ready]
            side, arm, d = 0, None, 0
            for j in range(i0, min(len(m5), i0 + 288 * 15)):
                pc = m5[j - 1][4]
                if side == 0:
                    side = 1 if pc > tp else -1 if pc < bt else 0
                if side == 1 and m5[j][3] <= tp:
                    arm, d = j, 1
                    break
                if side == -1 and m5[j][2] >= bt:
                    arm, d = j, -1
                    break
                c = m5[j][4]
                if (side == 1 and c < bt - brk * a) or (side == -1 and c > tp + brk * a):
                    break
            if arm is None:
                continue
            # most recent confirmed swing before arming
            bos = None
            src = ph if d == 1 else pl
            for k in range(arm, max(0, arm - 300), -1):
                if k in src:
                    bos = src[k]
                    break
            A5 = atr5_cache(m5)
            fired = {}
            for j in range(arm, min(len(m5), arm + sig_win + 1)):
                _, o, h, l, c, _ = m5[j]
                if j in src and j > arm:
                    bos = src[j]
                if (d == 1 and c < bt - brk * a) or (d == -1 and c > tp + brk * a):
                    break
                chase_ok = (c - tp) <= max_chase * a if d == 1 else (bt - c) <= max_chase * a
                if not chase_ok:
                    continue
                if d == 1:
                    rej = l <= tp and c > tp and c > o
                    bs = bos is not None and c > bos and m5[j - 1][4] <= bos
                else:
                    rej = h >= bt and c < bt and c < o
                    bs = bos is not None and c < bos and m5[j - 1][4] >= bos
                if rej and "REJ" not in fired:
                    fired["REJ"] = j
                if bs and "BOS" not in fired:
                    fired["BOS"] = j
            for kind, j in fired.items():
                entry = m5[j][4]
                if stop_mode == "zone":
                    stop = bt - brk * a if d == 1 else tp + brk * a
                else:   # beyond the lowest low / highest high since arming + 0.3 x 5m ATR
                    lo = min(b[3] for b in m5[arm:j + 1])
                    hi = max(b[2] for b in m5[arm:j + 1])
                    stop = lo - 0.3 * A5[j] if d == 1 else hi + 0.3 * A5[j]
                risk = abs(entry - stop)
                if risk <= 0:
                    continue
                tgt = entry + d * rr * risk
                r = None
                for k in range(j + 1, min(len(m5), j + 1 + max_bars)):
                    _, _, h, l, _, _ = m5[k]
                    if (d == 1 and l <= stop) or (d == -1 and h >= stop):
                        r = -1.0
                        break
                    if (d == 1 and h >= tgt) or (d == -1 and l <= tgt):
                        r = rr
                        break
                if r is None:
                    r = d * (m5[min(len(m5) - 1, j + max_bars)][4] - entry) / risk
                trades.append(dict(kind=kind, ctl=ctl, r=r - SPREAD / risk, risk=risk, bar=j))
    return trades


if __name__ == "__main__":
    m5 = load(os.path.join(HERE, "..", "data", "xauusd_5m.csv"))
    h1 = load(os.path.join(HERE, "..", "data", "xauusd_1h.csv"))
    for stop_mode in ("zone", "swing"):
        for rr in (1.0, 2.0):
            tr = run(m5, h1, rr=rr, stop_mode=stop_mode)
            print(f"\nStop: {stop_mode}   Target {rr:.0f}R")
            for kind in ("REJ", "BOS"):
                for ctl in (False, True):
                    xs = [t for t in tr if t["ctl"] == ctl and t["kind"] == kind]
                    if not xs:
                        print(f"  {kind:<4}{'random' if ctl else 'real':<7} n=0")
                        continue
                    w = 100 * sum(t["r"] > 0 for t in xs) / len(xs)
                    print(f"  {kind:<4}{'random' if ctl else 'real':<7} n={len(xs):<3} win {w:5.1f}%  "
                          f"avg {sum(t['r'] for t in xs) / len(xs):+.2f}R  total {sum(t['r'] for t in xs):+.1f}R  "
                          f"avg risk ${sum(t['risk'] for t in xs) / len(xs):.2f}")
