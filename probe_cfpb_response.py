#!/usr/bin/env python3
"""Probe: does CFPB's own response data discriminate between companies?

Read-only. Changes no pipeline file and writes no score. Run it from the repo root:

    python3 probe_cfpb_response.py                 # all matched companies
    python3 probe_cfpb_response.py --limit 8        # quick look

WHY THIS EXISTS

U.1's ladder divides CFPB complaint counts by SEC headcount. That denominator is not a
count of customers, and the ranking it produces says so: Tesla scores 84 — the best in the
entire CFPB set — because 134,785 people who build cars dilute 473 auto-loan complaints.
Morgan Stanley scores 78. Equifax hits the floor at 25 with 4.0M complaints against 15,000
employees, though Equifax has no customers at all; every American is a data subject.

So grounding ANCHOR and PER_DECADE against a published distribution would be calibrating a
ladder whose rungs are measured in the wrong unit. The v1.9.0 rule applies: a sub-signal is
grounded when an authoritative source measures the construct we claim, not when an
authoritative number happens to be available to divide by.

THE CANDIDATE THIS PROBE TESTS

Every CFPB complaint carries the agency's own outcome taxonomy — `company_response`
("Closed with monetary relief", "Closed with non-monetary relief", "Closed with
explanation", "Closed without relief", "Untimely response") and `timely` (Yes/No). A rate
built from those has both its numerator and its denominator inside CFPB. No headcount. No
revenue. No cross-company percentile, so a company's score cannot move because another
company's data changed — the property cfpb_pipeline.score() is written to protect, and the
reason renormalization was rejected in August.

It also reads closer to what U.1 claims to measure. "When a customer escalated to the
federal regulator, did this company make them whole?" is nearer to customer empathy than
"how many complaints per employee".

These aggregations come back on the SAME size=0 query the collector already makes, so this
costs no extra requests per company. subsignal_pipelines.fetch_cfpb already parsed
aggregations["timely"]["buckets"] from this endpoint before v1.5.0 replaced it; the current
collector receives those buckets and throws them away.

WHAT WOULD MAKE THE ANSWER NO

If relief rates cluster — everyone at roughly the same share of "Closed with explanation" —
there is no signal here and we should say so and stop. CFPB reports ~98% timely nationally,
so `timely` is almost certainly a disclosure field rather than a ladder input; this probe
measures that instead of assuming it. It also reports the spread across companies so the
answer is a number, not an impression.

This probe decides nothing. It reports.
"""
import argparse
import json
import statistics as st
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("  pip install requests --break-system-packages")

API = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
PAUSE = 0.3
YEARS = 3
UA = {"User-Agent": "HI Grade pipeline hi@thehibalance.org"}


def fetch(cfpb_name, since):
    """The collector's own query, with aggregations kept instead of discarded."""
    for attempt in range(3):
        try:
            time.sleep(PAUSE)
            r = requests.get(API, timeout=40, headers=UA, params={
                "company": cfpb_name,
                "size": 0,
                "no_aggs": "false",
                "date_received_min": since,
            })
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 503):
                time.sleep(5 * (attempt + 1))
                continue
            print(f"      HTTP {r.status_code}")
            return None
        except Exception as e:
            print(f"      {type(e).__name__}: {str(e)[:60]}")
            time.sleep(2)
    return None


def buckets(payload, field):
    """CFPB nests aggregation buckets inconsistently across fields; try both shapes."""
    agg = (payload or {}).get("aggregations") or {}
    node = agg.get(field)
    if not isinstance(node, dict):
        return None
    if "buckets" in node:
        return node["buckets"]
    inner = node.get(field)                      # {"timely": {"timely": {"buckets": [...]}}}
    if isinstance(inner, dict) and "buckets" in inner:
        return inner["buckets"]
    return None


def rates(bkts):
    total = sum(b.get("doc_count", 0) for b in bkts or [])
    if not total:
        return {}, 0
    return {b["key"]: b["doc_count"] / total for b in bkts}, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="pipeline/data")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="cfpb_response_probe.json")
    a = ap.parse_args()

    src = Path(a.data) / "cfpb" / "all_companies.json"
    if not src.exists():
        sys.exit(f"  no {src} — run this from the repo root, or pass --data")
    matched = json.load(open(src))
    since = (datetime.now() - timedelta(days=365 * YEARS)).strftime("%Y-%m-%d")

    print(f"CFPB response-quality probe — {len(matched)} matched companies, since {since}\n")
    print("Using the collector's own accepted CFPB names. Read-only.\n")

    schema_seen, out, skipped = set(), {}, []
    items = list(matched.items())
    if a.limit:
        items = items[:a.limit]

    for ticker, row in items:
        names = row.get("cfpb_names") or []
        if not names:
            skipped.append((ticker, "no accepted CFPB name"))
            continue

        resp_counts, timely_counts, total = Counter(), Counter(), 0
        for name in names[:8]:
            payload = fetch(name, since)
            if payload is None:
                continue
            if not schema_seen:
                schema_seen = set((payload.get("aggregations") or {}).keys())
            hits = ((payload.get("hits") or {}).get("total") or {})
            total += hits.get("value", 0) if isinstance(hits, dict) else (hits or 0)
            for b in buckets(payload, "company_response") or []:
                resp_counts[b["key"]] += b.get("doc_count", 0)
            for b in buckets(payload, "timely") or []:
                timely_counts[b["key"]] += b.get("doc_count", 0)

        if not resp_counts:
            skipped.append((ticker, "no company_response buckets returned"))
            print(f"  {ticker:6} {row.get('company','')[:30]:30}  no company_response aggregation")
            continue

        resp_share, resp_total = rates([{"key": k, "doc_count": v} for k, v in resp_counts.items()])
        timely_share, _ = rates([{"key": k, "doc_count": v} for k, v in timely_counts.items()])
        relief = sum(v for k, v in resp_share.items() if "relief" in k.lower())
        monetary = sum(v for k, v in resp_share.items() if "monetary" in k.lower()
                       and "non-monetary" not in k.lower())
        explanation = sum(v for k, v in resp_share.items() if "explanation" in k.lower())
        untimely = 1 - timely_share.get("Yes", 1.0) if timely_share else None

        out[ticker] = {
            "company": row.get("company"),
            "cfpb_names": names,
            "total_in_window": total,
            "response_total": resp_total,
            "response_mix": {k: round(v, 4) for k, v in sorted(resp_share.items(),
                                                              key=lambda x: -x[1])},
            "relief_rate": round(relief, 4),
            "monetary_relief_rate": round(monetary, 4),
            "explanation_only_rate": round(explanation, 4),
            "untimely_rate": round(untimely, 4) if untimely is not None else None,
            "published_U.1": row.get("U.1"),
            "per_10k_emp": row.get("per_10k_emp"),
            "probed": datetime.now().isoformat(),
        }
        print(f"  {ticker:6} {(row.get('company') or '')[:28]:28} "
              f"n={resp_total:>8,}  relief {relief*100:5.1f}%  "
              f"(monetary {monetary*100:4.1f}%)  explanation-only {explanation*100:5.1f}%  "
              f"untimely {('%.1f%%' % (untimely*100)) if untimely is not None else '  n/a'}"
              f"   was U.1 {row.get('U.1')}")

    # ── Does it discriminate? ────────────────────────────────────────────────
    print("\n" + "─" * 78)
    if schema_seen:
        print(f"aggregation fields the endpoint returned: {sorted(schema_seen)}")
    if skipped:
        print(f"\n{len(skipped)} skipped:")
        for t, why in skipped:
            print(f"  {t:6} {why}")

    for label, key in (("relief rate", "relief_rate"),
                       ("monetary relief rate", "monetary_relief_rate"),
                       ("explanation-only rate", "explanation_only_rate"),
                       ("untimely rate", "untimely_rate")):
        vals = sorted(v[key] for v in out.values() if v.get(key) is not None)
        if len(vals) < 3:
            print(f"\n{label}: too few values to judge ({len(vals)})")
            continue
        p10, p50, p90 = (vals[int(len(vals) * q)] for q in (0.10, 0.50, 0.90))
        p90 = min(p90, vals[-1])
        spread = p90 - p10
        print(f"\n{label}:  n={len(vals)}  min {vals[0]*100:.1f}%  p10 {p10*100:.1f}%  "
              f"median {p50*100:.1f}%  p90 {p90*100:.1f}%  max {vals[-1]*100:.1f}%")
        print(f"    p10-to-p90 spread: {spread*100:.1f} points  "
              f"stdev {st.pstdev(vals)*100:.1f}")
        if spread < 0.05:
            print("    ==> NOT DISCRIMINATING. Everyone lands in the same place; this cannot")
            print("        carry a ladder. Same shape as a signal whose best score is held by")
            print("        most companies it covers, which validate_pipeline flags on purpose.")
        elif spread < 0.15:
            print("    ==> WEAK. Real variation, but a ladder over it would move scores by very")
            print("        little. Worth reporting on a company page; not worth a spec bump.")
        else:
            print("    ==> DISCRIMINATING. Wide enough to carry a ladder anchored to CFPB's")
            print("        published national rate.")

    # Does it say something the current ladder does not?
    pairs = [(v["per_10k_emp"], v["relief_rate"]) for v in out.values()
             if v.get("per_10k_emp") and v.get("relief_rate") is not None]
    if len(pairs) >= 5:
        xs = [__import__("math").log10(x) for x, _ in pairs]
        ys = [y for _, y in pairs]
        mx, my = st.fmean(xs), st.fmean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        r = num / den if den else 0.0
        print(f"\ncorrelation, log10(complaints per 10k employees) vs relief rate: r = {r:+.2f}"
              f"  (n={len(pairs)})")
        if abs(r) < 0.4:
            print("    The two measure different things. Replacing one with the other is a")
            print("    change of construct, not a recalibration — say so in the spec note.")
        else:
            print("    They move together, so the new ladder would mostly restate the old one.")

    Path(a.out).write_text(json.dumps(out, indent=2))
    print(f"\nwrote {a.out}  ({len(out)} companies)")
    print("\nNothing in the pipeline changed. Paste the summary block back and we decide"
          "\nwhether U.1 gets rewritten or the finding gets written up as a dead end.")


if __name__ == "__main__":
    main()
