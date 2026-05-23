#!/usr/bin/env python3
"""
HI Grade — Dedupe all_scores.json (v2 with name-similarity guard)

Finds duplicate company records (same domain) AND verifies the company names
are similar enough to confidently merge. Keeps the record with more
data_sources.

v2 changes over v1:
- Added names_likely_same() check. Records must share a domain AND have similar
  company names. This prevents:
    * False positives where bad upstream domain data causes unrelated companies
      to "share" a domain (e.g., TSM and AMZN both claiming amazon.com).
    * Loss of subsidiary records intentionally scored separately from parent
      (e.g., Ring (Amazon), Ben & Jerry's (Unilever), Activision (Microsoft)).
- Embeds NAME_MAP from merge_seed.py so acronym matches still work (IBM ==
  International Business Machines).

Usage:
  python3 dedupe_scores.py                    # auto-detect repo
  python3 dedupe_scores.py --dry-run          # report only
  python3 dedupe_scores.py --scores PATH      # explicit path
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime


# Mirrors merge_seed.py NAME_MAP — keep in sync if you edit one
NAME_MAP = {
    "alphabet / google": ["alphabet"],
    "alphabet": ["alphabet"],
    "ibm": ["international business machines"],
    "tiktok / bytedance": ["bytedance"],
    "meta / facebook": ["meta platforms"],
    "x / twitter": ["x corp", "twitter"],
    "zara / inditex": ["inditex", "industria de diseno"],
    "37signals / basecamp": ["37signals", "basecamp"],
    "automattic / wordpress": ["automattic"],
    "ikea / ingka group": ["ikea", "ingka"],
    "kellanova / wk kellogg": ["kellanova", "kellogg"],
    "block (square)": ["block"],
    "ups": ["united parcel"],
    "exxonmobil": ["exxon mobil"],
    "samsung electronics": ["samsung"],
    "shell plc": ["shell"],
    "bp": ["bp plc", "british petroleum"],
    "toyota": ["toyota motor"],
    "subaru": ["subaru corp", "fuji heavy"],
    "rivian": ["rivian automotive"],
    "accenture": ["accenture plc"],
    "deloitte": ["deloitte touche"],
    "unilever": ["unilever plc", "unilever nv"],
    "hp inc.": ["hp inc", "hewlett"],
    "dell technologies": ["dell tech"],
    "lyft": ["lyft inc"],
    "doordash": ["doordash inc"],
    "instacart": ["maplebear"],
    "robinhood": ["robinhood markets"],
    "beyond meat": ["beyond meat inc"],
    "impossible foods": ["impossible"],
    "oatly": ["oatly group"],
    "warby parker": ["warby parker inc"],
    "allbirds": ["allbirds inc"],
    "lululemon": ["lululemon athletica"],
    "gap inc.": ["gap inc"],
    "nordstrom": ["nordstrom inc"],
    "coursera": ["coursera inc"],
    "duolingo": ["duolingo inc"],
    "chegg": ["chegg inc"],
    "nintendo": ["nintendo co"],
    "danone": ["danone sa"],
    "spacex": ["space exploration"],
    "dropbox": ["dropbox inc"],
    "stripe": ["stripe inc"],
    "valve corporation": ["valve corp"],
    "the new york times": ["new york times"],
    "fidelity investments": ["fidelity", "fmr"],
    "vanguard": ["vanguard group"],
    "biogen": ["biogen inc"],
    "moderna": ["moderna inc"],
}


def normalize(name):
    """Normalize for matching. Mirrors merge_seed.py normalize()."""
    n = (name or "").lower().strip()
    for s in [' inc.', ' inc', ' corporation', ' corp.', ' corp', ' llc', ' ltd.', ' ltd',
              ' co.', ' co', ' plc', ' sa', ' ag', ' se', ' nv',
              ' group', ' holdings', ' company', ' companies',
              ', inc.', ', inc', ', corporation', ', corp.', ', corp', ', llc']:
        n = n.replace(s, '')
    n = re.sub(r'\s*\(.*?\)', '', n)        # strip parentheticals
    n = re.sub(r'\s*/\s*', ' ', n)          # strip slashes
    n = re.sub(r'[^a-z0-9 &]', '', n)       # strip punctuation
    return re.sub(r'\s+', ' ', n).strip()


def has_parent_in_parens(company):
    """True if company name has '(Parent)' suffix — intentional separation."""
    return bool(re.search(r'\([^)]+\)\s*$', company or ""))


def names_likely_same(rec_a, rec_b):
    """Conservative same-entity check. Returns True only if names suggest
    the same company (not just shared domains).

    Allows merging when:
      1. Normalized names match exactly
      2. One normalized name is substring of the other (min 5 chars to avoid
         spurious 'inc' or 'corp' overlap)
      3. NAME_MAP links them
    """
    a_raw = rec_a.get("company", "")
    b_raw = rec_b.get("company", "")

    # Block: parent-in-parens means intentional separation, never auto-merge
    if has_parent_in_parens(a_raw) or has_parent_in_parens(b_raw):
        return False

    a = normalize(a_raw)
    b = normalize(b_raw)
    if not a or not b:
        return False
    if a == b:
        return True

    # Substring overlap (min length 5 — avoids "inc"/"corp" trivial matches)
    if len(a) >= 4 and len(b) >= 4 and (a in b or b in a):
        return True

    # NAME_MAP equivalence — check if either name is the key OR contains a value,
    # AND the other name also is the key OR contains a value
    for key, vals in NAME_MAP.items():
        kn = normalize(key)
        a_in = (a == kn) or any(v in a for v in vals)
        b_in = (b == kn) or any(v in b for v in vals)
        if a_in and b_in:
            return True

    return False


def record_priority(rec):
    """Higher tuple = better candidate to keep.
    1. data_sources count
    2. not a seed-only record
    3. has valid ticker
    """
    sources = len(rec.get("data_sources") or [])
    is_not_seed = 1 if rec.get("_source") != "seed" else 0
    has_ticker = 1 if (rec.get("ticker") or "").strip() else 0
    return (sources, is_not_seed, has_ticker)


def dedupe(scores, verbose=True):
    """Group by domain. For each group, check pairwise name similarity.
    Merge only when domain overlap AND name similarity both pass.
    """
    # Domain → record indices
    domain_to_idxs = {}
    for i, rec in enumerate(scores):
        for d in rec.get("domains") or []:
            d = (d or "").lower().strip()
            if not d:
                continue
            domain_to_idxs.setdefault(d, []).append(i)

    # Union-find, but only union if names_likely_same
    parent = list(range(len(scores)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    skipped_pairs = []
    for d, idxs in domain_to_idxs.items():
        if len(idxs) <= 1:
            continue
        # Pairwise check — only union if names match
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                if names_likely_same(scores[idxs[i]], scores[idxs[j]]):
                    union(idxs[i], idxs[j])
                else:
                    skipped_pairs.append({
                        "domain": d,
                        "a": f"{scores[idxs[i]].get('ticker') or '∅'}/{scores[idxs[i]].get('company')!r}",
                        "b": f"{scores[idxs[j]].get('ticker') or '∅'}/{scores[idxs[j]].get('company')!r}",
                    })

    # Group by component root
    components = {}
    for i in range(len(scores)):
        components.setdefault(find(i), []).append(i)

    drop_set = set()
    drops_detail = []
    for root, idxs in components.items():
        if len(idxs) <= 1:
            continue
        idxs_sorted = sorted(idxs, key=lambda i: record_priority(scores[i]), reverse=True)
        keep = idxs_sorted[0]
        for drop in idxs_sorted[1:]:
            drop_set.add(drop)
            drops_detail.append({
                "kept_ticker": scores[keep].get("ticker") or "",
                "kept_company": scores[keep].get("company") or "",
                "kept_sources": len(scores[keep].get("data_sources") or []),
                "dropped_ticker": scores[drop].get("ticker") or "",
                "dropped_company": scores[drop].get("company") or "",
                "dropped_sources": len(scores[drop].get("data_sources") or []),
                "shared_domains": sorted(
                    set(d.lower() for d in (scores[keep].get("domains") or []))
                    & set(d.lower() for d in (scores[drop].get("domains") or []))
                ),
            })

    if verbose:
        if drops_detail:
            print(f"\n  Will drop {len(drops_detail)} duplicate(s):\n")
            for d in drops_detail:
                ks = f"{d['kept_ticker'] or '∅'}/{d['kept_company']!r} ({d['kept_sources']} src)"
                ds = f"{d['dropped_ticker'] or '∅'}/{d['dropped_company']!r} ({d['dropped_sources']} src)"
                print(f"    KEEP {ks}")
                print(f"    DROP {ds}")
                print(f"    shared: {', '.join(d['shared_domains'])}\n")
        else:
            print("  No safe duplicates found.")

        # Dedup the unique skipped pairs by (a,b) tuple
        unique_skipped = {(p["a"], p["b"], p["domain"]): p for p in skipped_pairs}
        if unique_skipped:
            print(f"\n  Preserved {len(unique_skipped)} pair(s) sharing a domain but with different names")
            print(f"  (subsidiary-of-parent records and likely upstream data-quality issues):\n")
            for p in unique_skipped.values():
                print(f"    {p['a']}")
                print(f"    vs {p['b']}  [shared: {p['domain']}]\n")

    deduped = [s for i, s in enumerate(scores) if i not in drop_set]
    return deduped, drops_detail, list({(p["a"], p["b"], p["domain"]): p for p in skipped_pairs}.values())


def find_repo_root():
    for c in [Path.home() / "Desktop" / "repo", Path("/mnt/project"), Path.cwd(), Path.cwd().parent]:
        if (c / "pipeline" / "data" / "scores" / "all_scores.json").exists():
            return c
    return None


def main():
    ap = argparse.ArgumentParser(description="Dedupe HI Grade all_scores.json")
    ap.add_argument("--scores", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    print("═══ HI Grade — all_scores.json Deduper (v3) ═══\n")

    if args.scores:
        scores_path = Path(args.scores)
    else:
        root = find_repo_root()
        if not root:
            print("  ✗ Could not locate repo. Pass --scores explicitly.")
            sys.exit(1)
        scores_path = root / "pipeline" / "data" / "scores" / "all_scores.json"

    if not scores_path.exists():
        print(f"  ✗ File not found: {scores_path}")
        sys.exit(1)

    print(f"  Reading: {scores_path}")
    with open(scores_path) as f:
        scores = json.load(f)
    print(f"  Loaded: {len(scores)} records")

    deduped, drops, preserved = dedupe(scores)

    if not drops:
        print("  Nothing to do. Exiting.")
        return

    print(f"\n  Result: {len(scores)} → {len(deduped)} records "
          f"(removing {len(drops)} confirmed dupes; preserving {len(preserved)} pair(s) for review)")

    if args.dry_run:
        print("\n  --dry-run set; not writing.")
        return

    if not args.no_backup:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = scores_path.with_suffix(f".pre_dedupe_v3_{ts}.bak")
        shutil.copy2(scores_path, bak)
        print(f"\n  Backup: {bak}")

    tmp = scores_path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(deduped, f, indent=2)
    tmp.replace(scores_path)
    print(f"  ✓ Wrote: {scores_path}\n")


if __name__ == "__main__":
    main()
