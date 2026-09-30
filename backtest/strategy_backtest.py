"""
Strategy backtest: 5m-style entry signals inside fresh 1H high-volume rejection zones
(the logic of pinescript/xauusd_hv_zones_5m.pine, run with backtest/entry_signals_5m.py).

Samples
  A  OANDA 5m entries  + OANDA 1H zones   (~4 weeks, exact indicator timeframe)
  B  OANDA 15m entries + OANDA 1H zones   (~2.5 months, proxy: same rules on 15m candles)
  C  COMEX GC1! 5m     + GC1! 1H zones    (~4 weeks, real futures volume, different zones)

For each: trades, win rate, average R, total R, profit factor, max drawdown (R),
for both triggers, both stop modes and 1R / 1.5R / 2R targets, plus the same rules
on random zones. Spread 0.30 $ per trade is included.
Trade list of the indicator defaults is written to strategy_trades.csv.
"""
import csv
import datetime as dt
import os

from entry_signals_5m import run
from volume_zones_backtest import load

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")


def stats(xs):
    if not xs:
        return None
    rs = [t["r"] for t in sorted(xs, key=lambda t: t["time"])]
    eq = peak = dd = 0.0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    gp = sum(r for r in rs if r > 0)
    gl = -sum(r for r in rs if r < 0)
    return dict(n=len(rs), win=100 * sum(r > 0 for r in rs) / len(rs), avg=sum(rs) / len(rs),
                tot=sum(rs), pf=gp / gl if gl else float("inf"), dd=dd)


def fmt(st):
    if not st:
        return "n=0"
    return (f"n={st['n']:<4} win {st['win']:5.1f}%  avg {st['avg']:+.2f}R  total {st['tot']:+6.1f}R  "
            f"PF {st['pf']:4.2f}  maxDD {st['dd']:4.1f}R")


SAMPLES = [
    ("A  OANDA 5m entries (4 wks)", "xauusd_5m.csv", "xauusd_1h.csv", 12),
    ("B  OANDA 15m entries (2.5 mo, proxy)", "xauusd_15m.csv", "xauusd_1h.csv", 4),
    ("C  COMEX GC1! 5m (4 wks)", "gc1_5m.csv", "gc1_1h.csv", 12),
]

if __name__ == "__main__":
    default_trades = []
    for label, ef, hf, per_hour in SAMPLES:
        eb, hb = load(os.path.join(D, ef)), load(os.path.join(D, hf))
        kw = dict(sig_win=2 * per_hour, max_bars=16 * per_hour, age_bars=24 * 15 * per_hour)
        print(f"\n==================== {label}")
        for stop_mode in ("swing", "zone"):
            for rr in (1.0, 1.5, 2.0):
                tr = run(eb, hb, rr=rr, stop_mode=stop_mode, **kw)
                tag = "  <-- indicator defaults" if (stop_mode, rr) == ("swing", 2.0) else ""
                print(f"\n  stop={stop_mode:<5} target={rr}R{tag}")
                for kind in ("REJ", "BOS", "ALL"):
                    R = [t for t in tr if not t["ctl"] and (kind == "ALL" or t["kind"] == kind)]
                    C = [t for t in tr if t["ctl"] and (kind == "ALL" or t["kind"] == kind)]
                    print(f"    {kind:<4} real   {fmt(stats(R))}")
                    print(f"    {'':<4} random {fmt(stats(C))}")
                if (stop_mode, rr) == ("swing", 2.0):
                    for t in tr:
                        if not t["ctl"]:
                            default_trades.append(dict(t, sample=label[:1]))
        # monthly breakdown for the longest sample, defaults
        if label.startswith("B"):
            tr = [t for t in run(eb, hb, rr=2.0, stop_mode="swing", **kw) if not t["ctl"]]
            print("\n  Monthly (sample B, defaults, both triggers):")
            months = sorted({dt.datetime.utcfromtimestamp(t["time"]).strftime("%Y-%m") for t in tr})
            for m in months:
                xs = [t for t in tr if dt.datetime.utcfromtimestamp(t["time"]).strftime("%Y-%m") == m]
                print(f"    {m}  {fmt(stats(xs))}")
    with open(os.path.join(HERE, "strategy_trades.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sample", "time_utc", "trigger", "dir", "entry", "stop", "target", "risk_$", "result_R"])
        for t in default_trades:
            w.writerow([t["sample"], dt.datetime.utcfromtimestamp(t["time"]).strftime("%Y-%m-%d %H:%M"),
                        t["kind"], "BUY" if t["dir"] == 1 else "SELL", round(t["entry"], 2),
                        round(t["stop"], 2), round(t["tgt"], 2), round(t["risk"], 2), round(t["r"], 2)])
