"""
Backtest for the "XAUUSD Reaction Zones" Pine Script indicator.

Mirrors the indicator logic in pure Python (no dependencies) so the zone
sources can be measured on real XAUUSD data (OANDA feed, CSVs in ../data).

Reaction test (same as the indicator's built-in stats table):
  * A zone is TOUCHED when price enters it from outside
    (prev close above zone and low <= top  -> support test,
     prev close below zone and high >= bottom -> resistance test).
  * REACTION = price moves `react_atr` x ATR away from the zone edge
    (in the bounce direction) within `look` bars, BEFORE a candle closes
    `break_atr` x ATR through the far side of the zone.
  * Otherwise the touch is a FAIL (broke through or timed out).

Edge check: every real zone gets a CONTROL zone of identical width/age,
shifted randomly by 1-3 ATR. Controls are tested with exactly the same rules.
If a zone type does not react more often than its random controls it has no
real edge, no matter how "nice" its hit rate looks.

Usage:  python3 reaction_zones_backtest.py > results.txt
"""
import csv
import datetime as dt
import os
import random
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
NY = ZoneInfo("America/New_York")


def load(name):
    rows = []
    with open(os.path.join(DATA, name)) as f:
        for r in csv.DictReader(f):
            rows.append((int(r["time"]), float(r["open"]), float(r["high"]),
                         float(r["low"]), float(r["close"])))
    return rows


def atr(bars, n=14):
    out, prev = [], None
    for i, (_, o, h, l, c) in enumerate(bars):
        tr = h - l if i == 0 else max(h - l, abs(h - bars[i - 1][4]), abs(l - bars[i - 1][4]))
        prev = tr if prev is None else (prev * (n - 1) + tr) / n
        out.append(prev)
    return out


def trading_day(t):
    # Gold's trading day rolls at 17:00 New York -> shift +7h and take the date
    return (dt.datetime.fromtimestamp(t, NY) + dt.timedelta(hours=7)).date()


def resample(bars, secs):
    out = []
    for b in bars:
        k = b[0] - b[0] % secs
        if out and out[-1][0] == k:
            t, o, h, l, c = out[-1]
            out[-1] = (t, o, max(h, b[2]), min(l, b[3]), b[4])
        else:
            out.append((k, b[1], b[2], b[3], b[4]))
    return out


class Zone:
    __slots__ = ("top", "bot", "kind", "born", "breaks", "pending", "pdir",
                 "pbar", "patr", "dead", "control", "conf",
                 "away", "touches", "feat")

    def __init__(self, top, bot, kind, born, control=False):
        self.top, self.bot, self.kind, self.born = top, bot, kind, born
        self.breaks, self.pending, self.dead, self.control = 0, False, False, control
        self.conf = 1
        self.away, self.touches, self.feat = 0.0, 0, {}
        self.pdir = self.pbar = 0
        self.patr = 0.0


def size_zone(ext, body, a, is_high, min_w, max_w):
    """Zone from the wick extreme toward the body, clamped to [min_w, max_w] ATR."""
    if is_high:
        top = ext
        bot = max(body, top - max_w * a)
        bot = min(bot, top - min_w * a)
        return top, bot
    bot = ext
    top = min(body, bot + max_w * a)
    top = max(top, bot + min_w * a)
    return top, bot


def run(bars, cfg, htf_bars=None, seed=7):
    rnd = random.Random(seed)
    A = atr(bars)
    n = len(bars)
    L, R = cfg["piv_left"], cfg["piv_right"]
    lvl_w = cfg["level_w"]
    zones = []
    stats = {}          # kind -> [touches, reactions]
    ctrl = {}           # kind -> [touches, reactions]
    conf_stats = {}     # confluence bucket -> [touches, reactions]
    events = []

    def add(top, bot, kind, i):
        zones.append(Zone(top, bot, kind, i))
        off = rnd.choice((-1, 1)) * rnd.uniform(1.0, 3.0) * A[i]
        zones.append(Zone(top + off, bot + off, kind, i, control=True))

    # ---- HTF pivots (known at close of the HTF bar that confirms them)
    htf_events = {}
    if htf_bars:
        HA = atr(htf_bars)
        hsec = htf_bars[1][0] - htf_bars[0][0]
        hl, hr = cfg["htf_left"], cfg["htf_right"]
        for j in range(hl + hr, len(htf_bars)):
            p = j - hr
            win = htf_bars[p - hl:j + 1]
            t_ready = htf_bars[j][0] + hsec           # after the HTF bar closes
            o, h, l, c = htf_bars[p][1:]
            if h == max(b[2] for b in win) and h > max(b[2] for b in win if b is not htf_bars[p]):
                htf_events.setdefault(t_ready, []).append(
                    ("HTF Pivot",) + size_zone(h, max(o, c), HA[j], True, 0.10, 0.35))
            if l == min(b[3] for b in win) and l < min(b[3] for b in win if b is not htf_bars[p]):
                htf_events.setdefault(t_ready, []).append(
                    ("HTF Pivot",) + size_zone(l, min(o, c), HA[j], False, 0.10, 0.35))

    day_h = day_l = None
    wk_h = wk_l = None
    sess = {}
    rn_step = cfg["round_step"]
    rn_seen = set()

    for i in range(n):
        t, o, h, l, c = bars[i]
        a = A[i]

        # ---------------- 1) evaluate pending reactions / breaks / touches
        if i > 0:
            pc = bars[i - 1][4]
            for z in zones:
                if z.dead:
                    continue
                if z.pending:
                    ra, ba = z.patr * cfg["react_atr"], z.patr * cfg["break_atr"]
                    res = None
                    if z.pdir == 1:
                        if c < z.bot - ba:
                            res = 0
                        elif h >= z.top + ra:
                            res = 1
                    else:
                        if c > z.top + ba:
                            res = 0
                        elif l <= z.bot - ra:
                            res = 1
                    if res is None and i - z.pbar >= cfg["look"]:
                        res = 0
                    if res is not None:
                        z.pending = False
                        d = ctrl if z.control else stats
                        d.setdefault(z.kind, [0, 0])
                        d[z.kind][0] += 1
                        d[z.kind][1] += res
                        if not z.control:
                            b = min(z.conf, 3)
                            conf_stats.setdefault(b, [0, 0])
                            conf_stats[b][0] += 1
                            conf_stats[b][1] += res
                        f = dict(z.feat)
                        f.update(kind=z.kind, control=z.control, res=res, bar=z.pbar)
                        events.append(f)
                        z.away = 0.0
                        z.touches += 1
                        if res == 0:
                            z.breaks += 1
                    continue
                # fresh touch
                if pc > z.top and l <= z.top:
                    z.pending, z.pdir = True, 1
                elif pc < z.bot and h >= z.bot:
                    z.pending, z.pdir = True, -1
                if z.pending:
                    z.pbar, z.patr = i, a
                    kinds = {y.kind for y in zones if not y.dead and y.control == z.control
                             and y is not z and y.bot <= z.top and y.top >= z.bot}
                    kinds.discard(z.kind)
                    z.conf = 1 + len(kinds)
                    rej = (c > z.top) if z.pdir == 1 else (c < z.bot)
                    pen = ((z.top - l) if z.pdir == 1 else (h - z.bot)) / (z.top - z.bot)
                    z.feat = dict(first=z.touches == 0, flipped=z.breaks > 0, conf=z.conf,
                                  away=z.away, rej=rej, pen=pen,
                                  hour=dt.datetime.fromtimestamp(t, dt.timezone.utc).hour,
                                  age=i - z.born, dir=z.pdir,
                                  top=z.top, bot=z.bot, atr=a)
                else:
                    # track how far price travelled away from the zone since last test
                    if c > z.top:
                        z.away = max(z.away, (h - z.top) / a)
                    elif c < z.bot:
                        z.away = max(z.away, (z.bot - l) / a)
            for z in zones:
                if not z.dead and not z.pending and (
                        z.breaks >= cfg["max_breaks"] or i - z.born > cfg["max_age"]):
                    z.dead = True
            zones = [z for z in zones if not z.dead]

        if i < 20:
            continue

        # ---------------- 2) create new zones (known at close of bar i)
        src = cfg["sources"]
        # swing pivots
        if "Pivot" in src and i >= L + R:
            p = i - R
            hs = [bars[k][2] for k in range(p - L, i + 1)]
            ls = [bars[k][3] for k in range(p - L, i + 1)]
            _, po, ph, pl, pcl = bars[p]
            if ph == max(hs) and hs.count(ph) == 1:
                add(*size_zone(ph, max(po, pcl), a, True, 0.10, cfg["piv_max_w"]), "Pivot", i)
            if pl == min(ls) and ls.count(pl) == 1:
                add(*size_zone(pl, min(po, pcl), a, False, 0.10, cfg["piv_max_w"]), "Pivot", i)
        # order blocks (last opposite candle before a displacement candle that breaks structure)
        if "Order Block" in src:
            body = c - o
            if body >= cfg["ob_disp"] * a and c > max(bars[k][2] for k in range(i - 5, i)):
                for k in range(i - 1, i - 6, -1):
                    if bars[k][4] < bars[k][1]:
                        add(bars[k][1], bars[k][3], "Order Block", i) if bars[k][1] - bars[k][3] <= 1.5 * a \
                            else add(bars[k][3] + 1.5 * a, bars[k][3], "Order Block", i)
                        break
            if -body >= cfg["ob_disp"] * a and c < min(bars[k][3] for k in range(i - 5, i)):
                for k in range(i - 1, i - 6, -1):
                    if bars[k][4] > bars[k][1]:
                        add(bars[k][2], bars[k][1], "Order Block", i) if bars[k][2] - bars[k][1] <= 1.5 * a \
                            else add(bars[k][2], bars[k][2] - 1.5 * a, "Order Block", i)
                        break
        # fair value gaps
        if "FVG" in src:
            if l - bars[i - 2][2] >= cfg["fvg_min"] * a:
                add(l, bars[i - 2][2], "FVG", i)
            if bars[i - 2][3] - h >= cfg["fvg_min"] * a:
                add(bars[i - 2][3], h, "FVG", i)
        # previous day / week high-low
        d = trading_day(t)
        if i > 0 and trading_day(bars[i - 1][0]) != d:
            # a new day started on this bar -> previous day's H/L become levels
            if day_h is not None and "PDH/PDL" in src:
                add(day_h + lvl_w * a, day_h - lvl_w * a, "PDH/PDL", i)
                add(day_l + lvl_w * a, day_l - lvl_w * a, "PDH/PDL", i)
            day_h, day_l = h, l
            wk = d.isocalendar()[:2]
            if wk != trading_day(bars[i - 1][0]).isocalendar()[:2]:
                if wk_h is not None and "PWH/PWL" in src:
                    add(wk_h + lvl_w * a, wk_h - lvl_w * a, "PWH/PWL", i)
                    add(wk_l + lvl_w * a, wk_l - lvl_w * a, "PWH/PWL", i)
                wk_h, wk_l = h, l
            else:
                wk_h, wk_l = max(wk_h or h, h), min(wk_l or l, l)
        else:
            day_h = h if day_h is None else max(day_h, h)
            day_l = l if day_l is None else min(day_l, l)
            wk_h = h if wk_h is None else max(wk_h, h)
            wk_l = l if wk_l is None else min(wk_l, l)
        # session highs/lows (UTC): Asia 00-07, London 07-12, New York 12-20
        if "Session H/L" in src:
            hr_utc = dt.datetime.fromtimestamp(t, dt.timezone.utc).hour
            name = "Asia" if hr_utc < 7 else "London" if hr_utc < 12 else "NY" if hr_utc < 20 else None
            for s in list(sess):
                if s != name:
                    sh, sl = sess.pop(s)
                    add(sh + lvl_w * a, sh - lvl_w * a, "Session H/L", i)
                    add(sl + lvl_w * a, sl - lvl_w * a, "Session H/L", i)
            if name:
                sh, sl = sess.get(name, (h, l))
                sess[name] = (max(sh, h), min(sl, l))
        # round numbers
        if "Round #" in src:
            base = round(c / rn_step) * rn_step
            for k in (-2, -1, 0, 1, 2):
                lv = base + k * rn_step
                if lv not in rn_seen:
                    rn_seen.add(lv)
                    add(lv + lvl_w * a, lv - lvl_w * a, "Round #", i)
            if len(rn_seen) > 200:
                rn_seen = {x for x in rn_seen if abs(x - c) < 5 * rn_step}
                live = {round((z.top + z.bot) / 2, 6) for z in zones if z.kind == "Round #" and not z.control}
                rn_seen |= {x for x in rn_seen if x in live}
        # HTF pivots
        if "HTF Pivot" in src:
            for (kind, top, bot) in htf_events.get(t, ()):
                add(top, bot, kind, i)

        # cap zone count (oldest first), same as the indicator
        real = [z for z in zones if not z.control]
        if len(real) > cfg["max_zones"]:
            oldest = [z for z in real if not z.pending][:len(real) - cfg["max_zones"]]
            kill = set(map(id, oldest))
            zones = [z for z in zones if id(z) not in kill]

    return stats, ctrl, conf_stats, events


def simulate_trades(bars, events, rr=1.0, stop_buf=0.3, max_bars=48, only=None):
    """Enter at the close of a rejection candle, stop beyond the zone (+buffer),
    target = rr x risk. Returns list of R results (per trade)."""
    out = []
    for e in events:
        if not e["rej"] or (only and not only(e)):
            continue
        i = e["bar"]
        entry = bars[i][4]
        if e["dir"] == 1:
            stop = e["bot"] - stop_buf * e["atr"]
            risk = entry - stop
        else:
            stop = e["top"] + stop_buf * e["atr"]
            risk = stop - entry
        if risk <= 0:
            continue
        tgt = entry + e["dir"] * rr * risk
        r = None
        for k in range(i + 1, min(i + 1 + max_bars, len(bars))):
            _, o, h, l, c = bars[k]
            hit_stop = l <= stop if e["dir"] == 1 else h >= stop
            hit_tgt = h >= tgt if e["dir"] == 1 else l <= tgt
            if hit_stop:          # conservative: stop first if both in one bar
                r = -1.0
                break
            if hit_tgt:
                r = rr
                break
        if r is None:             # time exit
            c = bars[min(i + max_bars, len(bars) - 1)][4]
            r = e["dir"] * (c - entry) / risk
        out.append((e["control"], e["kind"], r))
    return out


def report(title, stats, ctrl, conf, bars_count):
    print(f"\n=== {title} ({bars_count} bars) ===")
    print(f"{'Zone type':<14}{'touches':>8}{'react%':>8}{'random%':>9}{'edge':>7}")
    tt = tr = ct = cr = 0
    for k in sorted(stats):
        t, r = stats[k]
        c_t, c_r = ctrl.get(k, [0, 0])
        tt, tr, ct, cr = tt + t, tr + r, ct + c_t, cr + c_r
        rp = 100 * r / t if t else 0
        cp = 100 * c_r / c_t if c_t else 0
        print(f"{k:<14}{t:>8}{rp:>7.1f}%{cp:>8.1f}%{rp - cp:>+6.1f}")
    rp, cp = 100 * tr / max(tt, 1), 100 * cr / max(ct, 1)
    print(f"{'ALL':<14}{tt:>8}{rp:>7.1f}%{cp:>8.1f}%{rp - cp:>+6.1f}")
    print("Confluence (distinct zone types overlapping at touch):")
    for b in sorted(conf):
        t, r = conf[b]
        print(f"  {'3+' if b == 3 else b:>2} types: {t:>6} touches  react {100 * r / t:5.1f}%")
    return {k: stats[k] for k in stats}


BASE = dict(piv_left=10, piv_right=5, piv_max_w=0.5, htf_left=5, htf_right=3,
            ob_disp=1.5, fvg_min=0.3, level_w=0.10, round_step=25.0,
            react_atr=1.0, break_atr=0.3, look=12, max_breaks=2,
            max_zones=150,
            sources={"Pivot", "Order Block", "FVG", "PDH/PDL", "PWH/PWL",
                     "Session H/L", "Round #", "HTF Pivot"})

def trade_report(bars, events):
    for rr in (1.0, 2.0):
        tr = simulate_trades(bars, events, rr=rr)
        print(f"Rejection-candle trades, target {rr:.0f}R "
              f"(entry = rejection close, stop = beyond zone + 0.3 ATR, spread NOT included):")
        print(f"  {'Zone type':<14}{'real n':>7}{'win%':>7}{'avgR':>8}   {'rand n':>7}{'win%':>7}{'avgR':>8}")
        for k in sorted({x[1] for x in tr}) + ["ALL"]:
            row = []
            for ctl in (False, True):
                xs = [r for c, kk, r in tr if c == ctl and (k == "ALL" or kk == k)]
                w = 100 * sum(1 for r in xs if r > 0) / len(xs) if xs else 0
                row += [len(xs), w, sum(xs) / len(xs) if xs else 0]
            print(f"  {k:<14}{row[0]:>7}{row[1]:>6.1f}%{row[2]:>+8.3f}   {row[3]:>7}{row[4]:>6.1f}%{row[5]:>+8.3f}")


def feature_report(events):
    R = [e for e in events if not e["control"]]
    C = [e for e in events if e["control"]]

    def rate(xs):
        return (100 * sum(e["res"] for e in xs) / len(xs), len(xs)) if xs else (0.0, 0)
    filters = {
        "all touches": lambda e: True,
        "first touch only": lambda e: e["first"],
        "flipped zone (retest)": lambda e: e["flipped"],
        "price away >= 2 ATR": lambda e: e["away"] >= 2,
        "rejection close": lambda e: e["rej"],
        "rejection + conf>=3": lambda e: e["rej"] and e["conf"] >= 3,
        "London/NY 07-17 UTC": lambda e: 7 <= e["hour"] < 17,
        "Asia 00-07 UTC": lambda e: e["hour"] < 7,
    }
    print("Filters (reaction %, real vs random control zones):")
    for k, f in filters.items():
        r, rn = rate([e for e in R if f(e)])
        c, cn = rate([e for e in C if f(e)])
        print(f"  {k:<24}{r:6.1f}% (n={rn:<5}) vs {c:5.1f}% (n={cn:<5}) edge {r - c:+5.1f}")


if __name__ == "__main__":
    m5 = load("xauusd_5m.csv")
    h1 = load("xauusd_1h.csv")

    cfg5 = dict(BASE, max_age=288 * 5)             # 5 trading days
    s, c, cf, ev = run(m5, cfg5, htf_bars=resample(m5, 3600))
    report("XAUUSD 5m  (HTF = 1H)", s, c, cf, len(m5))
    feature_report(ev)
    trade_report(m5, ev)

    cfg1 = dict(BASE, max_age=24 * 20, round_step=50.0, look=8)   # 20 trading days
    s, c, cf, ev = run(h1, cfg1, htf_bars=resample(h1, 4 * 3600))
    report("XAUUSD 1H  (HTF = 4H)", s, c, cf, len(h1))
    feature_report(ev)
    trade_report(h1, ev)
