#!/usr/bin/env python3
"""HI Grade — Renormalization Simulation. Read-only. Changes nothing."""
import collections, json, statistics, sys
from pathlib import Path

DIMS = ["H","U","M","A","N"]
NO_DATA = 50

def clamp(x, lo=0, hi=100): return max(lo, min(hi, x))

def composite_with_floor(dv):
    if not dv: return None, False
    comp = sum(dv.values())/len(dv)
    if any(v < 42 for v in dv.values()): return round(min(comp,50)), True
    return round(comp), False

def main():
    path = Path("data/scores/all_scores.json")
    if not path.exists():
        print(f"not found: {path} — run from ~/Desktop/repo/pipeline"); return 1
    rows = json.load(open(path))
    cur_comps, new_comps, movers = [], [], []
    vhits = vtotal = skipped = 0
    dropped = collections.Counter()
    thin_means = []

    for r in rows:
        genome = r.get("genome") or {}
        if not genome: skipped += 1; continue
        cur_dims, new_dims, measured_all, ok = {}, {}, [], True
        for d in DIMS:
            scores = (genome.get(d) or {}).get("scores") or {}
            vals = [v for v in scores.values() if isinstance(v,(int,float))]
            published = r.get(f"D_{d}")
            if not vals or not isinstance(published,(int,float)): ok = False; break
            offset = published - sum(vals)/len(vals)   # harm+decay, recovered
            cur_dims[d] = published
            measured = [v for v in vals if v != NO_DATA]
            measured_all.extend(measured)
            if measured: new_dims[d] = clamp(round(sum(measured)/len(measured) + offset))
            else: dropped[d] += 1
        if not ok: skipped += 1; continue
        cur_comp,_ = composite_with_floor(cur_dims)
        new_comp,_ = composite_with_floor(new_dims)
        if cur_comp is None or new_comp is None: skipped += 1; continue
        pc = r.get("composite")
        if isinstance(pc,(int,float)):
            vtotal += 1
            if abs(cur_comp - pc) <= 1: vhits += 1
        cur_comps.append(cur_comp); new_comps.append(new_comp)
        n = len(measured_all)
        movers.append((new_comp-cur_comp, r.get("ticker") or r.get("company"), cur_comp, new_comp, n))
        if n and n <= 8: thin_means.append(statistics.mean(measured_all))

    if not cur_comps: print("no usable rows"); return 1

    print("="*72); print("  VALIDATION — can we reproduce the published scores?"); print("="*72)
    pct = vhits/vtotal*100 if vtotal else 0
    print(f"  reconstructed within 1 point of published: {vhits}/{vtotal} ({pct:.1f}%)")
    print(f"  rows skipped: {skipped}")
    if pct < 90: print("\n  *** BELOW 90% — model of the engine is wrong. Ignore everything below.")

    def desc(label, xs):
        xs = sorted(xs); n = len(xs)
        return (f"  {label:12} n={n}  mean={statistics.mean(xs):5.1f}  stdev={statistics.pstdev(xs):4.1f}  "
                f"p25={xs[n//4]}  p50={xs[n//2]}  p75={xs[3*n//4]}  min={xs[0]}  max={xs[-1]}")
    print(); print("="*72); print("  DISTRIBUTION — current vs renormalized"); print("="*72)
    print(desc("current", cur_comps)); print(desc("renormalized", new_comps))
    cb = sum(1 for x in cur_comps if 45<=x<=65)/len(cur_comps)*100
    nb = sum(1 for x in new_comps if 45<=x<=65)/len(new_comps)*100
    print(f"\n  within 45-65:  current {cb:.0f}%   renormalized {nb:.0f}%")

    print(); print("="*72); print("  THE BIAS QUESTION"); print("="*72)
    if thin_means:
        m = statistics.mean(thin_means)
        print(f"  Thin-coverage companies (<=8 signals): mean of their ACTUALLY")
        print(f"  MEASURED sub-signals = {m:.1f}")
        if m > 55: print("\n  >> Measured signals skew HIGH. Renormalizing INFLATES thin-data\n     companies — rewards non-disclosure. Bad trade.")
        elif m < 45: print("\n  >> Measured signals skew LOW. Renormalizing PENALIZES thin-data\n     companies. Defensible but harsh on small/new companies.")
        else: print("\n  >> Measured signals near neutral. Renormalizing widens spread without\n     systematically favouring anyone. Good trade.")
    print(f"\n  mean score change: {statistics.mean(b-a for a,b in zip(cur_comps,new_comps)):+.1f} points")

    print(); print("="*72); print("  BIGGEST MOVERS"); print("="*72)
    movers.sort(key=lambda x: -x[0])
    print(f"  {'ticker':10} {'now':>5} {'new':>5} {'delta':>7} {'signals':>8}")
    for delta,t,c,n2,ns in movers[:10]: print(f"  {str(t)[:10]:10} {c:>5} {n2:>5} {delta:>+7} {ns:>8}")
    print("  ...")
    for delta,t,c,n2,ns in movers[-10:]: print(f"  {str(t)[:10]:10} {c:>5} {n2:>5} {delta:>+7} {ns:>8}")

    if dropped:
        print(); print("="*72); print("  DIMENSIONS WITH NO DATA AT ALL (excluded when renormalizing)"); print("="*72)
        for d,n in dropped.most_common(): print(f"  D_{d}: {n} companies have zero measured sub-signals")
    print()
    return 0

sys.exit(main())
