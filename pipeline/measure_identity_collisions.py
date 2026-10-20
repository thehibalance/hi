#!/usr/bin/env python3
"""Two silent failure modes in the company matcher, measured. Read-only. From pipeline/:

    python3 measure_identity_collisions.py

WHY

`index_by_company` indexes every record under its exact name, its `normalize_name`, its
`canon_name` and its ticker. Collisions go through `_claim`:

    def _claim(idx, key, record):
        \"\"\"Later spellings still win a shared key, except that an OTC foreign line never
        displaces a primary listing.\"\"\"

**Later wins, silently.** That is correct for the intended case — one company spelled two ways —
and indistinguishable from the unintended one: two different companies reducing to one key. The
exact-name path does not even go through `_claim`; it is a bare `idx[name] = r`, last wins
unconditionally.

And the scoring loop builds its universe from those keys:

    _k = canon_name(key) or normalize_name(key)
    if _k and _k not in _CANON_TOO_GENERIC:
        all_companies.add(_k)

`canon_name` returns "" for fifteen generic words, so a record whose canonical form reduces to
one of them contributes NO key. v1.8.2 added that after `normalize_name` turned "AMERICAN
INTERNATIONAL GROUP, INC." into "american" and the engine scored the remnant as its own company
— composite 39, 2 of 19 signals, no ticker. The comment says dropping it is safe because "the
record it came from is always in the universe under its full name too." **True for the remnant it
was fixing; an assumption for every other record.**

So two failure modes, both silent, both measurable:

  1. **MERGE** — one key claimed by records with different tickers. One company's data is
     attached to another company's name, and whichever was indexed later wins.
  2. **DROP** — a record contributing no usable key, so nothing it holds reaches the universe
     under its own identity.

WHAT THIS DOES

Replays the key construction for all five stores, recording EVERY claimant per key instead of
keeping the last. Then classifies each collision:

    same ticker        benign — one company, two spellings. The intended case.
    OTC protected      benign — _claim already refuses to let an F/Y line displace a primary.
    no ticker either    unclear — cannot tell a merge from a spelling without an identifier.
    DIFFERENT TICKERS  a merge. Two listed companies sharing one key.

And for drops, prints the records whose canon_name is empty, with whether their exact or
normalized name still reaches the universe — which is the assumption v1.8.2 relies on, tested
rather than trusted.

Changes nothing.
"""
import json
from collections import defaultdict
from pathlib import Path

try:
    from scoring_engine import (canon_name, normalize_name, _otc_foreign,
                                _CANON_TOO_GENERIC)
except Exception as e:                                      # noqa: BLE001
    raise SystemExit(f"  cannot import from scoring_engine ({e}) — run from pipeline/")

STORES = [
    ("sec", "data/sec/all_companies.json"),
    ("epa", "data/epa/all_companies.json"),
    ("cdp", "data/cdp/all_companies.json"),
    ("jobs", "data/jobs/all_companies.json"),
    ("glassdoor", "data/glassdoor/all_companies.json"),
]

loaded, missing = [], []
for label, rel in STORES:
    p = Path(rel)
    if not p.exists():
        missing.append((label, rel))
        continue
    try:
        recs = json.load(open(p))
    except (OSError, ValueError) as e:                      # noqa: BLE001
        missing.append((label, f"{rel} ({e})"))
        continue
    if isinstance(recs, dict):
        recs = recs.get("companies") or list(recs.values())
    loaded.append((label, [r for r in recs if isinstance(r, dict)]))

if not loaded:
    raise SystemExit("  no stores could be read — run from pipeline/")

print("STORES")
for label, recs in loaded:
    print(f"   {label:12} {len(recs):>5} records")
for label, rel in missing:
    print(f"   {label:12}     — not read: {rel}")
print()


def tick(r):
    return (r.get("ticker") or "").upper().strip()


def name_of(r):
    return (r.get("company") or "").strip()


# ── 1. collisions, per store ──────────────────────────────────────────────────
print("1. MERGES — one key claimed by more than one record\n")
all_merges = []
for label, recs in loaded:
    claims = defaultdict(list)
    for r in recs:
        nm = name_of(r).lower()
        if not nm:
            continue
        for key in {nm, normalize_name(nm), canon_name(nm)}:
            if key:
                claims[key].append(r)

    buckets = {"same ticker": 0, "OTC protected": 0, "no ticker": 0, "DIFFERENT": []}
    for key, rs in claims.items():
        if len(rs) < 2:
            continue
        ts = {tick(r) for r in rs}
        names = {name_of(r) for r in rs}
        if len(names) < 2:
            continue                                  # identical record repeated
        real = {t for t in ts if t}
        if len(real) <= 1:
            buckets["no ticker" if not real else "same ticker"] += 1
            continue
        # does _claim's OTC rule already protect this one?
        prim = [t for t in real if not _otc_foreign(t)]
        if len(prim) <= 1:
            buckets["OTC protected"] += 1
            continue
        buckets["DIFFERENT"].append((key, sorted(real), sorted(names)))

    n_diff = len(buckets["DIFFERENT"])
    print(f"   {label:12} same-ticker {buckets['same ticker']:>4} · "
          f"OTC-protected {buckets['OTC protected']:>3} · "
          f"no-ticker {buckets['no ticker']:>4} · "
          f"**DIFFERENT TICKERS {n_diff}**")
    for key, ts, names in buckets["DIFFERENT"][:10]:
        all_merges.append((label, key, ts, names))
        print(f"      key {key!r}")
        print(f"         tickers {', '.join(ts)}")
        for nm in names[:4]:
            print(f"         {nm}")
    if n_diff > 10:
        print(f"      … and {n_diff - 10} more")

print(f"\n   total merges across all stores: {len(all_merges)}")
if not all_merges:
    print("   Clean. Every shared key is one company under two spellings, or is already")
    print("   protected by _claim's OTC rule. That retires a standing worry rather than")
    print("   confirming it, which is the more useful of the two outcomes to have measured.")
else:
    print("   Each of these has one company's record attached to another company's key,")
    print("   with the later-indexed record winning. Whichever lost contributes nothing")
    print("   under its own identity, and whichever won may be scored with the other's data.")

# ── 2. drops ──────────────────────────────────────────────────────────────────
print("\n\n2. DROPS — records whose canon_name is empty\n")
print(f"   _CANON_TOO_GENERIC has {len(_CANON_TOO_GENERIC)} words: "
      f"{', '.join(sorted(_CANON_TOO_GENERIC))}\n")

total_dropped = 0
for label, recs in loaded:
    dropped = []
    for r in recs:
        nm = name_of(r)
        if not nm:
            continue
        if not canon_name(nm.lower()):
            dropped.append(r)
    if not dropped:
        print(f"   {label:12} none")
        continue
    total_dropped += len(dropped)
    print(f"   {label:12} {len(dropped)} record(s) contribute no canonical key:")
    for r in dropped[:12]:
        nm = name_of(r)
        norm = normalize_name(nm.lower())
        # v1.8.2's assumption: the record is in the universe under its full name anyway
        still = "exact+norm reach the universe" if norm and norm not in _CANON_TOO_GENERIC \
            else "!! NOTHING reaches the universe"
        print(f"      {nm[:38]:38} ticker {tick(r) or '—':8} norm={norm!r:22} {still}")
    if len(dropped) > 12:
        print(f"      … and {len(dropped) - 12} more")

print(f"\n   total dropped-canon records: {total_dropped}")
print("""
   A record here reaches the scoring universe ONLY through its exact or normalized name.
   v1.8.2 says that is always the case; the right-hand column tests it per record rather
   than assuming it. Any row reading "NOTHING reaches the universe" holds data for a
   company the engine never scores — the inverse of the phantom "american" that v1.8.2
   fixed, and harder to notice, because a missing company produces no output at all.

Nothing changed. Read-only.
""")
