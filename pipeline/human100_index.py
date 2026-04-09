#!/usr/bin/env python3
"""
HUMAN 100 Index — Patent Feature #8
The top 100 most human-conscious public companies, ranked by HI Grade.

ETF-licensable. Rebalanced monthly. Methodology: HUMAN Grade Spec v1.0.

Output:
  data/human100/index.json     — The ranked index
  data/human100/metadata.json  — Index metadata (date, stats, methodology)
  data/human100/changes.json   — Additions/removals since last rebalance

Usage:
  python human100_index.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def load_json(path):
    p = Path(path)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return []


def compute_human100():
    print(f"\n{'='*60}")
    print(f"  HUMAN 100 Index — Monthly Rebalance")
    print(f"  Patent Feature: ETF-Licensable Ethical Index")
    print(f"{'='*60}\n")

    scores = load_json("data/scores/all_scores.json")
    heartbeats = {h["ticker"]: h for h in load_json("data/heartbeat/heartbeats.json") if h.get("ticker")}

    output_dir = Path("data/human100")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ═══ ELIGIBILITY CRITERIA ═══
    # Must be a public company (has ticker)
    # Must have at least 3 data sources (signal confidence)
    # Must not have a hard floor trigger (dimension < 10)
    # Must not be grade F
    # Balance floor companies ARE eligible but capped at C

    eligible = []
    excluded = []

    for c in scores:
        ticker = c.get("ticker", "")
        name = c.get("company", "")
        grade = c.get("hi_grade", "F")
        composite = c.get("composite", 0)
        sources = c.get("data_sources", [])
        floor = c.get("floor_triggered", False)

        if not ticker:
            excluded.append({"company": name, "reason": "No ticker (private)"})
            continue
        if len(sources) < 3:
            excluded.append({"company": name, "ticker": ticker, "reason": f"Insufficient data ({len(sources)} sources)"})
            continue
        if floor:
            excluded.append({"company": name, "ticker": ticker, "reason": "Hard floor triggered"})
            continue
        if grade == "F":
            excluded.append({"company": name, "ticker": ticker, "reason": f"Grade F ({composite})"})
            continue
        # Integrity gate: no active humanwashing flags (matches Gold gating)
        hw_flags = c.get("humanwashing_flags", [])
        if hw_flags:
            first_flag = (hw_flags[0][:60] if isinstance(hw_flags[0], str) else "flagged")
            excluded.append({"company": name, "ticker": ticker, "reason": f"Humanwashing: {first_flag}"})
            continue
        # Integrity gate: AHI == 0 (zero tolerance)
        ah = c.get("algo_harm") or {}
        ahi = (ah.get("algo_harm_score", 0) if isinstance(ah, dict) else 0) or 0
        if ahi > 0:
            excluded.append({"company": name, "ticker": ticker, "reason": f"AHI {ahi}"})
            continue
        # Integrity gate: Heartbeat decay stable or watch
        hb = heartbeats.get(ticker.upper(), {})
        dl = hb.get("decay_level", "stable")
        if dl in ("warning", "critical"):
            di = hb.get("decay_index", 0)
            excluded.append({"company": name, "ticker": ticker, "reason": f"Decay {dl} ({di})"})
            continue

        eligible.append(c)

    # Sort by composite score (descending), then alphabetically for ties
    eligible.sort(key=lambda x: (-x.get("composite", 0), x.get("company", "")))

    # Take top 100
    human100 = eligible[:100]

    # ═══ BUILD INDEX ═══
    index = []
    for rank, c in enumerate(human100, 1):
        ticker = c.get("ticker", "")
        hb = heartbeats.get(ticker.upper(), {})

        entry = {
            "rank": rank,
            "company": c.get("company", ""),
            "ticker": ticker,
            "hi_grade": c.get("hi_grade", "?"),
            "composite": c.get("composite", 0),
            "D_H": c.get("D_H", 0),
            "D_U": c.get("D_U", 0),
            "D_M": c.get("D_M", 0),
            "D_A": c.get("D_A", 0),
            "D_N": c.get("D_N", 0),
            "industry": c.get("industry", ""),
            "data_sources": c.get("data_sources", []),
            "balance_floor": c.get("balance_floor", False),
            "decay_index": hb.get("decay_index", 0),
            "decay_level": hb.get("decay_level", "stable"),
            "humanwashing_flags": len(c.get("humanwashing_flags", [])),
        }
        index.append(entry)

    # ═══ COMPUTE INDEX STATS ═══
    composites = [e["composite"] for e in index]
    avg = sum(composites) / len(composites) if composites else 0
    median = sorted(composites)[len(composites)//2] if composites else 0

    grade_dist = {}
    for e in index:
        g = e["hi_grade"]
        grade_dist[g] = grade_dist.get(g, 0) + 1

    industry_dist = {}
    for e in index:
        ind = e.get("industry", "other") or "other"
        industry_dist[ind] = industry_dist.get(ind, 0) + 1

    # Dimension averages across the index
    dim_avgs = {}
    for d in ["D_H", "D_U", "D_M", "D_A", "D_N"]:
        vals = [e[d] for e in index if e[d]]
        dim_avgs[d] = round(sum(vals) / len(vals)) if vals else 0

    # Watchlist: companies in the 100 with decay signals
    watchlist = [e for e in index if e["decay_level"] != "stable"]
    watchlist.sort(key=lambda x: -x["decay_index"])

    # ═══ DETECT CHANGES (if previous index exists) ═══
    changes = {"additions": [], "removals": [], "rank_changes": []}
    prev_path = output_dir / "index.json"
    if prev_path.exists():
        prev = json.load(open(prev_path))
        prev_tickers = {e["ticker"]: e for e in prev}
        curr_tickers = {e["ticker"]: e for e in index}

        for t, e in curr_tickers.items():
            if t not in prev_tickers:
                changes["additions"].append({"ticker": t, "company": e["company"], "rank": e["rank"], "composite": e["composite"]})
            else:
                old_rank = prev_tickers[t]["rank"]
                new_rank = e["rank"]
                if old_rank != new_rank:
                    changes["rank_changes"].append({"ticker": t, "company": e["company"], "old_rank": old_rank, "new_rank": new_rank, "delta": old_rank - new_rank})

        for t, e in prev_tickers.items():
            if t not in curr_tickers:
                changes["removals"].append({"ticker": t, "company": e["company"], "old_rank": e["rank"]})

        changes["rank_changes"].sort(key=lambda x: -abs(x["delta"]))

    # ═══ METADATA ═══
    now = datetime.now(timezone.utc)
    metadata = {
        "name": "HUMAN 100 Index",
        "description": "The top 100 most human-conscious public companies, ranked by HI Grade.",
        "patent": "Patent Pending — Morf Innovations LLC",
        "methodology": "HUMAN Grade Methodology Spec v1.0",
        "rebalance_date": now.strftime("%Y-%m-%d"),
        "rebalance_time": now.isoformat(),
        "total_eligible": len(eligible),
        "total_excluded": len(excluded),
        "index_size": len(index),
        "average_composite": round(avg),
        "median_composite": median,
        "dimension_averages": dim_avgs,
        "grade_distribution": grade_dist,
        "industry_distribution": industry_dist,
        "watchlist_count": len(watchlist),
        "spec_version": "1.0.0",
        "license": "HUMAN 100 Index™ — licensing available for ETF, fund, and financial product use.",
    }

    # ═══ SAVE ═══
    with open(output_dir / "index.json", "w") as f:
        json.dump(index, f, indent=2)
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    with open(output_dir / "changes.json", "w") as f:
        json.dump(changes, f, indent=2)
    with open(output_dir / "watchlist.json", "w") as f:
        json.dump(watchlist, f, indent=2)

    # ═══ PRINT SUMMARY ═══
    print(f"  HUMAN 100 Index — {now.strftime('%B %d, %Y')}")
    print(f"  Eligible companies: {len(eligible)}")
    print(f"  Excluded: {len(excluded)}")
    print(f"  Index size: {len(index)}")
    print(f"  Average composite: {round(avg)}")
    print(f"  Median composite: {median}")
    print(f"\n  Grade distribution:")
    for g in ["HI Certified", "A", "B", "C"]:
        if g in grade_dist:
            print(f"    {g}: {grade_dist[g]}")

    print(f"\n  Dimension averages:")
    for d, v in dim_avgs.items():
        print(f"    {d}: {v}")

    print(f"\n  Industry breakdown:")
    for ind, count in sorted(industry_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"    {ind}: {count}")

    if watchlist:
        print(f"\n  ⚠ Watchlist ({len(watchlist)} companies with active decay):")
        for w in watchlist[:10]:
            print(f"    #{w['rank']:3d} {w['company']:30s}  Decay: {w['decay_index']}")

    if changes["additions"]:
        print(f"\n  ✚ New additions: {len(changes['additions'])}")
        for a in changes["additions"][:5]:
            print(f"    #{a['rank']} {a['company']} ({a['composite']})")

    if changes["removals"]:
        print(f"\n  ✖ Removals: {len(changes['removals'])}")
        for r in changes["removals"][:5]:
            print(f"    {r['company']} (was #{r['old_rank']})")

    print(f"\n  TOP 10:")
    for e in index[:10]:
        flags = ""
        if e["balance_floor"]: flags += " ⚖"
        if e["decay_level"] != "stable": flags += f" ♥{e['decay_index']}"
        if e["humanwashing_flags"]: flags += " ⚑"
        print(f"    #{e['rank']:3d}  {e['hi_grade']:12s}  {e['composite']:3d}  {e['company']:30s}  [{e['ticker']}]{flags}")

    print(f"\n  {'='*60}")
    print(f"  HUMAN 100 Index™ — Patent Pending")
    print(f"  Licensing available for ETF, fund, and financial product use.")
    print(f"  {'='*60}")
    print(f"\n  Outputs:")
    print(f"    data/human100/index.json     — {len(index)} ranked companies")
    print(f"    data/human100/metadata.json  — Index metadata")
    print(f"    data/human100/changes.json   — Rebalance changes")
    print(f"    data/human100/watchlist.json  — {len(watchlist)} decay-active companies")


if __name__ == "__main__":
    compute_human100()
