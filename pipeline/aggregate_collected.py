#!/usr/bin/env python3
"""v1.4.0 — fold the per-company collected files into the aggregates the scoring engine reads.

Until v1.4.0, data_collector wrote fresh results to data/subsignals/{TICKER}.json and
data/extended/{TICKER}.json every night, but scoring_engine only reads
data/subsignals/all_subsignals.json and data/subsignals/extended/all_extended.json, which had
not been rebuilt since April 2026. This step closes that gap, with evidence gates:

  * A blank fetch never overwrites a stored value.
  * Industry defaults (source "Industry", "Industry+EPA") are not evidence and are not folded in.
  * CFPB is withheld entirely: its company matching returns 0 complaints for almost every
    company (Bank of America, Wells Fargo, Capital One included), and "0 complaints" was being
    scored as a good record. It returns once matching is fixed and verified.
  * HIBP counts only when a breach is matched by exact domain (collector fix in v1.4.0) and at
    least one is found. Older records used substring matching ("gm" matched "CardingMafia") and
    are dropped. "No known breach" is not proof of good data practice and earns no credit.
  * FEC counts only when committees were actually found for that ticker. "0 committees" was
    scored as clean political conduct (M.5 85), and tickerless companies shared one cache file.
  * FDA from the per-company files is held back pending a matching audit.

Run from pipeline/:  python3 aggregate_collected.py [--data data] [--dry-run]
"""
import argparse
import glob
import json
import os
import re
from collections import Counter

WITHHELD_SS = {"cfpb"}   # never folded in, and removed from the aggregate
HELD_EXT = {"fda"}       # new per-company values not folded in (existing values untouched)
CACHE = re.compile(r"^[a-z]+\d*_")  # per-source caches like cfpb_AAPL.json, hibp2_AAPL.json
CACHE_KEY = re.compile(r"^(CFPB|FEC|CPSC|HIBP\d*)_")  # cache files mistaken for tickers (v1.4.0 bug)


def blank(v):
    return v is None or v == "" or v == [] or v == {}


def is_default(v):
    return isinstance(v, dict) and str(v.get("source", "")).startswith("Industry")


def all_blank(v):
    return isinstance(v, dict) and all(blank(x) for k, x in v.items() if k not in ("source", "raw", "note"))


def hibp_ok(v):
    raw = v.get("raw") if isinstance(v, dict) else None
    return isinstance(raw, dict) and raw.get("match") == "domain" and raw.get("breach_count", 0) > 0


def fec_ok(v):
    raw = v.get("raw") if isinstance(v, dict) else None
    return isinstance(raw, dict) and bool(raw.get("ticker")) and raw.get("committees_found", 0) > 0


def hibp_breaches(v):
    raw = v.get("raw") if isinstance(v, dict) else None
    return (raw or {}).get("breach_count", 0) if isinstance(raw, dict) else 0


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ss_path = os.path.join(a.data, "subsignals", "all_subsignals.json")
    ext_path = os.path.join(a.data, "subsignals", "extended", "all_extended.json")
    ss, ext = load(ss_path, {}), load(ext_path, {})
    n = Counter()
    for k in [k for k in ss if CACHE_KEY.match(k)]:
        ss.pop(k)
        n["removed:cache-file-entry"] += 1

    for f in glob.glob(os.path.join(a.data, "subsignals", "*.json")):
        b = os.path.basename(f)
        if CACHE.match(b) or b.startswith("all_"):
            continue
        d = load(f, None)
        if not isinstance(d, dict):
            continue
        cur = ss.setdefault(b[:-5].upper(), {})
        for k, v in d.items():
            if k in WITHHELD_SS or blank(v) or is_default(v) or all_blank(v):
                continue
            if (k == "hibp" and not hibp_ok(v)) or (k == "fec" and not fec_ok(v)):
                continue
            cur[k] = v
            n["ss:" + k] += 1

    for f in glob.glob(os.path.join(a.data, "extended", "*.json")):
        d = load(f, None)
        if not isinstance(d, dict):
            continue
        for t, e in d.items():
            if not isinstance(e, dict):
                continue
            cur = ext.setdefault(t.upper(), {})
            for k, v in e.items():
                if k in HELD_EXT or blank(v) or all_blank(v):
                    continue
                cur[k] = v
                n["ext:" + k] += 1

    # Gates apply to what was already stored, too.
    for t, d in ss.items():
        if not isinstance(d, dict):
            continue
        for k in WITHHELD_SS:
            if d.pop(k, None) is not None:
                n["removed:" + k] += 1
        if "hibp" in d and not hibp_ok(d["hibp"]):
            d.pop("hibp")
            n["removed:hibp-unverified"] += 1
        if "fec" in d and not fec_ok(d["fec"]):
            d.pop("fec")
            n["removed:fec-no-committees"] += 1

    print(f"  aggregate_collected: {len(ss)} subsignal tickers, {len(ext)} extended tickers")
    for k, v in sorted(n.items()):
        print(f"    {k:28} {v}")
    if not a.dry_run:
        with open(ss_path, "w") as f:
            json.dump(ss, f, indent=2)
        with open(ext_path, "w") as f:
            json.dump(ext, f, indent=2)


if __name__ == "__main__":
    main()
