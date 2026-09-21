#!/usr/bin/env python3
"""Recompute INDUSTRY_RPE_MEDIANS from the scored universe.

The median company in each industry should score 65 on H.1 by construction.
That only holds if the divisor equals the real median, and the real median moves
as the universe grows. Re-run whenever the universe or the SIC mapping changes.

  python3 recalibrate_medians.py --scores /tmp/scores_current.json
  python3 recalibrate_medians.py --scores /tmp/scores_current.json --apply
"""
import json, re, shutil, statistics, sys, tempfile, py_compile, collections
from pathlib import Path
import scoring_engine as se

MIN_N, CONFIDENT_N = 3, 10
args = sys.argv
path = args[args.index("--scores") + 1] if "--scores" in args else "data/scores/all_scores.json"
rows = json.load(open(path))
print(f"  source: {path}  rows={len(rows)}  spec={rows[0].get('spec_version')}\n")

def industry_of(r):
    """What the engine will call this company after the SIC-3 change.

    SEC filers resolve from SIC. Seed rows (Patagonia, OpenAI, Shein - private or
    foreign, no filing, no SIC) carry their own industry and must keep it, or they
    vanish from the medians and lose H.1. A literal "default" is not a category.
    """
    sic = r.get("sic")
    if sic:
        ind = se.get_industry(sic)
        if ind:
            return ind
    ind = r.get("industry")
    return ind if ind and ind != "default" else None

buckets, seed_kept, unknown = collections.defaultdict(list), 0, 0
for r in rows:
    ind = industry_of(r)
    if not ind:
        unknown += 1
        continue
    if not r.get("sic"):
        seed_kept += 1
    v = (r.get("key_signals") or {}).get("revenue_per_employee")
    if isinstance(v, (int, float)) and v > 0:
        buckets[ind].append(v)

old = dict(se.INDUSTRY_RPE_MEDIANS)
new = {i: int(round(statistics.median(v))) for i, v in buckets.items() if len(v) >= MIN_N}
thin = {i: len(v) for i, v in buckets.items() if 0 < len(v) < MIN_N}

print(f"  {'industry':16} {'n':>4} {'old':>11} {'new':>11}  {'change':>8}")
print("  " + "-" * 56)
for i in sorted(new, key=lambda k: -len(buckets[k])):
    o = old.get(i)
    d = f"{(new[i]/o - 1)*100:+.0f}%" if o else "NEW"
    flag = "" if len(buckets[i]) >= CONFIDENT_N else "  provisional"
    print(f"  {i:16} {len(buckets[i]):>4} {o or 0:>11,} {new[i]:>11,}  {d:>8}{flag}")
for i, n in sorted(thin.items()):
    print(f"  {i:16} {n:>4} {'':>11} {'omitted':>11}   n<{MIN_N}")
for i in sorted(set(old) - set(new) - set(thin)):
    print(f"  {i:16} {'':>4} {old[i]:>11,} {'removed':>11}   nothing maps here")

print(f"\n  seed rows keeping their own industry: {seed_kept}")
print(f"  no industry at all (H.1 -> no data) : {unknown}")

if "--apply" not in args:
    print("\n  REPORT ONLY - add --apply to rewrite the table")
    sys.exit(0)

def fmt(d):
    return "\n".join(f'    "{i}": {v},   # n={len(buckets[i])}'
                     for i, v in sorted(d.items(), key=lambda kv: -len(buckets[kv[0]])))
conf = {i: v for i, v in new.items() if len(buckets[i]) >= CONFIDENT_N}
prov = {i: v for i, v in new.items() if len(buckets[i]) < CONFIDENT_N}
block = ("INDUSTRY_RPE_MEDIANS = {\n"
         "    # Recomputed from the scored universe by recalibrate_medians.py.\n"
         "    # The median company in each industry scores 65 on H.1 by construction.\n"
         "    # Regenerate whenever the universe or the SIC mapping changes.\n"
         f"{fmt(conf)}\n"
         f"    # provisional - fewer than {CONFIDENT_N} companies with RPE data\n"
         f"{fmt(prov)}\n"
         '    # No "default" key on purpose: an unknown industry has no credible peer\n'
         "    # baseline, so H.1 returns no-data rather than dividing by a fiction.\n"
         "}")

P = Path("scoring_engine.py"); src = P.read_text()
pat = re.compile(r"INDUSTRY_RPE_MEDIANS = \{.*?\n\}", re.S)
if len(pat.findall(src)) != 1:
    print(f"ABORTED: matched {len(pat.findall(src))} tables"); sys.exit(1)
shutil.copy2(P, str(P) + ".bakcal"); P.write_text(pat.sub(lambda m: block, src, count=1))
try: py_compile.compile(str(P), doraise=True, cfile=tempfile.mktemp(suffix=".pyc"))
except Exception as e:
    shutil.copy2(str(P) + ".bakcal", P); print(f"compile FAILED, rolled back: {e}"); sys.exit(1)
print(f"\n  APPLIED - {len(conf)} calibrated, {len(prov)} provisional, {len(thin)} omitted")
