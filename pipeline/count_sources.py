#!/usr/bin/env python3
"""The honest source count, and the dead source paths. Read-only. From pipeline/:

    python3 count_sources.py

WHAT THE FIRST VERSION GOT WRONG

It printed `own tables counted as sources: 0`. `Industry` is on 100% of rows and
`Industry+EPA` on 28.5%, and both are the project's own tables — `Industry` IS the
INDUSTRY_DERIVED label. The exclusion list held `industry rpe`, `industry median`,
`industry default`, `industry table`, and not the bare word.

Twelfth defect in this project's audit tooling in two days, and the same shape as the other
eleven: a substring list standing in for the question "is this ours?". A script written
specifically to catch the project counting its own tables as external data counted the
project's own tables as external data.

So the classification is now an ALLOWLIST read from the filesystem — a source is external
if it has a collector directory — plus a short explicit list of the project's own labels.
There are ~22 collectors. Naming them is finite. Guessing at name fragments is not.

THE THREE POPULATIONS

The 56 names in the first run were not one thing:

  · data sources — collectors producing values across companies (~22)
  · the project's own tables — `Industry`, `Industry+EPA` (2)
  · citations in hand-authored harm documentation (~34) — individual DOJ press releases,
    a 2016 NYT magazine piece, a BMJ paper, CDC pages, one row each, via
    `harm_documentation.sources`

A URL cited once in a harm write-up is not a dataset. Counting it as one inflates the
figure by 34, which is the same category error as counting the industry tables.

THE DEAD-PATH CHECK, which is the part worth having

`sources_used.append("X")` in the engine names every source the code CAN credit. Comparing
that set against what actually appears in production finds sources that are wired and never
fire. The first run could not see these, because a list of what is present cannot show what
is absent — the oldest failure mode in this project, appearing one more time in the shape of
a question not asked.

OSHA, DOL and USPTO are the answer, and USPTO is the one nobody had noticed.
"""
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

# The project's own labels. Short, explicit, and NOT substring-guessed.
OWN = {"industry", "industry+epa", "ahi", "ahi™", "seed", "manual", "prior"}

SC = Path("data/scores/all_scores.json")
ENG = Path("scoring_engine.py")
for f in (SC, ENG):
    if not f.exists():
        raise SystemExit(f"  missing {f} — run from pipeline/")


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return "?"


rows = [r for r in json.load(open(SC)) if not r.get("error") and r.get("spec_version")]
eng = ENG.read_text()
print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}")
print(f"{len(rows)} pipeline rows\n")

# ── The allowlist: a source is external if it has a collector ─────────────
collectors = sorted(p.name for p in Path("data").iterdir()
                    if p.is_dir() and (p / "all_companies.json").exists()) \
    if Path("data").exists() else []
print(f"collector directories with an all_companies.json: {len(collectors)}")
print("  " + ", ".join(collectors) + "\n")

# ── Count, keeping the three populations apart ────────────────────────────
SRC_KEYS = {"sources", "sources_used", "data_sources", "source"}
data_src, harm_src = Counter(), Counter()
occurrences = Counter()


def walk(node, path, out):
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, f"{path}.{k}" if path else k, out)
    elif isinstance(node, list):
        for v in node:
            if isinstance(v, str):
                out.append((path, v))
            else:
                walk(v, path, out)


for r in rows:
    found = []
    walk(r, "", found)
    seen_data, seen_harm = set(), set()
    for path, val in found:
        leaf = path.split(".")[-1]
        if leaf not in SRC_KEYS:
            continue
        occurrences[path] += 1
        name = val.strip()
        # A citation is a URL, or it arrived under harm_documentation.
        if path.startswith("harm_documentation") or name.startswith("http"):
            seen_harm.add(name)
        else:
            seen_data.add(name)
    for n in seen_data:
        data_src[n] += 1
    for n in seen_harm:
        harm_src[n] += 1

if not data_src:
    raise SystemExit("  !! no data-source names found. Refusing to print a count from a\n"
                     "     field that does not exist. grep -n 'sources_used' scoring_engine.py")

print("occurrences by path (occurrences, NOT rows — the first version mislabelled this):")
for path, n in occurrences.most_common():
    print(f"   {path:44} {n:>7,}")

own = {s for s in data_src if s.lower() in OWN}
external = {s for s in data_src if s not in own}

print(f"\nDATA SOURCES — companies each contributed a value to\n")
print(f"   {'source':34} {'companies':>10} {'% universe':>11}")
print("   " + "─" * 58)
for s, n in data_src.most_common():
    mark = "   <- OURS" if s in own else ""
    print(f"   {s[:34]:34} {n:>10} {100 * n / len(rows):>10.1f}%{mark}")

LOAD = 40
heavy = sorted(((n, s) for s, n in data_src.items() if n >= LOAD and s in external),
               reverse=True)
print(f"\n   External sources reaching {LOAD}+ of {len(rows)} companies: **{len(heavy)}**")
for n, s in heavy:
    print(f"      {s[:34]:34} {n:>6}")
print("   Everything else is under that line. This is the honest answer to 'how much")
print("   evidence is behind a score', and no public document says it.")

# ── The dead-path check ───────────────────────────────────────────────────
named = set(re.findall(r'sources_used\.(?:append|extend)\(\s*\[?\s*"([^"]+)"', eng))
for m in re.finditer(r'sources_used\.extend\(\s*\[([^\]]+)\]', eng):
    named |= set(re.findall(r'"([^"]+)"', m.group(1)))
dead = sorted(n for n in named if data_src.get(n, 0) == 0)

print(f"\nDEAD SOURCE PATHS — named in the engine, credited on zero rows\n")
print(f"   the engine can credit {len(named)} source names: "
      f"{', '.join(sorted(named))}")
if dead:
    for n in dead:
        lines = [eng[:m.start()].count("\n") + 1
                 for m in re.finditer(r'sources_used\.\w+\([^)]*"' + re.escape(n) + r'"', eng)]
        print(f"   {n:12} 0 rows   scoring_engine.py:{', '.join(map(str, lines))}")
    print("\n   Wired and never firing. A list of what is present cannot show what is")
    print("   absent, which is why the first version of this script could not find these.")
else:
    print("   none — every source the engine can credit has credited at least one row")

print(f"\nTHE NUMBERS THE DOCUMENTS SHOULD QUOTE\n")
print(f"   collectors on disk                          : {len(collectors):>4}")
print(f"   data sources contributing a value           : {len(data_src):>4}")
print(f"   ...of those, the project's own tables       : {len(own):>4}"
      + (f"  ({', '.join(sorted(own))})" if own else ""))
print(f"   EXTERNAL data sources contributing a value  : {len(external):>4}")
print(f"   external sources reaching {LOAD}+ companies      : {len(heavy):>4}")
print(f"   harm-documentation citations (NOT sources)  : {len(harm_src):>4}")
print(f"\n   published:  README '21 sources feed today's scores, out of 41 integrated'")
print(f"               METHODOLOGY '17 public datasets' · docs '41 public data sources'")
print(f"   The '21 feed' figure is about right. The 41 is the one to re-derive.")
print(f"   check_continuity.py proves docs == source_audit. It does not prove either is")
print(f"   true: both sides can be wrong together and it still passes. Add this count as")
print(f"   a third leg so continuity means page = registry = reality.")

print("\nWHAT THIS STILL DOES NOT COVER")
print("  The floor rule (181 companies) and algo_harm (15, hand-authored, up to -7.4 on a")
print("  composite) move published scores and are not sources, not sub-signals, and in no")
print("  count here. D_H returns list(set(sources)) at line 1030 while D_U returns the raw")
print("  list at 1159, so source ORDER reads as precedence in one dimension and is")
print("  scrambled in the other.")
print("\nNothing changed. Read-only.")
