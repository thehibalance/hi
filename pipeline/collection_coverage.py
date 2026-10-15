#!/usr/bin/env python3
"""How fast does a change actually reach production? Read-only. From pipeline/:

    python3 collection_coverage.py

WHY THIS EXISTS

Three predictions this week were right about the fix and wrong about the day:

  · PR #39 changed `score_land`, a SUB-SIGNAL scorer. Checked the next morning, found
    nothing, concluded the patch had failed. It had not.
  · PR #40 changed the engine's own `sources_used` appends. 298 rows went to 1 in a single
    nightly, because scoring runs on every row every night.
  · PR #41's effect was checked against feature files that had not been regenerated.

The pipeline has TWO propagation speeds and nothing wrote them down:

    scoring_engine.py       runs on every row, every night        -> lands in ONE NIGHT
    subsignal_pipelines.py  runs inside collection, budget-capped -> lands over DAYS

The second horizon is set by whichever external quota binds first. The workflow names it:
`HI_COLLECT_BUDGET_MIN: '150'`, and in its own comments, the **FMP free tier at 250
calls/day**. Against 1,139 companies that is roughly five nights to cycle the universe.

So "it will be visible after the next nightly" is false for anything touching a sub-signal
scorer, and that sentence cost three days of chasing fixes that were already correct.

This script turns the horizon into an output. It also catches a stalled collector as a
number rather than as a surprise: the EPA store was 26 records last fetched 2026-04-14,
six months dead, and nothing reported it until someone happened to look.

WHAT IT MEASURES

For every collector store, when its records were last retrieved — so the report says how
many companies each source reached recently, how long that implies for a full cycle, and
which collectors have stopped entirely.

WHAT IT CANNOT MEASURE

Whether a company was SKIPPED as fresh or MISSED because the budget ran out. Both leave the
same trace: an old `retrieved` date. Separating them needs the pipeline log, which this does
not read. So a slow cycle here means "slow", not necessarily "starved".
"""
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATE_KEYS = ["retrieved", "fetched", "as_of", "collected", "updated", "timestamp", "date"]
UNIVERSE = 1139          # reported by the nightly commit message

if not Path("data").is_dir():
    raise SystemExit("  no data/ — run from pipeline/")


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=15).stdout.strip()
    except Exception:
        return "?"


now = datetime.now(timezone.utc)
print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}")
print(f"as of {now:%Y-%m-%d %H:%M} UTC\n")


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


def dig(node, depth=0, path=""):
    """First parseable date under any of DATE_KEYS, anywhere in the record.

    Returns (date, where-it-came-from). The second half matters: a recursive search
    finds *a* date, not necessarily a RETRIEVAL date. If a store has no `retrieved`
    stamp but its payload carries a filing date, this would happily report a 2024
    10-K date as the collector's freshness. So every number below is printed next to
    the field it came from, and a key that is not a retrieval stamp is visible as a
    key rather than believed as a date. That is the whole guard.
    """
    if depth > 4:
        return None
    if isinstance(node, dict):
        for k in DATE_KEYS:
            if k in node:
                d = parse(node[k])
                if d:
                    return d, (f"{path}.{k}" if path else k)
        for k, v in node.items():
            r = dig(v, depth + 1, f"{path}.{k}" if path else str(k))
            if r:
                return r
    elif isinstance(node, list):
        for v in node[:50]:
            r = dig(v, depth + 1, f"{path}[]")
            if r:
                return r
    return None


rows = []
for d in sorted(Path("data").iterdir()):
    f = d / "all_companies.json"
    if not f.is_file():
        continue
    try:
        raw = json.load(open(f))
    except Exception:
        print(f"  {d.name:22} !! unreadable")
        continue
    recs = [r for r in (raw if isinstance(raw, list) else list(raw.values()))
            if isinstance(r, dict)]
    if not recs:
        rows.append((d.name, 0, 0, 0, 0, None, None, 0, ""))
        continue
    hits = [dig(r) for r in recs]
    dated = [h[0] for h in hits if h]
    keys = Counter(h[1] for h in hits if h)
    errs = sum(1 for r in recs if r.get("error"))
    d1 = sum(1 for x in dated if (now - x).days < 1)
    d7 = sum(1 for x in dated if (now - x).days < 7)
    rows.append((d.name, len(recs), errs, d1, d7,
                 min(dated) if dated else None, max(dated) if dated else None,
                 len(dated), keys.most_common(1)[0][0] if keys else ""))

print("COLLECTOR FRESHNESS — when each store's records were last retrieved\n")
print(f"  {'collector':20} {'recs':>6} {'errs':>5} {'<24h':>6} {'<7d':>6} "
      f"{'newest':>12} {'age':>6} {'cycle':>6}  date field")
print("  " + "─" * 100)

stalled, undated, cycles, oddkeys = [], [], [], []
for name, n, errs, d1, d7, oldest, newest, ndated, key in rows:
    if n == 0:
        print(f"  {name:20} {'empty':>6}")
        continue
    if not ndated:
        undated.append(name)
        print(f"  {name:20} {n:>6} {errs:>5} {'—':>6} {'—':>6} {'no date field':>12}")
        continue
    if key not in ("retrieved", "fetched", "collected"):
        oddkeys.append((name, key))
    age = (now - newest).days
    # days to cycle this store at last night's observed rate
    cyc = f"{n / d1:.1f}d" if d1 else "—"
    if d1:
        cycles.append((n / d1, name))
    flag = ""
    if age > 7:
        flag = "  <- STALLED"
        stalled.append((name, age, n, errs))
    elif errs == n:
        flag = "  <- all errors"
    stamp = f"{newest:%Y-%m-%d}"
    print(f"  {name:20} {n:>6} {errs:>5} {d1:>6} {d7:>6} "
          f"{stamp:>12} {age:>5}d {cyc:>6}  {key}{flag}")

if oddkeys:
    print(f"\n  READ THESE ROWS WITH SUSPICION — **{len(oddkeys)}** store(s) have no")
    print("  retrieval stamp, so the date above is whatever date the payload happened to")
    print("  carry. That is not freshness, and the number is not evidence:")
    for name, key in oddkeys:
        print(f"      {name:20} dated by `{key}`")

if undated:
    print(f"\n  No date field found in: {', '.join(undated)}")
    print("  Those stores cannot report freshness. A collector that does not record when")
    print("  it ran cannot be shown to be running — worth adding a `retrieved` stamp.")

if stalled:
    print(f"\nSTALLED COLLECTORS — newest record older than 7 days: **{len(stalled)}**")
    for name, age, n, errs in sorted(stalled, key=lambda s: -s[1]):
        note = " (every record an error)" if errs == n else ""
        print(f"  {name:20} {age:>4}d old · {n} records · {errs} errors{note}")
    print("\n  A stalled collector is still listed as a source. The EPA store sat at 26")
    print("  records, all errors, for six months and nothing reported it. This is that")
    print("  check, so the next one surfaces as a number instead of a discovery.")

# ── The open prediction ──────────────────────────────────────────────────
# PR #40 removed "Industry+EPA" from the engine on 2026-10-12. The scoring path
# cleared in one night: 298 rows -> 1. The SUB-SIGNAL store did not, because it is
# rewritten per company as each company is re-collected — the five-day horizon.
#
# This block exists so the prediction is settled by a number on a date instead of by
# memory. Note the shape of the guard: a store that cannot be found reports NOT FOUND,
# never "0 hits". Zero hits in a file that does not exist is exactly this project's
# signature defect — a failure recorded as a favourable fact — and it would read here
# as the prediction coming true.
print("\n\nOPEN PREDICTION — does \"Industry+EPA\" clear on the sub-signal horizon?\n")
PR40 = datetime(2026, 10, 12, tzinfo=timezone.utc)
print(f"  PR #40 merged {PR40:%Y-%m-%d} · {(now - PR40).days} nights since\n")
for label, path, at_merge in (
        ("scored rows", "data/scores/all_scores.json", 298),
        ("sub-signal store", "data/subsignals/all_subsignals.json", 300)):
    p = Path(path)
    if not p.is_file():
        print(f"  {label:18} NOT FOUND at {path} — this check did not run.")
        print("                     (A path that does not resolve is not a clean result.)")
        continue
    hits = p.read_text(errors="replace").count("Industry+EPA")
    verdict = ("cleared" if hits == 0 else
               f"{hits} remaining of {at_merge} at merge")
    print(f"  {label:18} {hits:>5} hits   {verdict}")

print("\n  Expected: scored rows cleared the night after merge. The sub-signal store")
print("  drains as companies are re-collected, so it should reach zero within about a")
print("  week, and `get_contributing_sources()` should go 21 -> 20 when it does.")
print("\n  IF THE SUB-SIGNAL STORE HAS NOT MOVED IN A WEEK, the horizon is not the")
print("  explanation: data_collector._merge_save() is the third in-place store and the")
print("  only one without the v1.8.0 retirement guard, so it would be re-seeding a value")
print("  nothing re-earned. That is the fix, and this is how its cost gets measured.")

# ── The two horizons ─────────────────────────────────────────────────────
print("\n\nPROPAGATION HORIZONS — when a code change actually reaches production\n")
print("  scoring_engine.py       every row, every night        ->  ONE NIGHT")
if cycles:
    worst, worst_name = max(cycles)
    med = sorted(c for c, _ in cycles)[len(cycles) // 2]
    print(f"  subsignal_pipelines.py  runs inside collection        ->  "
          f"~{med:.0f}-{worst:.0f} DAYS")
    print(f"\n  Slowest store to cycle at last night's rate: {worst_name} "
          f"at {worst:.1f} days.")
    print(f"  Median across stores: {med:.1f} days.")
else:
    print("  subsignal_pipelines.py  runs inside collection        ->  cannot tell:")
    print("     no store recorded a retrieval in the last 24 hours. Either the nightly")
    print("     did not collect, or no store stamps its records.")

print("\n  The binding constraint is an external quota, not the pipeline. The workflow")
print("  comments name it: the FMP free tier at 250 calls/day, with")
print("  HI_COLLECT_BUDGET_MIN at 150 minutes. Against "
      f"{UNIVERSE:,} companies that is the floor on how")
print("  fast any sub-signal change can land.")

print("\nHOW TO USE THIS WHEN PREDICTING A CHANGE\n")
print("  Changed scoring_engine.py?      check tomorrow morning.")
print("  Changed a sub-signal scorer?    check in a week, and expect a mixture until then.")
print("  Changed a feature pipeline?     check after the features step rewrites its file,")
print("                                  which is not the same as the next nightly.")
print("\n  Saying 'it will be visible after the next nightly' is false for two of those")
print("  three, and that sentence cost three days this week of chasing fixes that were")
print("  already correct. A rate limit is not a refresh interval: the --incremental")
print("  threshold decides who is ELIGIBLE to be re-collected, the budget decides how")
print("  many actually ARE.")
print("\nNothing changed. Read-only.")
