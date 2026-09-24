#!/usr/bin/env python3
"""
Merge scores: keep every company the engine still produces, plus the ones it missed
tonight — but let fossils expire.

The old rule was "score count can only go UP, never down." That protected the site from
a collapsed run, and it also meant a row the engine stopped producing was published
forever at whatever spec it died at. Today that was four rows: BK and CTRA still carried
FDA evidence the project withdrew in v1.5.1 and CFPB matches from before the v1.5.0
rematch, frozen at spec 1.2.1 since March. Those two rows were the only reason "FDA"
still appeared in the public source list.

The rule now: a backup row survives only if it is hand-scored (seed data, no
spec_version) or still at the current spec. Anything older is a fossil — nothing
measured it tonight and it no longer matches the engine that scores everything else.
The anti-collapse guard stays: if expiring fossils would remove more than MAX_EXPIRY_PCT
of the file, that is a broken run, not a retirement, so nothing is dropped and the run
says so loudly.

Usage: python3 merge_scores.py backup.json fresh.json output.json
"""
import json
import os
import re
import sys

MAX_EXPIRY_PCT = 2.0

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from scoring_engine import canon_name
except Exception:                                    # pragma: no cover - fallback only
    def canon_name(name):
        return (name or "").lower().strip()


def current_spec():
    """Read the spec the engine stamps on rows it writes, so this file never drifts."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scoring_engine.py")
    try:
        m = re.search(r'"spec_version":\s*"([0-9.]+)"', open(p).read())
        return m.group(1) if m else None
    except OSError:
        return None


def key(c):
    """One key per company, the same spelling rule the engine uses. Keying on the raw
    name would let "BANK OF AMERICA CORP /DE/" and "Bank of America Corporation" both
    survive, which is the split canon_name() exists to end."""
    return canon_name(c.get("company", "")) or (c.get("company", "") or "").lower()


def merge(backup_path, fresh_path, output_path):
    backup = json.load(open(backup_path))
    fresh = json.load(open(fresh_path))
    spec = current_spec()

    fresh_by_key = {}
    for c in fresh:
        k = key(c)
        if k:
            fresh_by_key[k] = c

    carried, fossils = [], []
    for c in backup:
        k = key(c)
        if not k or k in fresh_by_key:
            continue
        v = c.get("spec_version")
        if v is None or v == spec:
            carried.append(c)                        # hand-scored, or missed this run
        else:
            fossils.append(c)

    if spec is None:
        print("  ! could not read the engine's spec_version — carrying every backup row")
        carried += fossils
        fossils = []
    elif len(fossils) > len(backup) * MAX_EXPIRY_PCT / 100.0:
        print(f"  !! {len(fossils)} of {len(backup)} rows are below spec v{spec} "
              f"(> {MAX_EXPIRY_PCT}%). That is a broken run, not a retirement — "
              f"carrying them and leaving the file at full size.")
        carried += fossils
        fossils = []

    result = list(fresh_by_key.values()) + carried

    for c in sorted(fossils, key=lambda x: x.get("company", "")):
        srcs = ", ".join(c.get("data_sources") or []) or "no sources"
        print(f"    expired  {(c.get('ticker') or '-'):6} {c.get('company','?')[:38]:38} "
              f"spec {c.get('spec_version')}  [{srcs}]")

    print(f"Merged: {len(fresh)} fresh + {len(carried)} carried "
          f"({len(fossils)} expired below spec v{spec}) = {len(result)} total")
    json.dump(result, open(output_path, "w"), indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 merge_scores.py backup.json fresh.json output.json")
        sys.exit(1)
    merge(sys.argv[1], sys.argv[2], sys.argv[3])
