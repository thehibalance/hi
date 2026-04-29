#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HI Grade Coverage Audit — read-only diagnostic

Produces AUDIT_YYYY-MM-DD.md covering:
  1. Score distribution (histogram)
  2. Duplicates (same company, multiple records)
  3. Companies scoring only from Defaults (no real data)
  4. Dimension health (per-dimension score distribution)
  5. AHI-tagged companies (verify math reconciles)
  6. HD-tagged companies (verify HD penalty applies)
  7. HW-flagged companies (sanity check)
  8. Balanced Board membership + why
  9. Sub-signal coverage per company (data thinness)
  10. Extreme scores (composites > 85 or < 20)
  11. Missing canary companies (Patagonia, Ford, etc)
  12. Data source coverage gaps

Read-only. Does not modify engine or data files.
"""
import json
import os
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

SCORES_PATH = os.path.expanduser('~/Desktop/repo/pipeline/data/scores/all_scores.json')

if not os.path.exists(SCORES_PATH):
    print(f"FAIL: {SCORES_PATH} not found")
    sys.exit(1)

data = json.load(open(SCORES_PATH))
# Normalize: data might be list-of-dicts or dict-keyed-by-ticker
if isinstance(data, dict):
    companies = list(data.values())
else:
    companies = [c for c in data if isinstance(c, dict)]

print(f"Loaded {len(companies)} company records")

# Output buffer
output = []
def p(line=""):
    output.append(line)

p("# HI Grade Coverage Audit")
p(f"_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
p()
p(f"**Total records:** {len(companies)}")
p()

# ═══════════════════════════════════════════════════════════════════════
# 1. SCORE DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════
p("## 1. Score Distribution")
p()
composites = [c.get('composite', 0) for c in companies if c.get('composite') is not None]
if composites:
    avg = sum(composites) / len(composites)
    p(f"- Companies with composite: {len(composites)}")
    p(f"- Min / Avg / Max: {min(composites)} / {avg:.1f} / {max(composites)}")
    p()
    p("**Distribution (buckets):**")
    p()
    buckets = Counter()
    for c in composites:
        bucket = (c // 10) * 10
        buckets[bucket] += 1
    for bucket in sorted(buckets.keys()):
        bar = "█" * min(50, buckets[bucket])
        p(f"  {bucket:>3}–{bucket+9}: {buckets[bucket]:>4} {bar}")
p()

# ═══════════════════════════════════════════════════════════════════════
# 2. DUPLICATES
# ═══════════════════════════════════════════════════════════════════════
p("## 2. Duplicate Companies")
p()
p("_Companies appearing multiple times by normalized name_")
p()
name_to_records = defaultdict(list)
for c in companies:
    name = (c.get('company') or c.get('name') or '').strip()
    if name:
        # Normalize: lowercase, strip corp/inc/co suffixes, collapse whitespace
        key = name.lower()
        for suffix in [', inc.', ', inc', ' inc.', ' inc', ' corp.', ' corp',
                       ' corporation', ' company', ' co.', ' co', ' plc', ' ltd',
                       ' ltd.', ', llc', ' llc', '.', ',']:
            if key.endswith(suffix):
                key = key[:-len(suffix)].strip()
        # Collapse whitespace
        key = ' '.join(key.split())
        name_to_records[key].append(c)

dups = {k: v for k, v in name_to_records.items() if len(v) > 1}
p(f"**Found {len(dups)} duplicate groups** ({sum(len(v) for v in dups.values())} total duplicate records)")
p()
if dups:
    p("| Normalized name | Tickers | Composites | Names (raw) |")
    p("|---|---|---|---|")
    for key in sorted(dups.keys())[:30]:  # top 30
        records = dups[key]
        tickers = [r.get('ticker', '?') for r in records]
        comps = [r.get('composite', '?') for r in records]
        names = [r.get('company', '?')[:30] for r in records]
        p(f"| {key} | {', '.join(tickers)} | {', '.join(str(c) for c in comps)} | {' / '.join(names)} |")
    if len(dups) > 30:
        p(f"| ... | | | _({len(dups)-30} more)_ |")
p()

# ═══════════════════════════════════════════════════════════════════════
# 3. DEFAULTS-ONLY COMPANIES
# ═══════════════════════════════════════════════════════════════════════
p("## 3. Companies with no real data (`[Defaults]` only)")
p()
p("_These companies have no actual sub-signal data and score from industry defaults only._")
p()
defaults_only = []
for c in companies:
    sources = c.get('data_sources', [])
    if sources == ['Defaults'] or (len(sources) == 1 and 'Default' in str(sources[0])):
        defaults_only.append(c)

p(f"**Found {len(defaults_only)} defaults-only companies**")
p()
if defaults_only:
    p("| Company | Ticker | Composite |")
    p("|---|---|---|")
    for c in sorted(defaults_only, key=lambda x: x.get('composite', 0)):
        name = c.get('company', '?')[:40]
        ticker = c.get('ticker', '?')
        comp = c.get('composite', '?')
        p(f"| {name} | {ticker} | {comp} |")
p()

# ═══════════════════════════════════════════════════════════════════════
# 4. DIMENSION HEALTH
# ═══════════════════════════════════════════════════════════════════════
p("## 4. Dimension Score Distribution")
p()
for dim in ['D_H', 'D_U', 'D_M', 'D_A', 'D_N']:
    values = [c.get(dim) for c in companies if c.get(dim) is not None]
    if values:
        avg = sum(values) / len(values)
        zero_count = sum(1 for v in values if v == 0)
        hundred_count = sum(1 for v in values if v == 100)
        p(f"**{dim}** — avg {avg:.1f}, min {min(values)}, max {max(values)}, "
          f"zeros: {zero_count}, perfect-100s: {hundred_count}")
p()

# ═══════════════════════════════════════════════════════════════════════
# 5. AHI-TAGGED COMPANIES (math check)
# ═══════════════════════════════════════════════════════════════════════
p("## 5. AHI-tagged Companies — Math Reconciliation")
p()
p("_For each AHI company: verify D_X = mean(sub-signals) + AHI penalty_")
p()
ahi_companies = [c for c in companies 
                 if c.get('algo_harm', {}).get('has_harm')]
p(f"**Found {len(ahi_companies)} AHI-tagged companies**")
p()
if ahi_companies:
    p("| Company | Composite | AHI Score | Penalties | D_M math check |")
    p("|---|---|---|---|---|")
    for c in sorted(ahi_companies, key=lambda x: -x.get('algo_harm', {}).get('algo_harm_score', 0)):
        name = c.get('company', '?')[:25]
        comp = c.get('composite', '?')
        ahi = c.get('algo_harm', {})
        score = ahi.get('algo_harm_score', '?')
        pens = ahi.get('penalties', {})
        pen_str = f"H:{pens.get('H', 0):.1f} U:{pens.get('U', 0):.1f} M:{pens.get('M', 0):.1f} N:{pens.get('N', 0):.1f}"
        
        # Math check for M dimension
        genome = c.get('genome', {})
        m_scores = genome.get('M', {}).get('scores', {})
        d_m = c.get('D_M', 0)
        if m_scores:
            m_mean = sum(m_scores.values()) / len(m_scores)
            expected_d_m = max(0, min(100, m_mean + pens.get('M', 0)))
            delta = abs(d_m - expected_d_m)
            check = "✓" if delta < 2 else f"⚠ Δ{delta:.1f}"
            math_note = f"mean({m_mean:.1f}) + AHI.M({pens.get('M', 0):.1f}) = {expected_d_m:.1f}, got {d_m} {check}"
        else:
            math_note = "no sub-signals"
        p(f"| {name} | {comp} | {score} | {pen_str} | {math_note} |")
p()

# ═══════════════════════════════════════════════════════════════════════
# 6. HD-TAGGED COMPANIES (math check)
# ═══════════════════════════════════════════════════════════════════════
p("## 6. HD-tagged Companies — Math Reconciliation")
p()
p("_For each HD company: verify D_M = clamp(mean(M sub-signals) + HD penalty)_")
p()
hd_companies = [c for c in companies 
                if c.get('harm_documentation', {}).get('has_harm')]
p(f"**Found {len(hd_companies)} HD-tagged companies**")
p()
if hd_companies:
    p("| Company | Composite | HD Penalty | D_M | D_M math check |")
    p("|---|---|---|---|---|")
    for c in sorted(hd_companies, key=lambda x: x.get('harm_documentation', {}).get('penalties', {}).get('M', 0)):
        name = c.get('company', '?')[:25]
        comp = c.get('composite', '?')
        hd = c.get('harm_documentation', {})
        hd_pen = hd.get('penalties', {}).get('M', 0)
        d_m = c.get('D_M', 0)
        
        # Also AHI?
        ahi_m = c.get('algo_harm', {}).get('penalties', {}).get('M', 0) if c.get('algo_harm', {}).get('has_harm') else 0
        
        genome = c.get('genome', {})
        m_scores = genome.get('M', {}).get('scores', {})
        if m_scores:
            m_mean = sum(m_scores.values()) / len(m_scores)
            expected_d_m = max(0, min(100, m_mean + hd_pen + ahi_m))
            delta = abs(d_m - expected_d_m)
            check = "✓" if delta < 2 else f"⚠ Δ{delta:.1f}"
            ahi_note = f" + AHI.M({ahi_m})" if ahi_m else ""
            math_note = f"mean({m_mean:.1f}) + HD({hd_pen}){ahi_note} = {expected_d_m:.1f}, got {d_m} {check}"
        else:
            math_note = "no sub-signals"
        p(f"| {name} | {comp} | {hd_pen} | {d_m} | {math_note} |")
p()

# ═══════════════════════════════════════════════════════════════════════
# 7. HW FLAGS
# ═══════════════════════════════════════════════════════════════════════
p("## 7. Humanwashing Flags")
p()
hw_companies = [c for c in companies 
                if c.get('humanwashing_flags')]
p(f"**Found {len(hw_companies)} companies with HW flags**")
p()
hw_types = Counter()
for c in hw_companies:
    for flag in c.get('humanwashing_flags', []):
        # Extract flag category (HW.1, HW.3, AH, HD)
        if ': ' in flag:
            category = flag.split(': ', 1)[0].strip()
            hw_types[category] += 1

p("**Flag distribution:**")
for cat, count in hw_types.most_common():
    p(f"- {cat}: {count}")
p()

# ═══════════════════════════════════════════════════════════════════════
# 8. BALANCED BOARD
# ═══════════════════════════════════════════════════════════════════════
p("## 8. Balanced Board (hi_balanced = True)")
p()
balanced = [c for c in companies if c.get('hi_balanced')]
p(f"**Found {len(balanced)} Balanced Board members**")
p()
if balanced:
    p("| Company | Ticker | Composite | D_H | D_U | D_M | D_A | D_N |")
    p("|---|---|---|---|---|---|---|---|")
    for c in sorted(balanced, key=lambda x: -x.get('composite', 0)):
        p(f"| {c.get('company', '?')[:30]} | {c.get('ticker', '?')} | {c.get('composite', '?')} | "
          f"{c.get('D_H', '?')} | {c.get('D_U', '?')} | {c.get('D_M', '?')} | "
          f"{c.get('D_A', '?')} | {c.get('D_N', '?')} |")
p()

# Canary check: where are Ford, KO, Patagonia?
p("**Canary check — why these dropped out of Balanced Board:**")
p()
for canary_name in ['Ford', 'Coca-Cola', 'Patagonia']:
    matches = [c for c in companies if canary_name.lower() in (c.get('company') or '').lower()]
    if matches:
        for c in matches:
            gates = c.get('hi_balanced_gates', {})
            dim_pass = gates.get('_detail', {}).get('dim_pass', {})
            failed_dims = [k for k, v in dim_pass.items() if not v]
            p(f"- **{c.get('company', '?')}** ({c.get('ticker', '?')}): composite={c.get('composite', '?')}, "
              f"balanced={c.get('hi_balanced', False)}, failed dims: {failed_dims or 'none'}")
p()

# ═══════════════════════════════════════════════════════════════════════
# 9. SUB-SIGNAL COVERAGE (thinness)
# ═══════════════════════════════════════════════════════════════════════
p("## 9. Sub-signal Coverage — Thinnest Companies")
p()
p("_Companies with fewest data sources (most vulnerable to single-source bias)_")
p()
coverage = []
for c in companies:
    sources = c.get('data_sources', [])
    coverage.append((len(sources), c))

coverage.sort(key=lambda t: t[0])
p("**Thinnest 20 companies:**")
p()
p("| Company | Ticker | Composite | # Sources | Sources |")
p("|---|---|---|---|---|")
for count, c in coverage[:20]:
    p(f"| {c.get('company', '?')[:30]} | {c.get('ticker', '?')} | {c.get('composite', '?')} | "
      f"{count} | {', '.join(c.get('data_sources', [])[:8])} |")
p()

# Distribution histogram
source_counts = Counter(len(c.get('data_sources', [])) for c in companies)
p("**Source count distribution:**")
p()
for count in sorted(source_counts.keys()):
    bar = "█" * min(50, source_counts[count])
    p(f"  {count:>2} sources: {source_counts[count]:>4} companies {bar}")
p()

# ═══════════════════════════════════════════════════════════════════════
# 10. EXTREME SCORES (defense-worthy edge cases)
# ═══════════════════════════════════════════════════════════════════════
p("## 10. Extreme Scores (>85 or <20)")
p()
p("**Top 20 (composite ≥ 65 — worth defending):**")
p()
p("| Company | Composite | Grade |")
p("|---|---|---|")
top = sorted([c for c in companies if c.get('composite', 0) >= 65], 
             key=lambda x: -x.get('composite', 0))[:20]
for c in top:
    p(f"| {c.get('company', '?')[:35]} | {c.get('composite', '?')} | {c.get('hi_grade', '?')} |")
p()

p("**Bottom 20 (composite ≤ 40 — worth defending):**")
p()
p("| Company | Composite | Grade | AHI? | HD? |")
p("|---|---|---|---|---|")
bottom = sorted([c for c in companies if c.get('composite', 0) <= 40 and c.get('composite', 0) > 0],
                key=lambda x: x.get('composite', 0))[:20]
for c in bottom:
    ahi = "Y" if c.get('algo_harm', {}).get('has_harm') else ""
    hd = "Y" if c.get('harm_documentation', {}).get('has_harm') else ""
    p(f"| {c.get('company', '?')[:35]} | {c.get('composite', '?')} | {c.get('hi_grade', '?')} | {ahi} | {hd} |")
p()

# ═══════════════════════════════════════════════════════════════════════
# 11. MATH RECONCILIATION — random sample
# ═══════════════════════════════════════════════════════════════════════
p("## 11. Math Reconciliation Audit (random 20 companies)")
p()
p("_For each: composite should ≈ mean(D_H, D_U, D_M, D_A, D_N)_")
p()
import random
random.seed(42)
# Take a spread: 5 top, 5 bottom, 10 middle
valid = [c for c in companies if c.get('composite') is not None and c.get('D_H') is not None]
sample_companies = (
    sorted(valid, key=lambda x: -x.get('composite', 0))[:5] +
    sorted(valid, key=lambda x: x.get('composite', 0))[:5] +
    random.sample(valid, min(10, len(valid)))
)
p("| Company | Comp | D_H | D_U | D_M | D_A | D_N | mean | delta |")
p("|---|---|---|---|---|---|---|---|---|")
for c in sample_companies:
    dims = [c.get('D_H', 0), c.get('D_U', 0), c.get('D_M', 0), c.get('D_A', 0), c.get('D_N', 0)]
    mean = sum(dims) / 5
    comp = c.get('composite', 0)
    delta = abs(comp - mean)
    flag = "✓" if delta < 1 else ("⚠" if delta < 3 else "✗")
    p(f"| {c.get('company', '?')[:25]} | {comp} | {dims[0]} | {dims[1]} | {dims[2]} | "
      f"{dims[3]} | {dims[4]} | {mean:.1f} | {delta:.1f} {flag} |")
p()

# ═══════════════════════════════════════════════════════════════════════
# 12. DATA SOURCE COVERAGE
# ═══════════════════════════════════════════════════════════════════════
p("## 12. Data Source Coverage")
p()
all_sources = Counter()
for c in companies:
    for src in c.get('data_sources', []):
        all_sources[src] += 1

p("**Sources by company count:**")
p()
p("| Source | Companies | % |")
p("|---|---|---|")
for src, count in all_sources.most_common():
    pct = 100 * count / len(companies)
    p(f"| {src} | {count} | {pct:.1f}% |")
p()

# ═══════════════════════════════════════════════════════════════════════
# 13. DIMENSION SOURCE DIVERSITY (single-source warnings)
# ═══════════════════════════════════════════════════════════════════════
p("## 13. Single-Source Dimension Risk")
p()
p("_When a dimension's sub-signals all come from ONE source → score may be unrepresentative_")
p()
single_source_issues = []
for c in companies:
    genome = c.get('genome', {})
    for dim_letter in ['H', 'U', 'M', 'A', 'N']:
        dim = genome.get(dim_letter, {})
        sources = dim.get('sources', [])
        scores = dim.get('scores', {})
        if len(sources) == 1 and scores:
            # Check for extreme values
            has_extreme = any(v >= 90 or v <= 20 for v in scores.values())
            if has_extreme:
                single_source_issues.append({
                    'company': c.get('company', '?'),
                    'ticker': c.get('ticker', '?'),
                    'dim': dim_letter,
                    'source': sources[0],
                    'scores': scores
                })

p(f"**Found {len(single_source_issues)} single-source dimensions with extreme scores**")
p()
if single_source_issues[:15]:
    p("| Company | Dim | Source | Sub-scores |")
    p("|---|---|---|---|")
    for issue in single_source_issues[:15]:
        scores_str = ", ".join(f"{k}={v}" for k, v in issue['scores'].items())
        p(f"| {issue['company'][:25]} | {issue['dim']} | {issue['source']} | {scores_str} |")
p()

# ═══════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════
p("---")
p()
p("## Summary")
p()
p(f"- Total records: {len(companies)}")
p(f"- Duplicates: {len(dups)} groups ({sum(len(v) for v in dups.values())} records)")
p(f"- Defaults-only: {len(defaults_only)} companies")
p(f"- AHI-tagged: {len(ahi_companies)}")
p(f"- HD-tagged: {len(hd_companies)}")
p(f"- HW-flagged: {len(hw_companies)}")
p(f"- Balanced Board: {len(balanced)}")
p(f"- Single-source dimension risks: {len(single_source_issues)}")
p()

# ═══════════════════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════════════════
out_path = os.path.expanduser(f'~/Desktop/repo/AUDIT_{datetime.now().strftime("%Y-%m-%d")}.md')
with open(out_path, 'w') as f:
    f.write('\n'.join(output))

print(f"\n✓ Audit written to: {out_path}")
print(f"  {len(output)} lines")
print()
print("Open it:")
print(f"  open {out_path}")
print()
print("Or view key sections:")
print(f"  head -80 {out_path}")
