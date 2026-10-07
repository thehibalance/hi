#!/usr/bin/env python3
"""Morning check — v1.12.0 (spec 1.11.0). Read-only. From pipeline/:

    python3 verify_nightly.py

Two kinds of line, kept visibly apart:

  ASSERT  a structural rule the methodology states, which cannot drift as the universe
          changes night to night. A mismatch is a defect.
  REPORT  a count or a distribution. Printed with its expected value beside it, never
          graded, because the company universe changes and an exact-count assertion
          would cry wolf.

WHY THE SPLIT MOVED FOR H.3

v1.12.0 made H.3 absence-derived when `rpe and _med_ok` is false. The obvious test —
"H.1 == 50 implies H.3 == 50" — is NOT a valid invariant: H.1 has four branches, and
lines 894 and 900 can set it away from 50 while the RPE input is still missing. That is
exactly why the pre-ship detector found 344 and production moved 352. So H.3 is reported
with its expected count, not asserted. An assertion that can be wrong for a legitimate
reason trains you to ignore it.

HISTORY — this script's own failures, worth keeping

  Oct 2, seven failures: four were a working copy on a merged feature branch three
  commits behind main, so it measured v1.10.0 and complained v1.11.0 was missing. Hence
  the branch/HEAD/behind header, printed before anything else.

  The other three were assertions encoding rules the project never adopted: "no row
  carries N.5" (the 94 hand-scored seed rows legitimately do), "every M.3 equals 50"
  (v1.11.0 made it absence-derived only where the litigation value is zero), and
  "D_N == N.2 exactly" (ignores algo_harm, which penalises H, U, M and N).
"""
import json
import re
import statistics as st
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

SPEC = "1.11.0"
COV_DENOM = 18
fails = []


def assert_(label, got, want, note=""):
    ok = got == want
    print(f"  {'OK  ' if ok else 'XX  '}{label:38} {str(got):>10}  expect {want}"
          + (f"   {note}" if note else ""))
    if not ok:
        fails.append(f"{label}: got {got}, expect {want}")


def rep(label, got, expect, note=""):
    print(f"  {label:34} {str(got):>8}      (expect ~{expect})" + (f"  {note}" if note else ""))


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return "?"


branch = git("rev-parse", "--abbrev-ref", "HEAD")
print(f"branch {branch} · HEAD {git('log', '-1', '--format=%h %cr  %s')}")
if branch != "main":
    print("  !! not on main. The nightly commits to main:"
          "  git checkout main && git pull --ff-only")
behind = git("rev-list", "--count", "HEAD..origin/main")
if behind not in ("0", "", "?"):
    print(f"  !! {behind} commit(s) behind origin/main — pull before trusting anything below")

p = Path("data/scores/all_scores.json")
if not p.exists():
    raise SystemExit("  no data/scores/all_scores.json — run from pipeline/")
rows = [r for r in json.load(open(p)) if not r.get("error")]
age = datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)
print(f"all_scores.json written {age.days}d {age.seconds // 3600}h ago · {len(rows)} companies")

# Has the engine moved since these scores were published?
#
# File mtime cannot answer this — a git checkout rewrites it, so a freshly pulled file
# holding week-old content looks minutes old. The Oct 6 run reported two spec failures
# that were nothing but this: HEAD was PR #33's merge commit, no nightly had run since,
# and the scores on disk were the previous version's output. Both facts were in the
# header and neither was connected to the other.
#
# This is the project's own fossil rule aimed at the repo: a cache may not outlive its
# source, and the engine is the source.
eng_t = git("log", "-1", "--format=%ct", "--", "scoring_engine.py")
sc_t = git("log", "-1", "--format=%ct", "--", "data/scores/all_scores.json")
if eng_t.isdigit() and sc_t.isdigit():
    if int(eng_t) > int(sc_t):
        d = (int(eng_t) - int(sc_t)) / 3600
        print(f"  !! THE ENGINE IS NEWER THAN THESE SCORES by {d:.0f}h.")
        print(f"     Last commit to scoring_engine.py:        "
              f"{git('log', '-1', '--format=%h %cr  %s', '--', 'scoring_engine.py')[:72]}")
        print(f"     Last commit to data/scores/all_scores.json: "
              f"{git('log', '-1', '--format=%h %cr', '--', 'data/scores/all_scores.json')}")
        print("     No nightly has published since the engine changed, so every spec and")
        print("     count assertion below describes the PREVIOUS version. That is staleness,")
        print("     not a defect. Wait for the nightly:  gh run list --limit 5")
    else:
        print(f"  engine last changed {git('log', '-1', '--format=%cr', '--', 'scoring_engine.py')}"
              f", scores published after it — these numbers describe the current code")
elif age.days >= 1:
    print("  !! over a day old and the git check was inconclusive. Confirm the working copy\n"
          "     is current, then:  gh run list --limit 5")
print()

pipe = [r for r in rows if r.get("spec_version")]
seed = [r for r in rows if not r.get("spec_version")]
idx = {r["ticker"]: r for r in rows if r.get("ticker")}
gen = lambda r, d: ((r.get("genome") or {}).get(d) or {}).get("scores", {})
print(f"{len(pipe)} pipeline rows · {len(seed)} hand-scored seed rows (engine never touches\n"
      f"them; every assertion is scoped to pipeline rows)\n")

# ── ASSERT — structural ───────────────────────────────────────────────────
print("ASSERT — structural rules")
specs = Counter(r.get("spec_version") for r in pipe)
assert_("pipeline rows at current spec", specs.get(SPEC, 0), len(pipe), f"{dict(specs)}")

n5 = [r["ticker"] for r in pipe if "N.5" in gen(r, "N")]
assert_("pipeline rows carrying N.5", len(n5), 0, f"{n5[:5]}" if n5 else "v1.11.0")

denoms = Counter()
cov = []
for r in pipe:
    m = re.match(r"(\d+)\s*/\s*(\d+)", str(r.get("signal_coverage") or ""))
    if m:
        cov.append(int(m.group(1)))
        denoms[int(m.group(2))] += 1
assert_("rows with a stale /19 denominator",
        sum(v for k, v in denoms.items() if k != COV_DENOM), 0, f"{dict(denoms)}")

bad_dn, harmed = [], 0
for r in pipe:
    n2, dn = gen(r, "N").get("N.2"), r.get("D_N")
    if n2 is None or dn is None:
        continue
    pen = ((r.get("algo_harm") or {}).get("penalties") or {}).get("N") or 0
    harmed += 1 if pen else 0
    if abs(dn - (n2 + pen)) > 1.01:
        bad_dn.append(f"{r['ticker']} D_N={dn} N.2={n2} pen={pen}")
assert_("rows where D_N != N.2 + algo_harm", len(bad_dn), 0,
        f"{harmed} carry a penalty")
for b in bad_dn[:6]:
    print(f"        !! {b}")

# H.3: there is NO valid published invariant, and this script asserted one anyway.
#
# The docstring above says it outright — "H.1 == 50 implies H.3 == 50" is not valid,
# because H.1's branches at 894 and 900 can land on 50 while RPE is present. A test for
# "H.1 == 50 and H.3 on the no-RPE lattice" is the same claim wearing a hat, and the Oct 6
# production run failed it on PRU, AFL and GL: three insurers with a credible finance RPE
# median, whose legitimately MEASURED H.3 happens to land on an integer the no-RPE path
# could also have produced. Three false positives in 1,045 rows.
#
# Nothing in the published row says which path H.3 took, so the honest test is the count,
# which is reported below and hit 635 exactly. Asserting what the data cannot settle
# teaches you to skip the whole report.
LATTICE_ABOVE = {52, 53, 55, 57, 58, 60, 63, 65, 68, 70, 73, 75}
coincident = [r["ticker"] for r in pipe
              if gen(r, "H").get("H.1") == 50 and gen(r, "H").get("H.3") in LATTICE_ABOVE]

print("\nASSERT — v1.11.1, the twelve fossils")
TWELVE = "COLB ZION UPST HWC ONB PNFP PB SSB TCBI VLY APPF VRSK".split()
bad = [t for t in TWELVE
       if t not in idx or gen(idx[t], "U").get("U.1") != 50]
assert_("twelve fossils at U.1 50", len(bad), 0, f"{bad}" if bad else "")

a = Path("data/subsignals/all_subsignals.json")
if a.exists():
    agg = json.load(open(a))
    assert_("cfpb blocks in the aggregate",
            sum(1 for v in agg.values() if isinstance(v, dict) and "cfpb" in v), 27,
            "a cache may not outlive its source")
assert_("rows with cfpb_disclosure", sum(1 for r in rows if r.get("cfpb_disclosure")), 27)
dupes = Counter(r["ticker"] for r in rows if r.get("ticker"))
assert_("duplicate tickers", sum(1 for v in dupes.values() if v > 1), 0)

# ── REPORT ────────────────────────────────────────────────────────────────
print("\nREPORT — counts, printed not graded (the universe changes nightly)")
h3 = [gen(r, "H").get("H.3") for r in pipe if isinstance(gen(r, "H").get("H.3"), (int, float))]
rep("H.3 values not 50", sum(1 for v in h3 if v != 50), 635,
    "was 987 before v1.12.0")
rep("H.1 50 + H.3 on old lattice", len(coincident), "a few",
    f"{coincident[:5]} — coincidence, not a defect; see the note in the source")
rep("rows at zero coverage", sum(1 for c in cov if c == 0), 270, "was 38")
rep("coverage median", f"{int(st.median(cov)) if cov else '?'}/{COV_DENOM}", f"2/{COV_DENOM}")
rep("coverage mean", f"{st.mean(cov):.2f}" if cov else "?", "2.33", "was 2.66")

comps = [r["composite"] for r in rows if isinstance(r.get("composite"), (int, float))]
pc = [r["composite"] for r in pipe if isinstance(r.get("composite"), (int, float))]
rep("composite median, all rows", int(st.median(comps)), 50, "was 51")
rep("stdev, all rows", f"{st.pstdev(comps):.1f}", "6.3")
rep("stdev, pipeline rows only", f"{st.pstdev(pc):.1f}", "3.6",
    "the gap is the seed rows")
rep("rows at exactly 50", sum(1 for c in comps if c == 50), 266, "was 224")
rep("floor-triggered", sum(1 for r in rows if r.get("floor_triggered")), 182, "was 177")

m3 = [gen(r, "M").get("M.3") for r in pipe if "M.3" in gen(r, "M")]
print(f"\n  M.3: {len(m3)} pipeline rows, {sum(1 for v in m3 if v != 50)} not 50 — a non-50"
      f" means a\n       NONZERO litigation disclosure, which is a real measurement.")

ah = [r for r in rows if (r.get("algo_harm") or {}).get("has_harm")]
if ah:
    print(f"\n  algo_harm: {len(ah)} companies — HW.1 is wired to the score. Largest:")
    for r in sorted(ah, key=lambda x: -(x["algo_harm"].get("algo_harm_score") or 0))[:4]:
        pen = r["algo_harm"].get("penalties") or {}
        print(f"    {(r.get('ticker') or '?'):6} harm "
              f"{r['algo_harm'].get('algo_harm_score'):>5.1f}  "
              f"~{sum(pen.get(k) or 0 for k in 'HUMN') / 5:>5.1f} composite")
    print("  Components and flags are hand-authored — the largest single adjustment")
    print("  in the system after the floor rule, and it is editorial.")

print()
if fails:
    print(f"{len(fails)} ASSERTION(S) FAILED")
    for f in fails:
        print(f"  · {f}")
    raise SystemExit(1)
print("All assertions passed.  Then: python3 check_continuity.py | tail -4")
