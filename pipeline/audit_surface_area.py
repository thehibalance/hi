#!/usr/bin/env python3
"""The denominator: everything that exists, and whether anything has audited it.

    cd pipeline && python3 audit_surface_area.py

Read-only. Nothing is scored, judged or changed — this builds the LIST.

WHY THIS EXISTS

Four days of audit produced one consistent failure: the denominator was always wrong.

  · `audit_constants.py` tested three fallback tables and concluded which sub-signals are
    constants. It only ever read `scoring_engine.py`. A.3's tables live in
    `subsignal_pipelines.py`, so A.3 was counted as the second-largest REAL signal for
    three days while being a nine-rung industry ladder.
  · `count_sources.py` listed every source that contributed. USPTO, OSHA, DOL and EPA
    contribute nothing, so a list of what is present could not show them.
  · Nothing examined error records, so 26 EPA failures reading "No EPA-regulated
    facilities found" sat unread for six months.
  · The honest baseline went 19 -> 13 -> 9 -> 8. Four revisions, all downward, each from
    looking one level closer at something already counted.

A number that only falls when examined was never measured. So before any more fixing:
build the map, mark what has been looked at, and let the percentage mean something.

WHAT THIS INVENTORIES

  1. EVERY hand-written numeric table in EVERY .py file — not just scoring_engine.py.
     A dict with string keys and numeric values is a candidate scoring ladder. This is
     the sweep that would have caught DEFORESTATION_RISK and DEFORESTATION_FLAGS.
  2. EVERY field published on a scored row, and whether the RUBRIC documents it.
     `decay_index`, `algo_harm`, `confidence`, `humanwashing_flags`, `hi_balanced_gates`
     are all published per company and none has a RUBRIC entry.
  3. EVERY collector directory: record count, error rate, and age of the newest fetch.
     This is how the EPA store's 26/26 failures become visible as a number.
  4. EVERY .py file in pipeline/, and whether any audit or probe script names it.
     The "has anything ever read this" column is the point of the whole exercise.

WHAT IT DOES NOT DO

It does not decide whether anything is wrong. A hand-written table is not a defect —
`u4_industry` is documented and disclosed. An unaudited file is not a bug. This produces
the list that makes "100% of gaps identified" a claim rather than a hope.
"""
import ast
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(".")
if not (HERE / "scoring_engine.py").exists():
    raise SystemExit("  run from pipeline/")


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=15).stdout.strip()
    except Exception:
        return "?"


print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}\n")

pyfiles = sorted(p for p in HERE.glob("*.py"))
AUDITS = [p for p in pyfiles if p.name.startswith(("audit_", "probe_", "verify_",
                                                   "count_", "check_", "sim_", "diff_"))]
CODE = [p for p in pyfiles if p not in AUDITS]

# ══ 1. Every hand-written numeric table, in every file ════════════════════
print("1. HAND-WRITTEN NUMERIC TABLES — every .py file, not just scoring_engine.py\n")
print(f"   {'file':28} {'line':>6} {'name':30} {'n':>4} {'range':>14}")
print("   " + "─" * 88)

tables = []
for p in CODE:
    try:
        tree = ast.parse(p.read_text())
    except Exception as e:
        print(f"   {p.name:28} !! could not parse: {e}")
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        name = (node.targets[0].id if isinstance(node.targets[0], ast.Name) else "?")
        try:
            d = ast.literal_eval(node.value)
        except Exception:
            continue
        nums = [v for v in d.values() if isinstance(v, (int, float))]
        if len(nums) < 3 or len(nums) != len(d):
            continue          # not a flat numeric lookup
        tables.append((p.name, node.lineno, name, len(d), min(nums), max(nums), d))
        print(f"   {p.name:28} {node.lineno:>6} {name[:30]:30} {len(d):>4} "
              f"{min(nums):>6} ..{max(nums):>5}")

print(f"\n   {len(tables)} flat numeric lookups across {len({t[0] for t in tables})} files.")
print("   `audit_constants.py` tested THREE of these, all in scoring_engine.py.")
print("   For each one the question is the same: which sub-signal reads it, how many")
print("   companies land on it, and did anything outside this repo choose its values.")

# ══ 2. Every published row field, against the RUBRIC ══════════════════════
print("\n\n2. PUBLISHED ROW FIELDS — what every company's record carries\n")
SC = Path("data/scores/all_scores.json")
rub = ""
for cand in (Path("../RUBRIC.md"), Path("RUBRIC.md")):
    if cand.exists():
        rub = cand.read_text()
        break

if SC.exists():
    rows = [r for r in json.load(open(SC))
            if not r.get("error") and r.get("spec_version")]
    top = Counter()
    for r in rows[:400]:
        top.update(r.keys())

    documented = set(re.findall(r"^### ([A-Z]\.\d)", rub, re.M)) if rub else set()
    IDENT = {"company", "ticker", "sic", "sic_description", "industry", "domains",
             "spec_version", "retrieved"}
    DIMS = {"D_A", "D_H", "D_M", "D_N", "D_U", "composite", "genome"}

    print(f"   {len(rows)} rows · {len(top)} distinct top-level fields\n")
    print(f"   {'field':26} {'on rows':>8}  RUBRIC / audited?")
    print("   " + "─" * 74)
    unexamined = []
    for f, n in sorted(top.items()):
        if f in IDENT:
            note = "identity"
        elif f in DIMS:
            note = "dimension math — documented"
        elif rub and f in rub:
            note = "named in RUBRIC.md"
        else:
            note = "** NOT in the RUBRIC **"
            unexamined.append(f)
        print(f"   {f:26} {n:>8}  {note}")

    print(f"\n   Fields published on every company with no RUBRIC entry: "
          f"**{len(unexamined)}**")
    for f in unexamined:
        print(f"      {f}")
    print("\n   These are published through the API and rendered on the site. A field a")
    print("   visitor can read and the methodology does not mention is a claim with no")
    print("   documentation behind it — the same defect as an undocumented sub-signal,")
    print("   in a place no sub-signal audit looks.")
else:
    print("   !! no data/scores/all_scores.json")

# ══ 3. Collector health ═══════════════════════════════════════════════════
print("\n\n3. COLLECTOR HEALTH — records, errors, and age\n")
print(f"   {'collector':20} {'records':>8} {'errors':>7} {'err %':>7} {'newest fetch':>14}")
print("   " + "─" * 70)
now = datetime.now(timezone.utc)
dead_collectors = []
for d in sorted(Path("data").iterdir()) if Path("data").exists() else []:
    f = d / "all_companies.json"
    if not f.is_file():
        continue
    try:
        raw = json.load(open(f))
    except Exception:
        print(f"   {d.name:20}   !! unreadable")
        continue
    recs = raw if isinstance(raw, list) else list(raw.values())
    recs = [r for r in recs if isinstance(r, dict)]
    errs = sum(1 for r in recs if r.get("error"))
    dates = [r.get("retrieved") for r in recs if r.get("retrieved")]
    newest = max(dates) if dates else "—"
    age = ""
    if newest != "—":
        try:
            days = (now - datetime.fromisoformat(newest).replace(
                tzinfo=timezone.utc)).days
            age = f"  ({days}d)"
        except Exception:
            pass
    pct = 100 * errs / len(recs) if recs else 0
    flag = "  <- ALL ERRORS" if recs and errs == len(recs) else ""
    print(f"   {d.name:20} {len(recs):>8} {errs:>7} {pct:>6.0f}% {newest:>14}{age}{flag}")
    if recs and errs == len(recs):
        dead_collectors.append(d.name)

if dead_collectors:
    print(f"\n   Collectors whose every record is an error: {', '.join(dead_collectors)}")
    print("   An error record still carries a `source` field, which is how a source with")
    print("   a 0% success rate stays in the registry and on the published source list.")

# ══ 4. Which files has the audit never read ═══════════════════════════════
print("\n\n4. WHAT NOTHING HAS AUDITED — the column that matters\n")
audit_text = "\n".join(p.read_text(errors="replace") for p in AUDITS)
docs_text = ""
for d in (Path("../claude"), Path("claude")):
    if d.is_dir():
        docs_text = "\n".join(f.read_text(errors="replace")
                              for f in d.glob("*.md"))
        break

print(f"   {len(AUDITS)} audit/probe scripts · {len(CODE)} pipeline modules")
_docs_note = "yes" if docs_text else "NO — claude/*.md not reachable from here"
print(f"   project findings read: {_docs_note}\n")
print(f"   {'module':34} {'lines':>7}  named by an audit?  named in a finding?")
print("   " + "─" * 84)
never = []
for p in CODE:
    n = len(p.read_text(errors="replace").splitlines())
    in_audit = p.name in audit_text
    in_docs = p.name in docs_text if docs_text else None
    a = "yes" if in_audit else "NO "
    d = ("yes" if in_docs else "NO ") if in_docs is not None else " ? "
    mark = ""
    if not in_audit and in_docs is False:
        never.append((p.name, n))
        mark = "   ** never examined **"
    print(f"   {p.name:34} {n:>7}  {a:>17}  {d:>18}{mark}")

print(f"\n   Modules no audit script and no finding document has ever named: "
      f"**{len(never)}**")
for name, n in sorted(never, key=lambda x: -x[1]):
    print(f"      {name:34} {n:>6} lines")

print("\n\nHOW TO READ THIS\n")
print("  Nothing above is a defect. A hand-written table is not a bug — `u4_industry` is")
print("  documented and disclosed. An unaudited module is not broken.")
print("\n  What this is, is the DENOMINATOR. Every revision of the honest baseline")
print("  (19 -> 13 -> 9 -> 8) came from finding something that was already there and")
print("  already counted, in a place the previous audit had not looked. The percentage")
print("  of gaps identified cannot be stated until this list stops growing.")
print("\n  The order to work it: tables with no known reader, then row fields with no")
print("  RUBRIC entry, then modules nothing has read, longest first.")
print("\nNothing changed. Read-only.")
