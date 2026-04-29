#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_bunching.py — Find where defaults are propagating in the score data

Pulls live API data and identifies:
  1. Companies with low data coverage (< 50% real sub-signals)
  2. Score clustering at common default values
  3. Sub-signals that are 50/55/60 (likely defaults)
  4. Companies with backslash artifacts in names
  5. Companies whose detail page won't load properly

Run locally:  python3 audit_bunching.py

Output: audit_report.md (human-readable) + audit_data.json (raw)
"""
import json
import urllib.request
import urllib.error
import sys
from collections import Counter, defaultdict

API = "https://api.thehibalance.org/api/v1"
TIMEOUT = 30

# Cloudflare blocks no-UA requests with 403 — pretend to be a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}

def fetch_json(url, timeout=TIMEOUT):
    """Fetch URL with browser-like headers, return parsed JSON."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

print("HI Grade Score Audit")
print("=" * 60)
print()

# ═══════════════════════════════════════════════════════════════════════
# Step 1: Fetch HUMAN 100 list
# ═══════════════════════════════════════════════════════════════════════
print("Fetching HUMAN 100...")
try:
    h100 = fetch_json(API + "/human100")
    constituents = h100.get('constituents', [])
    print(f"  ✓ Got {len(constituents)} constituents")
except Exception as e:
    print(f"  ✗ HUMAN 100 fetch failed: {e}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════
# Step 2: Fetch detail for each one (to get sub-signal coverage)
# ═══════════════════════════════════════════════════════════════════════
print()
print(f"Fetching detail for each company (this takes ~2 min)...")

details = []
broken_pages = []
for i, c in enumerate(constituents):
    ticker = c.get('ticker')
    if not ticker:
        continue
    try:
        d = fetch_json(f"{API}/score/ticker/{ticker}", timeout=10)
        if d.get('error') or not d.get('D_H'):
            broken_pages.append({'ticker': ticker, 'company': c.get('company'), 'error': d.get('error', 'no D_H')})
        else:
            details.append(d)
    except Exception as e:
        broken_pages.append({'ticker': ticker, 'company': c.get('company'), 'error': str(e)})
    
    # Progress
    if (i + 1) % 20 == 0:
        print(f"  ... {i + 1}/{len(constituents)}")

print(f"  ✓ Got {len(details)} valid details")
print(f"  ✗ Broken/incomplete: {len(broken_pages)}")

# ═══════════════════════════════════════════════════════════════════════
# Step 3: Analyze
# ═══════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("ANALYSIS")
print("=" * 60)

# 3a: Score distribution
print()
print("Score Distribution (all constituents):")
scores = [c.get('composite', 0) for c in constituents]
score_counter = Counter(scores)
top_scores = score_counter.most_common(15)
for score, count in top_scores:
    bar = "█" * count
    print(f"  {score}: {count:3d} {bar}")

# Identify cluster point — the most common score
cluster_score = top_scores[0][0] if top_scores else None
cluster_count = top_scores[0][1] if top_scores else 0
print()
print(f"⚠ Most common score: {cluster_score} ({cluster_count} companies)")

# 3b: Coverage analysis (how many sub-signals have real data)
print()
print("Coverage Analysis (sub-signals with real vs default data):")
print()

# Default values that scoring engine assigns when no data: 50, 55, 60, 40
DEFAULT_VALUES = {50, 55, 60, 40}

low_coverage = []
high_coverage = []

for d in details:
    genome = d.get('genome', {})
    real_count = 0
    default_count = 0
    total = 0
    
    for dim in ['H', 'U', 'M', 'A', 'N']:
        dg = genome.get(dim, {})
        sub_scores = dg.get('scores', {})
        sources = dg.get('sources', [])
        
        for sub_key, val in sub_scores.items():
            total += 1
            if val in DEFAULT_VALUES and not sources:
                default_count += 1
            elif val in DEFAULT_VALUES and sources:
                # Has sources but landed on default value — could go either way
                # Conservative: count as default
                default_count += 1
            else:
                real_count += 1
    
    coverage_pct = (real_count / total * 100) if total > 0 else 0
    
    entry = {
        'ticker': d.get('ticker'),
        'company': d.get('company'),
        'composite': d.get('composite'),
        'real_signals': real_count,
        'default_signals': default_count,
        'total_signals': total,
        'coverage_pct': round(coverage_pct, 1)
    }
    
    if coverage_pct < 50:
        low_coverage.append(entry)
    else:
        high_coverage.append(entry)

print(f"  Companies with < 50% real data: {len(low_coverage)}")
print(f"  Companies with >= 50% real data: {len(high_coverage)}")

if low_coverage:
    print()
    print("  Top 20 LOW COVERAGE companies (mostly default scores):")
    low_coverage.sort(key=lambda x: x['coverage_pct'])
    for e in low_coverage[:20]:
        print(f"    {e['composite']:3d} · {e['coverage_pct']:5.1f}% · {e['ticker']:6s} · {e['company']}")

# 3c: Companies at the cluster score
if cluster_score:
    print()
    print(f"Companies at {cluster_score} (the cluster):")
    cluster_companies = [d for d in details if d.get('composite') == cluster_score]
    for c in cluster_companies[:15]:
        # find the matching coverage entry
        cov = next((e for e in low_coverage + high_coverage if e['ticker'] == c.get('ticker')), None)
        if cov:
            print(f"    {c.get('ticker'):6s} · {c.get('company'):40s} · coverage {cov['coverage_pct']:5.1f}%")

# 3d: Backslash artifacts in names
print()
print("Companies with backslash artifacts in names:")
backslash_companies = [c for c in constituents if '\\' in (c.get('company') or '')]
for c in backslash_companies:
    print(f"  '{c.get('company')}'  →  needs cleaning")
if not backslash_companies:
    print("  (none — name cleanup may have already deployed)")

# 3e: Most common defaults per sub-signal
print()
print("Sub-signal default frequency (top 10 most-defaulted sub-signals):")
sub_signal_defaults = defaultdict(int)
sub_signal_total = defaultdict(int)

for d in details:
    genome = d.get('genome', {})
    for dim in ['H', 'U', 'M', 'A', 'N']:
        dg = genome.get(dim, {})
        sub_scores = dg.get('scores', {})
        sources = dg.get('sources', [])
        for sub_key, val in sub_scores.items():
            sub_signal_total[sub_key] += 1
            if val in DEFAULT_VALUES and not sources:
                sub_signal_defaults[sub_key] += 1

sub_signal_pct = {}
for k in sub_signal_total:
    pct = sub_signal_defaults[k] / sub_signal_total[k] * 100 if sub_signal_total[k] else 0
    sub_signal_pct[k] = pct

ranked = sorted(sub_signal_pct.items(), key=lambda x: -x[1])
for sub, pct in ranked[:10]:
    print(f"  {sub}: {pct:5.1f}% defaulted ({sub_signal_defaults[sub]}/{sub_signal_total[sub]} companies)")

# ═══════════════════════════════════════════════════════════════════════
# Step 4: Save
# ═══════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("SAVING REPORTS")
print("=" * 60)

# Markdown report
with open('audit_report.md', 'w') as f:
    f.write("# HI Grade Score Audit\n\n")
    f.write(f"Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")
    f.write(f"- Total constituents: {len(constituents)}\n")
    f.write(f"- Successful detail fetches: {len(details)}\n")
    f.write(f"- Broken/incomplete detail pages: {len(broken_pages)}\n\n")
    
    f.write("## Score Distribution\n\n")
    f.write("Most common scores (the bunching):\n\n")
    for score, count in top_scores:
        f.write(f"- **{score}**: {count} companies\n")
    
    f.write("\n## Broken Detail Pages\n\n")
    if broken_pages:
        f.write("These tickers don't return valid detail data:\n\n")
        for b in broken_pages:
            f.write(f"- `{b['ticker']}` ({b['company']}) — {b['error']}\n")
    else:
        f.write("(none)\n")
    
    f.write("\n## Backslash-Name Companies\n\n")
    if backslash_companies:
        for c in backslash_companies:
            f.write(f"- `{c.get('company')}`  ({c.get('ticker')})\n")
    else:
        f.write("(none — already cleaned)\n")
    
    f.write("\n## Low Coverage Companies (mostly defaults)\n\n")
    f.write("Score | Coverage | Ticker | Company\n")
    f.write("------|----------|--------|--------\n")
    for e in sorted(low_coverage, key=lambda x: x['coverage_pct'])[:30]:
        f.write(f"{e['composite']} | {e['coverage_pct']}% | {e['ticker']} | {e['company']}\n")
    
    f.write("\n## Sub-signal Default Rates\n\n")
    f.write("How often each sub-signal lands on a default value:\n\n")
    f.write("Sub-signal | Defaulted | Total | % Defaulted\n")
    f.write("-----------|-----------|-------|------------\n")
    for sub, pct in ranked:
        f.write(f"{sub} | {sub_signal_defaults[sub]} | {sub_signal_total[sub]} | {pct:.1f}%\n")

# JSON for downstream scripts
report_data = {
    'generated_at': __import__('datetime').datetime.now().isoformat(),
    'total_constituents': len(constituents),
    'total_details': len(details),
    'broken_pages': broken_pages,
    'score_distribution': dict(score_counter),
    'cluster_score': cluster_score,
    'cluster_count': cluster_count,
    'low_coverage_companies': low_coverage,
    'backslash_companies': [
        {'ticker': c.get('ticker'), 'company': c.get('company')}
        for c in backslash_companies
    ],
    'sub_signal_default_rates': {k: round(v, 2) for k, v in sub_signal_pct.items()}
}

with open('audit_data.json', 'w') as f:
    json.dump(report_data, f, indent=2)

print()
print("✓ audit_report.md — readable summary")
print("✓ audit_data.json — raw data for follow-up scripts")
print()
print("=" * 60)
print("KEY FINDINGS — quick read:")
print("=" * 60)
print(f"  Cluster: {cluster_count} companies at {cluster_score}")
print(f"  Low coverage: {len(low_coverage)} companies (<50% real data)")
print(f"  Broken pages: {len(broken_pages)} tickers")
print(f"  Backslash names: {len(backslash_companies)} companies")
if ranked:
    print(f"  Worst sub-signal: {ranked[0][0]} ({ranked[0][1]:.1f}% defaulted)")
