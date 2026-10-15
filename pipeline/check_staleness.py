#!/usr/bin/env python3
"""A gate: fail the nightly when a collector goes quiet. Read-only. From pipeline/:

    python3 check_staleness.py          # exit 0 = ok, 1 = something needs a human

WHY THIS EXISTS

Four collectors stopped on 2026-04-14 and nothing reported it for 183 days:

    cdp        35 records   0 errors    2026-04-14
    epa        26 records  26 errors    2026-04-14
    glassdoor  43 records   0 errors    2026-04-14
    jobs       37 records   0 errors    2026-04-14

Three of the four are published in `get_contributing_sources()`'s list of 21 contributing
sources, with zero errors and six-month-old data. Every health check in the repo passed
them, because `audit_surface_area.py` flags a store only when `errors == len(records)` —
a rule about error rate, against a defect about time.

This is that missing check. Four collectors at 183 days should have been a red build in
April, not a discovery in October.

WHY IT IS A GATE AND NOT A REPORT

`collection_coverage.py` reports freshness and is allowed to be generous: it will dig a
date out of anywhere in a record and then warn you that the field it found was not a
retrieval stamp. That is right for a report and WRONG for a gate. A gate that accepts a
10-K filing date as evidence of freshness would pass a dead collector forever.

So this script accepts only STAMP_KEYS — fields that mean "we fetched this, then". An
unrecognised date is not freshness, it is no stamp, and the store is reported as
unmeasurable rather than fresh. The two scripts disagree on purpose.

THE EXEMPTION LIST HAS TO STAY HONEST

The four known-stale collectors are declared in KNOWN_STALE below so that NEW stalls fail
while the known ones stay visible. An exemption list with no expiry is the same defect in
a new costume, so:

  · a declared store that is still stale  -> reported, exit 0, with its age growing
  · a declared store that has RECOVERED   -> **exit 1**, telling you to delete the entry

That second one fails in the right direction. A fixed collector should not be able to
leave a lie behind in the exemption list.

WHAT IT CANNOT SEE

15 of 22 stores carry no retrieval stamp at all. This gate cannot check them and does not
pretend to: it prints its own coverage on every run. A check that does not state its
denominator is how the first four died.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fields that mean "this record was fetched at this time". Nothing else counts.
STAMP_KEYS = ("retrieved", "fetched", "collected")

MAX_AGE_DAYS = int(os.environ.get("HI_MAX_STORE_AGE_DAYS", "7"))

# Declared stale, with the date each one stopped. See
# claude/FINDING-four-collectors-died-on-the-same-day.md and
# claude/FINDING-the-april-stall-and-the-untracked-keys.md
# Delete an entry the day its collector is fixed — this script will tell you to.
KNOWN_STALE = {
    "cdp":       "2026-04-14",
    "epa":       "2026-04-14",
    "glassdoor": "2026-04-14",
    "jobs":      "2026-04-14",
}

# Stores with no stamp as of 2026-10-14. A NEW unstamped store is a regression: it means
# a collector was added without recording when it ran, which is how a stall hides.
KNOWN_UNSTAMPED = {
    "bcorp", "ceo", "climate_neutral", "dei", "fairtrade", "finnhub", "fmp", "harm",
    "hrc", "newsapi", "one_percent", "sec", "sec_8k", "usda_organic", "yahoo",
}

# The workflow runs some steps from the repo root and some from pipeline/, so resolve
# the store directory rather than assuming the cwd. A gate that only works from one
# directory is a gate that silently does not run from the other.
DATA = Path("data")
if not DATA.is_dir():
    DATA = Path(__file__).resolve().parent / "data"
if not DATA.is_dir():
    raise SystemExit("  no data/ — looked in the cwd and beside this script")

now = datetime.now(timezone.utc)


def parse(v):
    if not isinstance(v, str):
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(v[:26], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except Exception:
        return None


def stamp(rec):
    """A retrieval time, or None. Top level only — a nested date is payload, not a stamp."""
    if not isinstance(rec, dict):
        return None
    for k in STAMP_KEYS:
        if k in rec:
            d = parse(rec[k])
            if d:
                return d
    return None


fresh, stale_new, stale_known, recovered, unstamped_new, unstamped_known, empty = (
    [], [], [], [], [], [], [])

for d in sorted(DATA.iterdir()):
    f = d / "all_companies.json"
    if not f.is_file():
        continue
    name = d.name
    try:
        raw = json.load(open(f))
    except Exception as e:
        stale_new.append((name, -1, 0, f"unreadable: {e}"))
        continue

    recs = [r for r in (raw if isinstance(raw, list) else list(raw.values()))
            if isinstance(r, dict)]
    if not recs:
        empty.append(name)
        continue

    stamps = [s for s in (stamp(r) for r in recs) if s]
    if not stamps:
        (unstamped_known if name in KNOWN_UNSTAMPED else unstamped_new).append(
            (name, len(recs)))
        continue

    newest = max(stamps)
    age = (now - newest).days
    errs = sum(1 for r in recs if r.get("error"))

    if age <= MAX_AGE_DAYS:
        if name in KNOWN_STALE:
            recovered.append((name, age, len(recs), KNOWN_STALE[name]))
        else:
            fresh.append((name, age, len(recs), errs))
    elif name in KNOWN_STALE:
        stale_known.append((name, age, len(recs), errs, KNOWN_STALE[name]))
    else:
        stale_new.append((name, age, len(recs), f"{errs} errors"))

checkable = len(fresh) + len(stale_new) + len(stale_known) + len(recovered)
total = checkable + len(unstamped_new) + len(unstamped_known) + len(empty)

print(f"STORE FRESHNESS GATE · {now:%Y-%m-%d %H:%M} UTC · "
      f"threshold {MAX_AGE_DAYS}d\n")
print(f"  this gate can check {checkable} of {total} stores. "
      f"{len(unstamped_new) + len(unstamped_known)} carry no retrieval stamp"
      f"{f', {len(empty)} empty' if empty else ''}.")
print("  Freshness is unknown for those, not good. A check that does not state its")
print("  denominator is how the first four stalls went unnoticed for six months.\n")

if fresh:
    print(f"  FRESH ({len(fresh)})")
    for name, age, n, errs in sorted(fresh):
        note = f" · {errs} errors" if errs else ""
        print(f"    {name:20} {age:>4}d  {n:>5} records{note}")

if stale_known:
    print(f"\n  STALE, DECLARED ({len(stale_known)}) — tracked, not failing the build")
    for name, age, n, errs, since in sorted(stale_known):
        note = " · every record an error" if errs == n else (
            f" · {errs} errors" if errs else "")
        print(f"    {name:20} {age:>4}d  {n:>5} records  stopped {since}{note}")

failures = []

if stale_new:
    print(f"\n  ** STALE, NEW ({len(stale_new)}) **")
    for name, age, n, extra in sorted(stale_new):
        agetxt = "unreadable" if age < 0 else f"{age}d"
        print(f"    {name:20} {agetxt:>5}  {n:>5} records  {extra}")
    failures.append(
        f"{len(stale_new)} collector(s) went quiet and are not declared in KNOWN_STALE")

if recovered:
    print(f"\n  ** RECOVERED ({len(recovered)}) — delete these from KNOWN_STALE **")
    for name, age, n, since in sorted(recovered):
        print(f"    {name:20} {age:>4}d  {n:>5} records  was stale since {since}")
    print("\n    This is a good failure. The collector is fixed; the exemption list is")
    print("    now the only thing still claiming it is broken. An exemption with no")
    print("    expiry is the same defect in a new costume — remove the entry.")
    failures.append(f"{len(recovered)} collector(s) recovered; KNOWN_STALE is out of date")

if unstamped_new:
    print(f"\n  ** NO RETRIEVAL STAMP, NEW ({len(unstamped_new)}) **")
    for name, n in sorted(unstamped_new):
        print(f"    {name:20} {n:>5} records")
    print("\n    A collector added without a retrieval stamp cannot be shown to be")
    print("    running, so it cannot be shown to have stopped. Stamp it on write — see")
    print("    cfpb_pipeline.py:484, which writes `fetched` and reads it back at :464")
    print("    to decide whether to refetch. The stamp is only useful when something")
    print("    consults it.")
    failures.append(f"{len(unstamped_new)} new store(s) with no retrieval stamp")

if unstamped_known:
    print(f"\n  no stamp, known ({len(unstamped_known)}): "
          f"{', '.join(sorted(n for n, _ in unstamped_known))}")
if empty:
    print(f"  empty ({len(empty)}): {', '.join(sorted(empty))}")

print()
if failures:
    print("FAIL")
    for f_ in failures:
        print(f"  · {f_}")
    print("\n  Declare an intentional stall in KNOWN_STALE with the date it stopped, or")
    print("  fix the collector. Do not raise HI_MAX_STORE_AGE_DAYS to make this pass —")
    print("  that converts a measured failure into a favourable fact, which is the exact")
    print("  defect this project has spent a week removing.")
    sys.exit(1)

print("PASS — every checkable store is within the threshold or declared.")
print(f"  Still unmeasurable: {len(unstamped_known)} stores with no retrieval stamp.")
print("  This gate is worth what that number is low.")
sys.exit(0)
