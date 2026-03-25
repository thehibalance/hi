#!/usr/bin/env python3
"""
HI. Pipeline Data Validation — 3-Layer Defense
═══════════════════════════════════════════════

Layer 1: INPUT VALIDATION — Catches bad data before it enters scoring
Layer 2: OUTPUT VALIDATION — Catches broken scores before they go live
Layer 3: SOURCE CROSS-REFERENCING — MSSI rule: no single source moves a score >15

Run standalone:
    python3 validate_pipeline.py                     # Full validation
    python3 validate_pipeline.py --layer 1           # Input only
    python3 validate_pipeline.py --layer 2           # Output only  
    python3 validate_pipeline.py --layer 3           # Cross-ref only
    python3 validate_pipeline.py --strict             # Block on warnings too
    python3 validate_pipeline.py --fix                # Auto-fix recoverable issues

Plug into run_all.py:
    from validate_pipeline import validate_all
    issues = validate_all(data_dir="data")
    if issues["critical"]:
        print("BLOCKED — critical issues found")
        sys.exit(1)

Patent Pending · Morf Innovations LLC · The HI Balance
"""

import json
import os
import sys
import math
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

DIMENSIONS = ["D_H", "D_U", "D_M", "D_A", "D_N"]
DIM_LABELS = {"D_H": "Human Consciousness", "D_U": "Understanding & Empathy",
              "D_M": "Moral & Ethical Conduct", "D_A": "Alive & Environmental",
              "D_N": "Natural Transparency"}

# Layer 1: Input bounds
VALID_SCORE_RANGE = (0, 100)
MAX_HEADCOUNT = 3_000_000        # Walmart is ~2.1M — largest employer
MAX_REVENUE_PER_EMPLOYEE = 50_000_000  # Some hedge funds hit this
MAX_HEADCOUNT_CHANGE_PCT = 80    # No company legitimately changes 80%+ in one quarter
MAX_AI_HIRING_RATIO = 1.0        # Can't be >100%

# Layer 2: Output bounds
MAX_COMPOSITE_CHANGE = 15        # Flag if score moves >15 between runs
MAX_GOLD_COMPANIES_PCT = 15      # If >15% of companies are Gold, something's wrong
MIN_COMPANIES_EXPECTED = 100     # Pipeline should produce at least this many
EXPECTED_DISTRIBUTION = {        # Rough expected shape
    "high_90_100": (0, 5),       # 0-5% of companies should score 90-100
    "mid_40_70": (30, 70),       # 30-70% should be in the middle
    "low_0_20": (0, 15),         # 0-15% should be very low
}

# Layer 3: MSSI (Maximum Single-Source Impact)
MSSI_THRESHOLD = 15              # No single source can move a sub-signal by more than 15 points


# ═══════════════════════════════════════════════════════════════════════
# ISSUE TRACKING
# ═══════════════════════════════════════════════════════════════════════

class ValidationReport:
    """Tracks issues across all three layers."""
    
    def __init__(self):
        self.issues = []
        self.stats = {}
        self.timestamp = datetime.now().isoformat()
    
    def add(self, layer, severity, company, field, message, value=None, expected=None):
        """
        severity: 'critical' (blocks pipeline), 'warning' (flag but continue), 'info' (logged only)
        """
        self.issues.append({
            "layer": layer,
            "severity": severity,
            "company": company,
            "field": field,
            "message": message,
            "value": value,
            "expected": expected,
        })
    
    @property
    def critical(self):
        return [i for i in self.issues if i["severity"] == "critical"]
    
    @property
    def warnings(self):
        return [i for i in self.issues if i["severity"] == "warning"]
    
    @property
    def info(self):
        return [i for i in self.issues if i["severity"] == "info"]
    
    def summary(self):
        return {
            "timestamp": self.timestamp,
            "total_issues": len(self.issues),
            "critical": len(self.critical),
            "warnings": len(self.warnings),
            "info": len(self.info),
            "blocked": len(self.critical) > 0,
            "stats": self.stats,
            "issues": self.issues,
        }
    
    def print_report(self):
        """Human-readable report."""
        print("\n" + "=" * 60)
        print("HI. PIPELINE VALIDATION REPORT")
        print("=" * 60)
        print(f"Timestamp: {self.timestamp}")
        print(f"Total issues: {len(self.issues)}")
        print(f"  🔴 Critical: {len(self.critical)}")
        print(f"  🟡 Warning:  {len(self.warnings)}")
        print(f"  🔵 Info:     {len(self.info)}")
        print(f"  Pipeline:    {'BLOCKED' if self.critical else 'PASSED'}")
        
        if self.stats:
            print(f"\nStats:")
            for k, v in self.stats.items():
                print(f"  {k}: {v}")
        
        if self.critical:
            print(f"\n{'─' * 60}")
            print("🔴 CRITICAL — Pipeline blocked until resolved:")
            for i in self.critical:
                print(f"  [{i['layer']}] {i['company']}: {i['message']}")
                if i.get("value") is not None:
                    print(f"         Value: {i['value']}  Expected: {i.get('expected', '—')}")
        
        if self.warnings:
            print(f"\n{'─' * 60}")
            print("🟡 WARNINGS — Review recommended:")
            for i in self.warnings[:20]:  # Cap at 20
                print(f"  [{i['layer']}] {i['company']}: {i['message']}")
            if len(self.warnings) > 20:
                print(f"  ... and {len(self.warnings) - 20} more warnings")
        
        print("=" * 60 + "\n")


# ═══════════════════════════════════════════════════════════════════════
# LAYER 1: INPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════════

def validate_inputs(companies, report, subsignals_dir=None):
    """
    Layer 1: Validate raw data before scoring.
    Catches impossible values, missing data, and suspicious inputs.
    """
    print("  Layer 1: Input validation...")
    
    for c in companies:
        name = c.get("company", c.get("name", "Unknown"))
        ticker = c.get("ticker", "")
        
        # ── Score range checks ──
        for dim in DIMENSIONS:
            val = c.get(dim)
            if val is None:
                continue  # Missing is OK — defaults to industry median
            if not isinstance(val, (int, float)):
                report.add(1, "critical", name, dim,
                          f"Non-numeric dimension score: {type(val).__name__}",
                          val, "number 0-100")
                continue
            if val < VALID_SCORE_RANGE[0] or val > VALID_SCORE_RANGE[1]:
                report.add(1, "critical", name, dim,
                          f"Dimension score out of range: {val}",
                          val, "0-100")
        
        # ── Composite sanity ──
        composite = c.get("composite")
        if composite is not None:
            if composite < 0 or composite > 100:
                report.add(1, "critical", name, "composite",
                          f"Composite out of range: {composite}",
                          composite, "0-100")
            
            # Verify composite matches dimensions
            dims = [c.get(d, 0) for d in DIMENSIONS]
            if all(d > 0 for d in dims):
                expected_raw = sum(dims) / 5
                # Account for floor rule
                if min(dims) < 10:
                    expected = min(expected_raw, 40)
                else:
                    expected = expected_raw
                expected = round(expected)
                if abs(composite - expected) > 2:  # Allow small rounding differences
                    report.add(1, "warning", name, "composite",
                              f"Composite {composite} doesn't match dimensions (expected ~{expected})",
                              composite, expected)
        
        # ── Key signals validation ──
        ks = c.get("key_signals", {})
        if ks:
            # Headcount
            hc = ks.get("headcount")
            if hc is not None:
                if hc < 0:
                    report.add(1, "critical", name, "headcount",
                              f"Negative headcount: {hc}", hc, ">= 0")
                elif hc > MAX_HEADCOUNT:
                    report.add(1, "warning", name, "headcount",
                              f"Headcount exceeds maximum known ({hc:,})",
                              hc, f"< {MAX_HEADCOUNT:,}")
                elif hc == 0:
                    report.add(1, "warning", name, "headcount",
                              "Zero headcount — data source may have failed",
                              0, "> 0")
            
            # Headcount change
            hc_pct = ks.get("headcount_change_pct")
            if hc_pct is not None:
                if abs(hc_pct) > MAX_HEADCOUNT_CHANGE_PCT:
                    report.add(1, "critical", name, "headcount_change_pct",
                              f"Headcount change {hc_pct}% — likely bad data",
                              hc_pct, f"±{MAX_HEADCOUNT_CHANGE_PCT}%")
            
            # Revenue per employee
            rpe = ks.get("revenue_per_employee")
            if rpe is not None:
                if rpe < 0:
                    report.add(1, "critical", name, "revenue_per_employee",
                              f"Negative RPE: {rpe}", rpe, ">= 0")
                elif rpe > MAX_REVENUE_PER_EMPLOYEE:
                    report.add(1, "warning", name, "revenue_per_employee",
                              f"RPE ${rpe:,.0f} — unusually high",
                              rpe, f"< ${MAX_REVENUE_PER_EMPLOYEE:,.0f}")
            
            # AI hiring ratio
            ahr = ks.get("ai_hiring_ratio")
            if ahr is not None:
                if ahr < 0 or ahr > MAX_AI_HIRING_RATIO:
                    report.add(1, "critical", name, "ai_hiring_ratio",
                              f"AI hiring ratio out of range: {ahr}",
                              ahr, "0.0-1.0")
            
            # Glassdoor
            gr = ks.get("glassdoor_rating")
            if gr is not None:
                if gr < 1.0 or gr > 5.0:
                    report.add(1, "critical", name, "glassdoor_rating",
                              f"Glassdoor rating out of range: {gr}",
                              gr, "1.0-5.0")
        
        # ── Data source validation ──
        ds = c.get("data_sources", [])
        if not ds or ds == ["Manual Scoring"]:
            pass  # Seed companies — OK
        elif len(ds) < 2:
            report.add(1, "info", name, "data_sources",
                      f"Only {len(ds)} data source — score may be unreliable",
                      len(ds), ">= 2")
    
    # ── Subsignal file validation (if directory provided) ──
    if subsignals_dir and Path(subsignals_dir).exists():
        for f in Path(subsignals_dir).glob("*.json"):
            try:
                data = json.load(open(f))
                ticker = f.stem
                
                # Check for null/NaN values in subsignal scores
                for dim_key in ["H", "U", "M", "A", "N"]:
                    dim_data = data.get(dim_key, {})
                    scores = dim_data.get("scores", {})
                    for sig_id, val in scores.items():
                        if val is None:
                            continue  # None is acceptable — means no data
                        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                            report.add(1, "critical", ticker, sig_id,
                                      f"Invalid subsignal value: {val}",
                                      val, "number 0-100 or null")
                        elif val < 0 or val > 100:
                            report.add(1, "critical", ticker, sig_id,
                                      f"Subsignal out of range: {val}",
                                      val, "0-100")
            except json.JSONDecodeError:
                report.add(1, "critical", f.stem, "file",
                          f"Corrupt JSON: {f.name}")
            except Exception as e:
                report.add(1, "warning", f.stem, "file",
                          f"Error reading {f.name}: {e}")
    
    print(f"    ✓ {len(companies)} companies checked")


# ═══════════════════════════════════════════════════════════════════════
# LAYER 2: OUTPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════════

def validate_outputs(companies, previous_companies, report):
    """
    Layer 2: Validate scored output before publishing.
    Compares against previous run, checks distribution, catches anomalies.
    """
    print("  Layer 2: Output validation...")
    
    if not companies:
        report.add(2, "critical", "PIPELINE", "companies",
                  "No companies in output — pipeline produced nothing")
        return
    
    # ── Minimum company count ──
    if len(companies) < MIN_COMPANIES_EXPECTED:
        report.add(2, "critical", "PIPELINE", "count",
                  f"Only {len(companies)} companies (expected {MIN_COMPANIES_EXPECTED}+)",
                  len(companies), f">= {MIN_COMPANIES_EXPECTED}")
    
    # ── Score distribution check ──
    composites = [c.get("composite", 0) for c in companies if c.get("composite")]
    if composites:
        avg = sum(composites) / len(composites)
        stdev = math.sqrt(sum((x - avg) ** 2 for x in composites) / len(composites))
        min_score = min(composites)
        max_score = max(composites)
        
        report.stats["total_companies"] = len(companies)
        report.stats["avg_composite"] = round(avg, 1)
        report.stats["stdev"] = round(stdev, 1)
        report.stats["min_score"] = min_score
        report.stats["max_score"] = max_score
        
        # Check distribution shape
        pct_high = sum(1 for c in composites if c >= 90) / len(composites) * 100
        pct_mid = sum(1 for c in composites if 40 <= c <= 70) / len(composites) * 100
        pct_low = sum(1 for c in composites if c <= 20) / len(composites) * 100
        
        report.stats["pct_90_100"] = round(pct_high, 1)
        report.stats["pct_40_70"] = round(pct_mid, 1)
        report.stats["pct_0_20"] = round(pct_low, 1)
        
        if pct_high > EXPECTED_DISTRIBUTION["high_90_100"][1]:
            report.add(2, "warning", "DISTRIBUTION", "high_scores",
                      f"{pct_high:.1f}% of companies score 90-100 (expected <{EXPECTED_DISTRIBUTION['high_90_100'][1]}%)",
                      pct_high, f"< {EXPECTED_DISTRIBUTION['high_90_100'][1]}%")
        
        if pct_mid < EXPECTED_DISTRIBUTION["mid_40_70"][0]:
            report.add(2, "warning", "DISTRIBUTION", "mid_scores",
                      f"Only {pct_mid:.1f}% in 40-70 range (expected {EXPECTED_DISTRIBUTION['mid_40_70'][0]}-{EXPECTED_DISTRIBUTION['mid_40_70'][1]}%)",
                      pct_mid)
        
        # All scores the same = broken pipeline
        if stdev < 1.0:
            report.add(2, "critical", "DISTRIBUTION", "stdev",
                      f"Standard deviation is {stdev:.1f} — scores are nearly identical. Pipeline likely broken.",
                      stdev, "> 5.0")
        
        # Gold count check
        gold_count = sum(1 for c in companies if c.get("hi_balanced"))
        gold_pct = gold_count / len(companies) * 100
        report.stats["gold_count"] = gold_count
        report.stats["gold_pct"] = round(gold_pct, 1)
        
        if gold_pct > MAX_GOLD_COMPANIES_PCT:
            report.add(2, "warning", "DISTRIBUTION", "gold_count",
                      f"{gold_pct:.1f}% of companies are Gold ({gold_count}) — threshold may be too low",
                      gold_pct, f"< {MAX_GOLD_COMPANIES_PCT}%")
    
    # ── Comparison with previous run ──
    if previous_companies:
        prev_by_key = {}
        for c in previous_companies:
            key = c.get("ticker") or c.get("company", "")
            if key:
                prev_by_key[key.upper() if c.get("ticker") else key] = c
        
        big_movers = []
        disappeared = []
        
        for c in companies:
            key = c.get("ticker") or c.get("company", "")
            lookup = key.upper() if c.get("ticker") else key
            
            if lookup in prev_by_key:
                prev = prev_by_key[lookup]
                old_score = prev.get("composite", 0)
                new_score = c.get("composite", 0)
                delta = abs(new_score - old_score)
                
                if delta > MAX_COMPOSITE_CHANGE:
                    direction = "↑" if new_score > old_score else "↓"
                    big_movers.append((c.get("company", key), old_score, new_score, delta, direction))
                    
                    severity = "critical" if delta > 25 else "warning"
                    report.add(2, severity, c.get("company", key), "composite_change",
                              f"Score moved {direction}{delta} points ({old_score} → {new_score})",
                              delta, f"< {MAX_COMPOSITE_CHANGE}")
                
                # Check individual dimensions for big swings
                for dim in DIMENSIONS:
                    old_dim = prev.get(dim, 0)
                    new_dim = c.get(dim, 0)
                    dim_delta = abs(new_dim - old_dim)
                    if dim_delta > 25:
                        report.add(2, "warning", c.get("company", key), dim,
                                  f"{DIM_LABELS.get(dim, dim)} moved {dim_delta} points ({old_dim} → {new_dim})",
                                  dim_delta, "< 25")
                
                del prev_by_key[lookup]
        
        # Companies that disappeared
        for key, prev in prev_by_key.items():
            if prev.get("data_sources") and prev["data_sources"] != ["Manual Scoring"]:
                report.add(2, "warning", prev.get("company", key), "missing",
                          "Company was in previous run but missing from current output")
        
        report.stats["big_movers"] = len(big_movers)
        report.stats["disappeared"] = len(prev_by_key)
        
        if big_movers:
            big_movers.sort(key=lambda x: -x[3])
            report.stats["top_movers"] = [
                {"company": m[0], "old": m[1], "new": m[2], "delta": m[3], "direction": m[4]}
                for m in big_movers[:10]
            ]
    else:
        report.add(2, "info", "PIPELINE", "previous",
                  "No previous scores found — skipping comparison")
    
    # ── Sanity spot-checks ──
    # Known ethical leaders shouldn't score below 30
    known_ethical = {"patagonia", "costco", "rei"}
    # Known problematic shouldn't score above 85
    known_problematic = {"meta platforms", "tiktok / bytedance", "x / twitter"}
    
    for c in companies:
        name_lower = c.get("company", "").lower()
        composite = c.get("composite", 50)
        
        for ethical in known_ethical:
            if ethical in name_lower and composite < 30:
                report.add(2, "warning", c["company"], "sanity_check",
                          f"Known ethical leader scoring only {composite}",
                          composite, "> 30")
        
        for problematic in known_problematic:
            if problematic in name_lower and composite > 85:
                report.add(2, "warning", c["company"], "sanity_check",
                          f"Known problematic company scoring {composite}",
                          composite, "< 85")
    
    print(f"    ✓ {len(companies)} companies validated against {len(previous_companies) if previous_companies else 0} previous")


# ═══════════════════════════════════════════════════════════════════════
# LAYER 3: SOURCE CROSS-REFERENCING (MSSI RULE)
# ═══════════════════════════════════════════════════════════════════════

def validate_source_crossref(companies, subsignals_dir, report):
    """
    Layer 3: Enforce MSSI — Maximum Single-Source Impact.
    No single data source can move any sub-signal by more than 15 points.
    Material changes require corroboration from 2+ independent sources.
    """
    print("  Layer 3: Source cross-referencing (MSSI)...")
    
    if not subsignals_dir or not Path(subsignals_dir).exists():
        report.add(3, "info", "PIPELINE", "subsignals",
                  "No subsignals directory — skipping MSSI validation")
        return
    
    prev_dir = Path(subsignals_dir).parent / "subsignals_previous"
    has_previous = prev_dir.exists()
    
    mssi_violations = 0
    single_source_scores = 0
    
    for f in Path(subsignals_dir).glob("*.json"):
        try:
            data = json.load(open(f))
            ticker = f.stem
            company_name = data.get("company", ticker)
            
            for dim_key in ["H", "U", "M", "A", "N"]:
                dim_data = data.get(dim_key, {})
                scores = dim_data.get("scores", {})
                sources = dim_data.get("sources", [])
                
                # Check: does this dimension have data from 2+ independent sources?
                if len(sources) < 2 and scores:
                    non_default_scores = {k: v for k, v in scores.items() if v is not None and v != 50}
                    if non_default_scores:
                        single_source_scores += 1
                        # Only flag if the single-source score is far from 50 (industry default)
                        extreme_scores = {k: v for k, v in non_default_scores.items() if abs(v - 50) > 20}
                        if extreme_scores:
                            report.add(3, "warning", company_name, f"{dim_key}_sources",
                                      f"Dimension {dim_key} has only {len(sources)} source(s) "
                                      f"but extreme scores: {extreme_scores}",
                                      len(sources), ">= 2 for extreme values")
                
                # Check MSSI: if we have previous data, no single source should have
                # moved any sub-signal by more than MSSI_THRESHOLD
                if has_previous:
                    prev_file = prev_dir / f.name
                    if prev_file.exists():
                        try:
                            prev_data = json.load(open(prev_file))
                            prev_scores = prev_data.get(dim_key, {}).get("scores", {})
                            
                            for sig_id, new_val in scores.items():
                                if new_val is None:
                                    continue
                                old_val = prev_scores.get(sig_id)
                                if old_val is None:
                                    continue
                                
                                delta = abs(new_val - old_val)
                                if delta > MSSI_THRESHOLD:
                                    # Check if multiple sources corroborate the change
                                    if len(sources) < 2:
                                        mssi_violations += 1
                                        report.add(3, "critical", company_name, sig_id,
                                                  f"MSSI violation: {sig_id} moved {delta:.0f} points "
                                                  f"({old_val:.0f} → {new_val:.0f}) from single source",
                                                  delta, f"< {MSSI_THRESHOLD} without corroboration")
                                    else:
                                        report.add(3, "info", company_name, sig_id,
                                                  f"{sig_id} moved {delta:.0f} points but corroborated "
                                                  f"by {len(sources)} sources",
                                                  delta)
                        except Exception:
                            pass  # Previous file corrupt — skip comparison
        except Exception as e:
            report.add(3, "warning", f.stem, "file",
                      f"Error processing {f.name}: {e}")
    
    report.stats["mssi_violations"] = mssi_violations
    report.stats["single_source_dimensions"] = single_source_scores
    
    files_checked = len(list(Path(subsignals_dir).glob("*.json")))
    print(f"    ✓ {files_checked} subsignal files checked, {mssi_violations} MSSI violations")


# ═══════════════════════════════════════════════════════════════════════
# MAIN VALIDATION RUNNER
# ═══════════════════════════════════════════════════════════════════════

def validate_all(data_dir="data", layers=None, strict=False):
    """
    Run all validation layers and return the report.
    
    Args:
        data_dir: Path to the data directory
        layers: List of layers to run (default: all [1, 2, 3])
        strict: If True, treat warnings as critical
    
    Returns:
        ValidationReport with all issues
    """
    if layers is None:
        layers = [1, 2, 3]
    
    report = ValidationReport()
    data_path = Path(data_dir)
    scores_dir = data_path / "scores"
    subsignals_dir = data_path / "subsignals"
    
    print("\nHI. Pipeline Validation")
    print("─" * 40)
    
    # Load current scores
    scores_file = scores_dir / "all_scores.json"
    companies = []
    if scores_file.exists():
        try:
            companies = json.load(open(scores_file))
            companies = [c for c in companies if not c.get("error")]
            print(f"  Loaded {len(companies)} companies from {scores_file}")
        except Exception as e:
            report.add(0, "critical", "PIPELINE", "scores_file",
                      f"Cannot read {scores_file}: {e}")
    else:
        report.add(0, "critical", "PIPELINE", "scores_file",
                  f"Scores file not found: {scores_file}")
    
    # Load previous scores (for comparison)
    prev_file = scores_dir / "all_scores_previous.json"
    previous = []
    if prev_file.exists():
        try:
            previous = json.load(open(prev_file))
            previous = [c for c in previous if not c.get("error")]
            print(f"  Loaded {len(previous)} previous companies")
        except Exception:
            pass
    
    # Run requested layers
    if 1 in layers and companies:
        validate_inputs(companies, report, 
                       subsignals_dir if subsignals_dir.exists() else None)
    
    if 2 in layers and companies:
        validate_outputs(companies, previous, report)
    
    if 3 in layers:
        validate_source_crossref(companies, 
                                subsignals_dir if subsignals_dir.exists() else None,
                                report)
    
    # Strict mode: upgrade warnings to critical
    if strict:
        for issue in report.issues:
            if issue["severity"] == "warning":
                issue["severity"] = "critical"
    
    # Print report
    report.print_report()
    
    # Save report to file
    report_dir = data_path / "validation"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json.dump(report.summary(), open(report_file, "w"), indent=2, default=str)
    print(f"  Report saved: {report_file}")
    
    # Also save latest
    latest_file = report_dir / "latest.json"
    json.dump(report.summary(), open(latest_file, "w"), indent=2, default=str)
    
    return report


def snapshot_previous(data_dir="data"):
    """
    Save current scores as 'previous' for next run comparison.
    Call this AFTER validation passes, BEFORE publishing new scores.
    """
    scores_dir = Path(data_dir) / "scores"
    current = scores_dir / "all_scores.json"
    previous = scores_dir / "all_scores_previous.json"
    
    if current.exists():
        import shutil
        shutil.copy2(current, previous)
        print(f"  Snapshot saved: {previous}")
    
    # Also snapshot subsignals
    subsignals_dir = Path(data_dir) / "subsignals"
    prev_subsignals = Path(data_dir) / "subsignals_previous"
    
    if subsignals_dir.exists():
        if prev_subsignals.exists():
            import shutil
            shutil.rmtree(prev_subsignals)
        import shutil
        shutil.copytree(subsignals_dir, prev_subsignals)
        print(f"  Subsignals snapshot saved: {prev_subsignals}")


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HI. Pipeline Data Validation")
    parser.add_argument("--data", default="data", help="Data directory path")
    parser.add_argument("--layer", type=int, nargs="+", help="Run specific layers (1, 2, 3)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as critical")
    parser.add_argument("--snapshot", action="store_true", help="Save current as previous (run after validation passes)")
    args = parser.parse_args()
    
    if args.snapshot:
        snapshot_previous(args.data)
        sys.exit(0)
    
    report = validate_all(
        data_dir=args.data,
        layers=args.layer,
        strict=args.strict
    )
    
    if report.critical:
        print("❌ Pipeline BLOCKED — resolve critical issues before publishing")
        sys.exit(1)
    else:
        print("✅ Pipeline PASSED — scores are safe to publish")
        
        # Auto-snapshot on success
        snapshot_previous(args.data)
        sys.exit(0)
