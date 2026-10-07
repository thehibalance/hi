#!/usr/bin/env python3
"""The master audit: what the RUBRIC claims vs what the engine does. Read-only.

    cd pipeline && python3 audit_rubric_vs_engine.py

THE RULE THIS ENFORCES

RUBRIC.md says so itself, at the top:

    "Every entry below was checked against pipeline/scoring_engine.py in September 2026.
     Where this file and the code disagree, the code is right and this file is a bug."

Nineteen versions have shipped since that check. This script applies the rule mechanically
instead of by reading, so the answer stops depending on who last remembered to look.

WHAT CHANGED IN THIS VERSION, AND WHY — read this before trusting the old output

The previous version decided "overstated grounding" from a static grep: if the engine source
contained `INDUSTRY_DERIVED.add("<ss>")` anywhere, the sub-signal was a CONSTANT, and a
RUBRIC status of PARTIAL or GROUNDED on it was a documentation bug.

That reasoning is wrong, and it produced the worst single over-claim of the October audit.
The `.add()` sits INSIDE A BRANCH. A.4 has three measured paths — iFixit hardware scores
(line ~1413), a certification average (~1429), CDP Forests (~1435) — and only reaches
`hw_defaults` when all three miss. It is measured for 101 companies and constant for 944.
The RUBRIC calling it PARTIAL is correct. The audit calling that a bug was not.

Same error three times in one audit, each time reading a source-level fact as a per-company
runtime property: `v != 50` read as "measured"; absence-derived sub-signals excluded by name;
a conditional `.add()` read as unconditional.

So the test is now a runtime one, using the proxy from `audit_constants.py`: each fallback
draws from a small dict of hand-written integers, so a published value that is NOT on that
lattice came from a measured path. A PARTIAL/GROUNDED claim is overstated only when the
off-lattice count falls below MIN_N — i.e. when the constant really does carry the sub-signal.

It is a proxy, not proof. A measured path can land on a lattice value by coincidence, which
inflates the constant count; a table entry equal to 50 is invisible here because 50 is
already excluded as neutral. The real answer needs the engine to publish `derived_signals`
per row. Until it does, every audit of this question is estimating, and should say so.

AND THE SAME ERROR ONE LEVEL UP — fixed in this revision

The first attempt at the above gave the test TWO outcomes, cleared or overstated, and sent
anything it could not test into "cleared". A.1's fallback is INLINE with no named dict, so
it was untestable, so it was cleared, so it was counted as a real sub-signal and the
baseline printed 10 instead of 9.

That is the same mistake as the one this script was rewritten to stop making, one level up:
an absent test read as a pass. There are three outcomes. A sub-signal with no lattice to
test against is **UNPROVEN** — excluded from the baseline, named in the output, counted
neither way. The printed count is a floor, and it rises when something is shown to measure,
not when nothing contradicts it.

WHAT IT CHECKS

  1. The RUBRIC against ITSELF — header counts vs the summary table vs the sections, and
     whether every section carries its measured-coverage line.
  2. The RUBRIC's spec version against the engine's.
  3. Sub-signals the RUBRIC documents as active that the engine never assigns (retired).
  4. Sub-signals the engine assigns that the RUBRIC does not document.
  5. **Overstated grounding** — PARTIAL/GROUNDED where the published values are, in fact,
     almost all on the fallback lattice. Runtime-measured, per the note above.
  6. "Not yet scored" entries the engine does score, and vice versa.
  7. How much of the universe each active sub-signal actually covers.
  8. Same-dimension rank correlation, because two sub-signals averaged into one dimension
     that rank companies alike are one input claimed as two.

WHAT IT CANNOT CHECK

Whether an authoritative source measures the construct the sub-signal claims — the v1.9.0
test. That needs a human reading the source's methodology against the RUBRIC's words. This
script narrows the list to the ones worth reading.
"""
import ast
import json
import re
import statistics as st
import subprocess
from collections import defaultdict
from pathlib import Path

MIN_N = 40
NEUTRAL = 50
COVERAGE_TAG = "Coverage (Oct 2026)"
# sub-signal -> the dict its fallback branch reads, for the off-lattice proxy
TABLES = {"H.2": "craft_defaults", "U.4": "u4_industry", "A.4": "hw_defaults"}

ROOT = Path("..") if Path("../RUBRIC.md").exists() else Path(".")
RUB = ROOT / "RUBRIC.md"
ENG = Path("scoring_engine.py")
SCORES = Path("data/scores/all_scores.json")
for f in (RUB, ENG, SCORES):
    if not f.exists():
        raise SystemExit(f"  missing {f} — run this from pipeline/")

rub, eng = RUB.read_text(), ENG.read_text()
rows = [r for r in json.load(open(SCORES)) if not r.get("error") and r.get("spec_version")]


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return "?"


def grab_dict(name):
    """Pull `name = { ... }` out of the engine source by brace matching."""
    m = re.search(re.escape(name) + r"\s*=\s*\{", eng)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, len(eng)):
        if eng[j] == "{":
            depth += 1
        elif eng[j] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return ast.literal_eval(eng[i:j + 1])
                except Exception:
                    return None
    return None


print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}")
print(f"{len(rows)} pipeline rows · RUBRIC at {RUB}\n")

# ── Parse the RUBRIC ──────────────────────────────────────────────────────
# Sections are sliced to the NEXT heading so a per-section check cannot read a
# neighbour's text — the bug that let a missing coverage line go unnoticed.
heads = [(m.group(1), m.group(2), m.start(), m.end())
         for m in re.finditer(r"^### ([A-Z]\.\d)\s*[—-]\s*(.+?)\s*$", rub, re.M)]
claims, sect = {}, {}
for idx, (ss, name, s, e) in enumerate(heads):
    nxt = heads[idx + 1][2] if idx + 1 < len(heads) else len(rub)
    body = rub[e:nxt]
    sect[ss] = body
    sm = re.search(r"\*\*Status:\*\*\s*\**\s*(GROUNDED|PARTIAL|UNGROUNDED)", body)
    claims[ss] = (name, sm.group(1) if sm else "?")

hdr = re.search(r"Spec version:\s*\**v?([\d.]+)\**.*?Active sub-signals:\s*\**(\d+)\**"
                r".*?Not yet scored:\s*\**(\d+)\**", rub)
rub_spec, rub_active, rub_unscored = (hdr.group(1), int(hdr.group(2)),
                                      int(hdr.group(3))) if hdr else ("?", -1, -1)

summary = {}
for lvl in ("GROUNDED", "PARTIAL", "UNGROUNDED"):
    sm = re.search(r"\|\s*" + lvl + r"\s*\|\s*(\d+)\s*\|", rub)
    if sm:
        summary[lvl] = int(sm.group(1))

unscored = set()
ns = rub.find("## Not yet scored")
if ns > 0:
    for m in re.finditer(r"^\|\s*([A-Z]\.\d)\s*\|", rub[ns:ns + 2500], re.M):
        unscored.add(m.group(1))

# ── Parse the engine ──────────────────────────────────────────────────────
assigned = set(re.findall(r'scores\["([A-Z]\.\d)"\]\s*=', eng))
CONST_SRC = set(re.findall(r'INDUSTRY_DERIVED\.add\("([^"]+)"\)', eng))
ABSENT = set(re.findall(r'ABSENCE_DERIVED\.add\("([^"]+)"\)', eng))
em = re.search(r'"spec_version":\s*"([\d.]+)"', eng)
eng_spec = em.group(1) if em else "?"

# ── Measured reality ──────────────────────────────────────────────────────
vals, dim_of, allvals = defaultdict(dict), {}, defaultdict(list)
for i, r in enumerate(rows):
    for dim, blk in (r.get("genome") or {}).items():
        for k, v in ((blk or {}).get("scores") or {}).items():
            if isinstance(v, (int, float)):
                dim_of[k] = dim
                allvals[k].append(v)
                if v != NEUTRAL:
                    vals[k][i] = v

present = set(dim_of)

# The off-lattice proxy: how many published values are NOT one of the fallback integers.
offlat, lattices = {}, {}
for ss, tname in TABLES.items():
    tbl = grab_dict(tname)
    if tbl is None:
        continue
    lat = {v for v in tbl.values() if isinstance(v, (int, float))}
    lattices[ss] = (tname, lat)
    offlat[ss] = sum(1 for v in allvals.get(ss, []) if v not in lat)


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    ma, mb = st.mean(ra), st.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


twin = {}
bydim = defaultdict(list)
for k in vals:
    bydim[dim_of[k]].append(k)
for d, ks in bydim.items():
    for i, a in enumerate(sorted(ks)):
        for b in sorted(ks)[i + 1:]:
            both = sorted(set(vals[a]) & set(vals[b]))
            if len(both) < MIN_N:
                continue
            rho = spearman([vals[a][c] for c in both], [vals[b][c] for c in both])
            for x, y in ((a, b), (b, a)):
                if x not in twin or abs(rho) > abs(twin[x][0]):
                    twin[x] = (rho, y, len(both))

# ── PART 1: the RUBRIC against itself ─────────────────────────────────────
bugs = []
print("1. THE RUBRIC AGAINST ITSELF")
print(f"   header: spec v{rub_spec} · {rub_active} active · {rub_unscored} not scored")
print(f"   summary table: " + " · ".join(f"{k} {v}" for k, v in summary.items())
      + f"  = {sum(summary.values())}")
if summary and sum(summary.values()) != rub_active:
    bugs.append(f"summary table totals {sum(summary.values())}, header says {rub_active} active")
    print(f"   XX totals disagree with the header")
print(f"   sections found: {len(claims)}  ({', '.join(sorted(claims))})")
if len(claims) != rub_active:
    bugs.append(f"{len(claims)} sub-signal sections, header claims {rub_active} active")
    print(f"   XX section count disagrees with the header")
if len(unscored) != rub_unscored:
    bugs.append(f"{len(unscored)} not-yet-scored rows, header claims {rub_unscored}")
    print(f"   XX not-yet-scored rows ({len(unscored)}) disagree with the header")

no_status = sorted(k for k, (_, s) in claims.items() if s == "?")
if no_status:
    bugs.append(f"no parseable Status line: {', '.join(no_status)}")
    print(f"   XX no parseable **Status:** line: {', '.join(no_status)}")

# Every section must carry its coverage line. Checked INSIDE each section's own slice.
no_cov = sorted(k for k in claims if COVERAGE_TAG not in sect[k])
print(f"\n   sections carrying a '{COVERAGE_TAG}' line: "
      f"{len(claims) - len(no_cov)} of {len(claims)}")
if no_cov:
    bugs.append(f"no coverage line: {', '.join(no_cov)}")
    print(f"   XX missing it: {', '.join(no_cov)}")
    print("      A status word with no coverage beside it is the defect the October audit")
    print("      found: one word cannot describe a sub-signal that is authoritative for a")
    print("      tenth of companies and a constant for the other nine tenths.")

print(f"\n   RUBRIC spec v{rub_spec} · engine spec {eng_spec}")
if rub_spec != eng_spec:
    bugs.append(f"RUBRIC says spec v{rub_spec}, engine says {eng_spec}")
    print("   XX the document and the engine name different specs")

# ── PART 2: claims vs code ────────────────────────────────────────────────
print("\n2. THE RUBRIC AGAINST THE CODE")
retired = [k for k in claims if k not in assigned]
undoc = [k for k in sorted(assigned) if k not in claims and k not in unscored]
scored_but_listed_unscored = [k for k in unscored if k in assigned]

# Runtime test, not a grep. See the docstring: the `.add()` is inside a branch.
#
# Three outcomes, not two. A sub-signal whose fallback is INLINE has no lattice to test
# against, and an absent test is NOT a pass — that is the same error this script was
# rewritten to stop making, one level up. A.1 is the case: it reaches INDUSTRY_DERIVED
# from an inline branch with no named dict, so it is UNPROVEN and says so, rather than
# being counted among the measured because nothing contradicted it.
UNTESTABLE = sorted(k for k in CONST_SRC if k not in offlat)
overstated, cleared, unproven = [], [], []
for k in claims:
    if k not in CONST_SRC or claims[k][1] not in ("PARTIAL", "GROUNDED"):
        continue
    if k not in offlat:
        unproven.append(k)
    else:
        (cleared if offlat[k] >= MIN_N else overstated).append(k)

for label, items, why in (
    ("documented as active, engine never assigns it", retired,
     "retired in code, still described as live"),
    ("engine assigns it, RUBRIC does not document it", undoc, "undocumented signal"),
    ("**OVERSTATED GROUNDING** — PARTIAL/GROUNDED but the values are on the fallback lattice",
     overstated, "the document claims an authoritative input where the values are constants"),
    ("**UNPROVEN** — PARTIAL/GROUNDED, falls back to an inline constant, no lattice to test",
     unproven, "the claim cannot be checked by this proxy and is not assumed true"),
    ("listed 'not yet scored' but the engine scores it", scored_but_listed_unscored,
     "understated"),
):
    print(f"\n   {label}: {len(items)}")
    for k in sorted(items):
        nm = claims.get(k, ("—", "—"))
        extra = f"  off-lattice n={offlat[k]}" if k in offlat else ""
        print(f"      {k:5} {nm[0][:34]:34} RUBRIC={nm[1]:11} — {why}{extra}")
        bugs.append(f"{k}: {why}")
    if not items:
        print("      none")

if cleared:
    print(f"\n   NOT a bug, though a grep would say so — PARTIAL/GROUNDED with an")
    print(f"   `INDUSTRY_DERIVED.add()` in source, but enough off-lattice values to show the")
    print(f"   measured branch really fires:")
    for k in sorted(cleared):
        tname, lat = lattices[k]
        n = len(allvals.get(k, []))
        print(f"      {k:5} RUBRIC={claims[k][1]:11} off-lattice {offlat[k]:>4} of {n:,}"
              f"   (fallback: {tname})")
    print("      The previous version of this script reported these as the project's worst")
    print("      over-claims. They were not. Proxy, not proof — see the docstring.")

if UNTESTABLE:
    print(f"\n   NOT TESTABLE by the off-lattice proxy — the fallback is inline, with no named")
    print(f"   dict to recover: {', '.join(UNTESTABLE)}")
    print("      These are excluded from the baseline count below. An untested claim is not")
    print("      a cleared one. To make them testable, lift the inline fallback into a named")
    print("      dict, or publish `derived_signals` per row and stop estimating altogether.")

# ── PART 3: the master inventory ──────────────────────────────────────────
print("\n3. MASTER INVENTORY")
print(f"   {'ss':5} {'RUBRIC':11} {'engine':16} {'n':>5} {'%univ':>6} {'twin':>22} verdict")
print("   " + "─" * 94)
allss = sorted(set(claims) | present | unscored)
holes = []
for k in allss:
    name, status = claims.get(k, ("(undocumented)", "—"))
    n = len(vals.get(k, {}))
    pct = 100 * n / len(rows)
    if k in UNTESTABLE:
        treat = "inline fallback"
    elif k in CONST_SRC:
        treat = ("mostly constant" if offlat[k] < MIN_N
                 else f"part measured ({offlat[k]})")
    elif k not in assigned:
        treat = "not in engine"
    elif k in ABSENT:
        treat = "measured/absence"
    else:
        treat = "measured"
    tw = ""
    if k in twin:
        rho, y, tn = twin[k]
        tw = f"{y} {rho:+.2f} (n={tn})"
    verdict = []
    if k in UNTESTABLE:
        verdict.append("UNPROVEN")
    elif k in CONST_SRC and offlat[k] < MIN_N:
        verdict.append("CONSTANT")
    if k not in assigned and k not in unscored:
        verdict.append("RETIRED")
    if k in unscored:
        verdict.append("not scored")
    if k in assigned and k not in UNTESTABLE and not (k in CONST_SRC and offlat[k] < MIN_N):
        eff = offlat.get(k, n)
        if eff == 0:
            verdict.append("DEAD")
        elif eff < MIN_N:
            verdict.append("THIN")
    if k in twin and abs(twin[k][0]) >= 0.85:
        verdict.append("REDUNDANT")
    if not verdict:
        verdict.append("ok")
    v = ",".join(verdict)
    print(f"   {k:5} {status:11} {treat:16} {n:>5} {pct:>5.1f}% {tw:>22} {v}")
    if v != "ok":
        holes.append((k, name, v, n, pct))

# ── PART 4: the work list ─────────────────────────────────────────────────
print("\n4. THE HOLES, by how much of the universe they touch")
print(f"   {'ss':5} {'n':>5} {'%univ':>6} {'problem':24} name")
print("   " + "─" * 78)
for k, name, v, n, pct in sorted(holes, key=lambda h: -h[4]):
    print(f"   {k:5} {n:>5} {pct:>5.1f}% {v:24} {name[:30]}")

real = [k for k in allss
        if k in assigned
        and k not in UNTESTABLE
        and not (k in CONST_SRC and offlat[k] < MIN_N)
        and max(len(vals.get(k, {})), offlat.get(k, 0)) >= MIN_N
        and not (k in twin and abs(twin[k][0]) >= 0.85)]
red_pairs = sorted({tuple(sorted((k, twin[k][1]))) for k in allss
                    if k in twin and abs(twin[k][0]) >= 0.85})
print(f"\n   Measured, not a constant, above {MIN_N} companies, not redundant with a")
print(f"   same-dimension partner, and testable: **{len(real)}** — {', '.join(real)}")
for a, b in red_pairs:
    print(f"   Plus {a}/{b}, which rank alike and count as ONE: +1")
print(f"   Honest baseline: **{len(real) + len(red_pairs)} real sub-signals**. "
      f"The RUBRIC header claims {rub_active} active.")
if UNTESTABLE:
    print(f"   Not counted either way: {', '.join(UNTESTABLE)} — inline fallback, UNPROVEN.")
    print(f"   The count is a floor. It rises only when one of those is shown to measure")
    print(f"   something, not when nothing contradicts it.")

print(f"\n5. RUBRIC BUGS FOUND: {len(bugs)}")
for b in bugs:
    print(f"   · {b}")
if not bugs:
    print("   none — the document and the engine agree on every mechanical check.")
print("\n   By the RUBRIC's own rule — 'where this file and the code disagree, the code is")
print("   right and this file is a bug' — each line above is a documentation defect.")
print("\n   What this cannot judge: whether an authoritative source measures the construct")
print("   each sub-signal claims. That is the v1.9.0 test and it needs a human reading the")
print("   source's methodology. The list above says which ones are worth that time.")
print("\nNothing changed. Read-only.")
