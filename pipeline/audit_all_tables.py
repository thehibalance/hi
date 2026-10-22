#!/usr/bin/env python3
"""Every hand-written table, which sub-signal reads it, and how much it carries.

    cd pipeline && python3 audit_all_tables.py

Read-only.

WHY THIS REPLACES audit_constants.py

`audit_constants.py` tested three tables — `craft_defaults`, `u4_industry`, `hw_defaults`
— all in `scoring_engine.py`, and its output was read as "which sub-signals are constants".
`audit_surface_area.py` found **25 real tables across 10 files**. The three it tested were
the three it knew about.

That gap cost three baseline revisions:

  · A.3 counted as the second-largest REAL signal for three days. Its tables
    (`DEFORESTATION_RISK`, `DEFORESTATION_FLAGS`) are in `subsignal_pipelines.py`.
  · A.4 was CLEARED at 101 off-lattice against `hw_defaults` — 4 entries,
    `scoring_engine.py:1437`. It also reads `HARDWARE_INDUSTRY_DEFAULTS` — 15 entries,
    `subsignal_pipelines.py:455`. **The clearance tested one of two tables.**
  · A.1 was marked UNPROVEN, "inline fallback, no lattice to test". Its dict is called
    `defaults` at `scoring_engine.py:1356`. It was always testable.

THE FOUR KINDS OF TABLE, which matters more than the count

  ladder  values inside 0..100, all non-negative — a score lattice. A published value
          equal to one of these is probably the fallback.
  offset  contains negatives, or everything is small — these SHIFT a ladder, so the
          lattice for a sub-signal is {base} union {base + offset}. A.3's nine published
          rungs are exactly `DEFORESTATION_RISK` plus `DEFORESTATION_FLAGS`, which is why
          testing either one alone would have found nothing.
  data    hand-written FACTS outside the 0..100 range — employee counts, pay ratios,
          revenue medians. Not a ladder. A different and arguably worse problem: a
          hardcoded fact about a named company, feeding a signal counted as measured.
  flag    0/1 membership lists — `GRI_REPORTERS`, `KNOWN_B_CORPS`. A hardcoded list of
          tickers labelled with the name of an external source.

WHAT THIS STILL CANNOT SEE

Adjustments written inline rather than in a dict — H.3's headcount tiers (+15/+10/+5) and
its displacement penalty are `if` statements, so H.3's lattice here is incomplete and its
off-lattice count will read high. Flagged in the output rather than left to be discovered.
"""
import ast
import json
import re
import subprocess
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

SS = re.compile(r"^[A-Z]\.\d$")
NEUTRAL = 50
MIN_N = 40

if not Path("scoring_engine.py").exists():
    raise SystemExit("  run from pipeline/")


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=15).stdout.strip()
    except Exception:
        return "?"


files = sorted(p for p in Path(".").glob("*.py")
               if not p.name.startswith(("audit_", "probe_", "verify_", "count_",
                                         "check_", "sim_", "diff_", "patch_",
                                         "measure_")))

print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}")
print(f"scanning {len(files)} modules\n")


def classify(vals):
    nums = [v for v in vals if isinstance(v, (int, float))]
    if not nums or len(nums) != len(vals):
        return None
    if set(nums) <= {0, 1}:
        return "flag"
    if all(v == 0 for v in nums):
        return None                     # a counter, not a table
    if min(nums) < 0 or max(nums) <= 25:
        return "offset"
    if 0 <= min(nums) and max(nums) <= 100:
        return "ladder"
    return "data"


# ── Collect tables and the functions that read them ───────────────────────
tables = {}          # (file, name) -> dict(kind, vals, line)
fns = []             # (file, parsed tree)

for p in files:
    try:
        tree = ast.parse(p.read_text())
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict) \
                and isinstance(node.targets[0], ast.Name):
            try:
                d = ast.literal_eval(node.value)
            except Exception:
                continue
            kind = classify(list(d.values()))
            if kind:
                tables[(p.name, node.targets[0].id)] = {
                    "kind": kind, "vals": d, "line": node.lineno}
    fns.append((p.name, tree))

# ── Attribute tables to sub-signals BY DATA FLOW, not by function membership ──
#
# THE BUG THIS REPLACES
#
# The first version asked: does this function reference the table AND assign this
# sub-signal? A dimension function assigns four sub-signals and references all of its
# dimension's tables, so every sub-signal inherited every table:
#
#   A.1 A.2 A.3 A.4  ->  defaults, hw_defaults          (identical)
#   H.1 H.2 H.3 H.5  ->  craft_defaults, h3_industry    (identical)
#   U.1 U.2 U.3 U.4  ->  u4_industry                    (identical)
#
# Each lattice then became its whole dimension's tables plus every base+offset sum, wide
# enough to cover most of 0..100, so nearly nothing read as off-lattice. A.4 came back at
# 3 measured against the 101 measured directly; U.3 at "mostly table" with 108 from HRC
# and Disability:IN. Every verdict was void.
#
# Second attribution failure in two days, same root as the first: a structural fact about
# the FILE read as a fact about the SIGNAL. Function membership is not data flow.
#
# So: follow the assignments. A variable carries the tables it was derived from, through
# any number of steps, and a sub-signal is attributed only the tables that reach its own
# assignment expression.
#
#   base = DEFORESTATION_RISK.get(industry, 50)   -> base  carries {DEFORESTATION_RISK}
#   flag = DEFORESTATION_FLAGS.get(ticker, 0)     -> flag  carries {DEFORESTATION_FLAGS}
#   a3   = base + flag                            -> a3    carries both
#   scores["A.3"] = a3                            -> A.3   gets both, and nothing else
#
# Branches are merged by union, which is conservative: a sub-signal may be credited a
# table from a path it did not take, never denied one from a path it did.
TABLE_NAMES = {n for (_, n) in tables}
reader = defaultdict(set)


def names_in(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def flow(stmts, carried, fname):
    """Walk statements in source order, carrying var -> tables it derives from."""
    for st in stmts:
        if isinstance(st, (ast.Assign, ast.AugAssign)):
            val = st.value
            ids = names_in(val)
            got = {n for n in ids if n in TABLE_NAMES}
            for n in ids:
                got |= carried.get(n, set())
            targets = st.targets if isinstance(st, ast.Assign) else [st.target]
            for tgt in targets:
                if isinstance(tgt, ast.Name):
                    carried[tgt.id] = carried.get(tgt.id, set()) | got
                elif isinstance(tgt, ast.Subscript) and isinstance(tgt.slice, ast.Constant) \
                        and isinstance(tgt.slice.value, str) and SS.match(tgt.slice.value):
                    reader[tgt.slice.value] |= got
        elif isinstance(st, ast.Return) and isinstance(st.value, ast.Dict):
            for k, v in zip(st.value.keys, st.value.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str) \
                        and SS.match(k.value):
                    ids = names_in(v)
                    got = {n for n in ids if n in TABLE_NAMES}
                    for n in ids:
                        got |= carried.get(n, set())
                    reader[k.value] |= got
        # recurse into any nested block, carrying the same map (branches merge by union)
        for field in ("body", "orelse", "finalbody"):
            inner = getattr(st, field, None)
            if isinstance(inner, list) and inner and isinstance(inner[0], ast.stmt):
                flow(inner, carried, fname)


for fname, tree in fns:
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        flow(fn.body, {}, fname)

# reader is keyed by sub-signal -> set of TABLE NAMES. Re-key tables by name for lookup.
by_name = {}
for (fname, tname), info in tables.items():
    by_name.setdefault(tname, []).append((fname, info))

# table name -> sub-signals whose assignment expression it reaches
tbl_to_ss = defaultdict(set)
for ss, tnames in reader.items():
    for tn in tnames:
        tbl_to_ss[tn].add(ss)

print("EVERY TABLE, ITS KIND, AND WHICH SUB-SIGNAL'S VALUE IT REACHES\n")
print("  Attribution follows the assignment chain, so a table appears against a")
print("  sub-signal only if it reaches that sub-signal's own expression.\n")
print(f"  {'file':26} {'table':30} {'kind':7} {'n':>4} {'range':>15}  reaches")
print("  " + "─" * 104)
for (fname, tname), info in sorted(tables.items(),
                                   key=lambda kv: (kv[0][0], kv[1]["line"])):
    nums = [v for v in info["vals"].values()]
    rd = ",".join(sorted(tbl_to_ss.get(tname, ()))) or "— reaches no sub-signal —"
    print(f"  {fname[:26]:26} {tname[:30]:30} {info['kind']:7} {len(nums):>4} "
          f"{min(nums):>7}..{max(nums):<6} {rd}")

orphans = [(f, t) for (f, t) in tables if not tbl_to_ss.get(t)]
print(f"\n  Tables reaching no sub-signal assignment: **{len(orphans)}**")
for f, t in sorted(orphans):
    print(f"      {t:32} {f}  ({tables[(f, t)]['kind']})")
print("  Either they feed something that is not a sub-signal — decay, harm, the floor —")
print("  or nothing reads them at all. Both are worth knowing; neither is a lattice.")

# ── The off-lattice test, per sub-signal, over ALL its tables ─────────────
SCP = Path("data/scores/all_scores.json")
if not SCP.exists():
    raise SystemExit("\n  no data/scores/all_scores.json — the table map above still stands")
rows = [r for r in json.load(open(SCP)) if not r.get("error") and r.get("spec_version")]

by_ss = defaultdict(lambda: {"ladder": [], "offset": [], "where": []})
for ss, tnames in reader.items():
    for tn in tnames:
        for fname, info in by_name.get(tn, []):
            if info["kind"] not in ("ladder", "offset"):
                continue
            by_ss[ss][info["kind"]] += list(info["vals"].values())
            by_ss[ss]["where"].append(f"{tn}@{fname}:{info['line']}")

g = lambda r, d, k: ((r.get("genome") or {}).get(d) or {}).get("scores", {}).get(k)

print(f"\n\nOFF-LATTICE TEST — {len(rows)} rows, every table a sub-signal reads\n")
print("  lattice = {ladder values} union {ladder + offset}, because an offset table")
print("  shifts a base. A.3's nine published rungs are DEFORESTATION_RISK plus")
print("  DEFORESTATION_FLAGS — testing either alone finds nothing.\n")
print(f"  {'ss':5} {'tables':>7} {'rows':>6} {'at 50':>7} {'on-lat':>7} {'OFF-LAT':>8} "
      f"{'measured %':>11}  verdict")
print("  " + "─" * 86)

results = {}
for ss in sorted(by_ss):
    base = [v for v in by_ss[ss]["ladder"]]
    offs = [v for v in by_ss[ss]["offset"]]
    lat = set(base) | {b + o for b, o in product(base or [0], offs or [0])}
    lat = {round(v, 1) for v in lat}
    dim = ss.split(".")[0]
    vals = [g(r, dim, ss) for r in rows]
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        continue
    at50 = sum(1 for v in vals if v == NEUTRAL)
    on = sum(1 for v in vals if v != NEUTRAL and round(v, 1) in lat)
    off = sum(1 for v in vals if v != NEUTRAL and round(v, 1) not in lat)
    pct = 100 * off / len(vals)
    verdict = ("TABLE" if off < MIN_N else
               "mostly table" if off < len(vals) * 0.25 else "measured")
    results[ss] = (off, verdict, by_ss[ss]["where"])
    print(f"  {ss:5} {len(by_ss[ss]['where']):>7} {len(vals):>6} {at50:>7} {on:>7} "
          f"{off:>8} {pct:>10.1f}%  {verdict}")

print("\n  OFF-LAT is the measured count: a published value that is NOT reachable from")
print("  any of this sub-signal's tables had to come from a measured path.\n")
for ss in sorted(results):
    print(f"  {ss}: {' · '.join(results[ss][2])}")

tabled = [ss for ss, (off, v, _) in results.items() if v == "TABLE"]
print(f"\n  Sub-signals below the {MIN_N}-company threshold on measured values: "
      f"**{len(tabled)}** — {', '.join(tabled) or 'none'}")

# ── Hand-written facts and membership lists ───────────────────────────────
print("\n\nHAND-WRITTEN FACTS AND MEMBERSHIP LISTS — a different problem\n")
print("  These are not ladders. They are hardcoded statements about named companies,")
print("  feeding signals that are counted as measured.\n")
print(f"  {'file':28} {'table':28} {'kind':6} {'entries':>8}  reads into")
print("  " + "─" * 94)
for (fname, tname), info in sorted(tables.items()):
    if info["kind"] not in ("data", "flag"):
        continue
    rd = ",".join(sorted(tbl_to_ss.get(tname, ()))) or "— reaches no sub-signal —"
    print(f"  {fname[:28]:28} {tname[:28]:28} {info['kind']:6} {len(info['vals']):>8}  {rd}")

print("\n  The two that matter most:")
print("    EMPLOYEE_COUNTS  — revenue-per-employee is the divisor for H.1 AND H.3,")
print("                       553 companies, half of D_H, the largest real signal.")
print("                       A hardcoded headcount makes part of that divisor editorial.")
print("    GRI_REPORTERS    — a list of tickers labelled with the name of a database that")
print("                       is decommissioned. It was never fetched from anywhere.")

print("\n\nWHAT THIS CANNOT SEE")
print("  Inline adjustments. H.3's headcount tiers (+15/+10/+5) and displacement penalty")
print("  are `if` statements, not dicts, so H.3's lattice above is incomplete and its")
print("  off-lattice count reads HIGH. Same for any sub-signal whose arithmetic is")
print("  written out rather than tabulated. A high OFF-LAT is evidence of measurement")
print("  only where the sub-signal's whole fallback is in dicts.")
print("\n  This is the proxy, still. The real answer is `derived_signals` published per")
print("  row — then nothing is inferred and this script can be deleted rather than")
print("  extended. Five instances of the project's oldest bug have now come from")
print("  estimating what the engine could simply record.")
print("\nNothing changed. Read-only.")
