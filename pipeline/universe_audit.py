#!/usr/bin/env python3
"""Is every ticker in the universe still a company?

`regen_sp500_companies.py` builds the universe from SEC's own ticker file and, when SEC
doesn't recognise a symbol, "falls back to ticker-as-name for the rare ticker SEC doesn't
recognize". It isn't rare — 41 of 973 entries carry a name identical to their ticker — and
the fallback is the same shape as every other bug this project has fixed: a lookup that
failed, recorded as a fact. Those entries are collected against nightly, resolve to no CIK,
return nothing, and never say so.

This reports, it does not edit. Four buckets:

  OK          resolves to a CIK, and SEC's name for it agrees with ours
  RENAMED     our symbol resolves to nothing, but SEC lists our company under another one
  MISMATCH    our symbol resolves, but to a different company (PARA -> Banzai)
  UNRESOLVED  SEC's ticker file has neither the symbol nor the name — delisted, acquired,
              taken private, or a symbol we invented

Run from the repo root or from pipeline/:

    python3 pipeline/universe_audit.py                 # cached index (<= 7 days old)
    python3 pipeline/universe_audit.py --refresh       # force a fresh SEC download
    python3 pipeline/universe_audit.py --json data/universe_audit.json
    python3 pipeline/universe_audit.py --strict        # exit 1 if anything MISMATCHes
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

STOP = {"inc", "corp", "corporation", "co", "company", "companies", "ltd", "limited",
        "plc", "lp", "llc", "the", "group", "holdings", "holding", "class", "trust",
        "international", "cos", "and", "technologies", "technology"}


def toks(s):
    s = "".join(c if c.isalnum() else " " for c in str(s).lower())
    return {w for w in s.split() if len(w) > 1 and w not in STOP}


def local_name(ticker, data):
    """What we already know this ticker's company is called. The universe stores 41
    entries whose "name" is just the ticker again, but the pipeline's own cache usually
    has the real name from the last run that worked — data/sec/BK.json still says
    'Bank of New York Mellon Corp'. That is enough to ask SEC where it went."""
    f = data / "sec" / f"{ticker.upper()}.json"
    if f.exists():
        try:
            n = (json.load(open(f)) or {}).get("company")
            if n and n.upper() != ticker.upper():
                return n, "sec cache"
        except (OSError, ValueError):
            pass
    f = data / "scores" / "all_scores.json"
    if f.exists():
        try:
            for row in json.load(open(f)):
                if (row.get("ticker") or "").upper() == ticker.upper():
                    n = row.get("company")
                    if n and n.upper() != ticker.upper():
                        return n, "published score"
        except (OSError, ValueError):
            pass
    return None, None


def load_universe():
    """(ticker, name) pairs from the generated file the pipelines actually import."""
    src = (HERE / "sp500_companies.py").read_text()
    return re.findall(r'\("([A-Z0-9.\-]{1,8})",\s*"([^"]*)"\)', src)


def best_title_match(name, by_title):
    """The symbol SEC lists this company under, if any. Jaccard over name tokens, so
    'Bank of New York Mellon Corp' finds BNY without matching every bank."""
    a = toks(name)
    if not a:
        return None
    best = (0.0, None)
    for title, ticker in by_title.items():
        b = toks(title)
        if not b:
            continue
        j = len(a & b) / len(a | b)
        if j > best[0]:
            best = (j, (ticker, title))
    return best[1] + (round(best[0], 2),) if best[0] >= 0.6 else None


def main():
    ap = argparse.ArgumentParser(description="Audit the universe against SEC's ticker file")
    ap.add_argument("--refresh", action="store_true", help="force a fresh SEC download")
    ap.add_argument("--json", help="also write the full result here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any ticker MISMATCHes")
    a = ap.parse_args()

    # sec_index caches to a path relative to the working directory, so run where the
    # pipeline runs. Without this, calling from the repo root writes a stray data/
    # directory there and leaves the pipeline's own cache untouched.
    os.chdir(HERE)
    import sec_index
    idx = sec_index.load_sec_index(force=a.refresh)
    if not idx:
        sys.exit("  SEC ticker index unavailable — nothing to audit against")
    print(f"  SEC ticker file: {len(idx):,} symbols")

    # First symbol wins, so a company listed twice reports its primary line.
    by_title = {}
    for t, v in idx.items():
        by_title.setdefault(v.get("title") or "", t)

    universe = load_universe()
    print(f"  universe:        {len(universe)} entries\n")

    data = HERE / "data"
    ok, renamed, mismatch, unresolved, unnamed = [], [], [], [], []
    for ticker, name in universe:
        named = bool(name) and name.upper() != ticker.upper()
        if sec_index.get_cik(ticker):
            if not named:
                unnamed.append((ticker, sec_index.get_title(ticker)))
                continue
            good, title = sec_index.verify(ticker, name)
            (ok if good else mismatch).append((ticker, name, title))
            continue
        source = "universe"
        if not named:
            name, source = local_name(ticker, data)
        hit = best_title_match(name, by_title) if name else None
        if hit:
            renamed.append((ticker, f"{name} [{source}]", hit[0], hit[1], hit[2]))
        else:
            unresolved.append((ticker, name or "no name on file"))

    if renamed:
        print(f"  RENAMED — {len(renamed)}: SEC lists these under a different symbol.")
        print("  Until the universe is updated they are collected against nightly and return nothing.")
        for t, n, new, title, score in sorted(renamed):
            print(f"    {t:7} {n[:44]:46} -> {new:7} {title[:34]:36} ({score})")
        print()

    if mismatch:
        print(f"  MISMATCH — {len(mismatch)}: the symbol resolves, but to another company.")
        for t, n, title in sorted(mismatch):
            print(f"    {t:7} we say {n[:28]:30} SEC says {title[:38]}")
        print()

    if unnamed:
        print(f"  UNNAMED — {len(unnamed)}: resolve fine, but the universe stored the ticker")
        print("  as the company name, so nothing can check they are still the same company.")
        print("  Re-run regen_sp500_companies.py to fill these in.")
        print("    " + " ".join(t for t, _ in sorted(unnamed)))
        print()

    if unresolved:
        print(f"  UNRESOLVED — {len(unresolved)}: SEC's ticker file has neither the symbol")
        print("  nor the name. Delisted, acquired, taken private, or never real.")
        for t, n in sorted(unresolved):
            print(f"    {t:7} {n[:48]}")
        print()

    # One check that needs no network: does the universe's name for a ticker agree with
    # the name we actually collected and publish for it? Where they disagree, one of the
    # two is a company that renamed, and nothing else in the pipeline notices.
    diverged = []
    published = {}
    for rel in ("sec/all_companies.json", "scores/all_scores.json"):
        f = data / rel
        if not f.exists():
            continue
        try:
            for row in json.load(open(f)):
                t = (row.get("ticker") or "").upper()
                if t and row.get("company"):
                    published.setdefault(t, row["company"])
        except (OSError, ValueError):
            pass
    for ticker, name in universe:
        other = published.get(ticker.upper())
        if not other or not name or name.upper() == ticker.upper():
            continue
        x, y = toks(name), toks(other)
        if not x or not y or (x & y):
            continue
        jx, jy = "".join(sorted(x)), "".join(sorted(y))
        if jx in jy or jy in jx:
            continue
        if any(p.startswith(q) or q.startswith(p) for p in x for q in y):
            continue
        diverged.append((ticker, name, other))
    if diverged:
        print(f"  DIVERGED — {len(diverged)}: the universe and the published score disagree")
        print("  about who this ticker is. One of the two names belongs to a company that renamed.")
        for t, n, o in sorted(diverged):
            print(f"    {t:7} universe: {n[:34]:36} published: {o[:34]}")
        print()

    print(f"  OK {len(ok)} · RENAMED {len(renamed)} · MISMATCH {len(mismatch)} · "
          f"UNNAMED {len(unnamed)} · UNRESOLVED {len(unresolved)} · DIVERGED {len(diverged)}")

    if a.json:
        out = Path(a.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        json.dump({"sec_symbols": len(idx), "universe": len(universe),
                   "ok": [t for t, _, _ in ok],
                   "renamed": [{"ticker": t, "name": n, "sec_ticker": s,
                                "sec_title": ti, "score": sc} for t, n, s, ti, sc in renamed],
                   "mismatch": [{"ticker": t, "name": n, "sec_title": ti} for t, n, ti in mismatch],
                   "unnamed": [t for t, _ in unnamed],
                   "unresolved": [{"ticker": t, "name": n} for t, n in unresolved],
                   "diverged": [{"ticker": t, "universe": n, "published": o}
                                for t, n, o in diverged]},
                  open(out, "w"), indent=2)
        print(f"  wrote {out}")

    return 1 if (a.strict and mismatch) else 0


if __name__ == "__main__":
    sys.exit(main())
