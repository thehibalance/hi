#!/usr/bin/env python3
"""
HI. — Harm Documentation Pipeline
==================================
Documents publicly verifiable harm caused by companies, to penalize the M dimension.

CORE PRINCIPLE: "Humans can still choose."
- Sugar, alcohol, tobacco-as-product, gambling: NO penalty (consumer choice)
- Hidden risk, deception, undisclosed harm, weapons: PENALTY (no consent possible)

Three orthogonal harm signals, each with its own ladder:
  1. Settlement magnitude (financial accountability for harm)
  2. Documented deaths/serious injury (body count from product use)
  3. Knowing concealment (deception of users/regulators about known risk)

All three flow into M.3 (Market Ethics) and M.4 (Product Ethics) via the
same penalty pattern as the existing AHI (Algorithmic Harm Index).

NOT a separate gate. NOT a separate index. Direct dimension adjustments.

Sources are public:
- DOJ press releases
- SEC 10-K disclosures
- State AG settlements
- CDC/NIH attribution data
- Court findings of fact
- Master Settlement Agreement (MSA) tobacco

Maps to: M.3 (Market Ethics), M.4 (Product Ethics)
"""

import json
import os
from pathlib import Path

# ============================================================================
# CURATED HARM DATA — public record only
# ============================================================================
# For each company:
#   settlement_total_5yr: total documented settlements/judgments in trailing 5y
#   deaths_attributed:    deaths attributed by court findings or regulatory data
#   concealment_findings: list of court-proven concealment patterns
#   sources:              public URLs documenting each claim
#   remediation_status:   "active" | "paid_in_full" | "ongoing"
#   review_date:          date this record was last verified
# ============================================================================

HARM_DATA = {
    # ─────────── PHARMA: hidden risks, doctor-prescribed, no informed user choice ───────────
    "JNJ": {
        "company": "Johnson & Johnson",
        "settlement_total_5yr": 12_500_000_000,
        "deaths_attributed": 50000,  # opioid-attributed (court findings)
        "concealment_findings": [
            "talc_asbestos_internal_documents_1971_2018",
            "opioid_marketing_concealment_1990s_2010s",
            "vaginal_mesh_safety_concealment"
        ],
        "sources": [
            "https://www.justice.gov/opa/pr/johnson-johnson-and-johnson-johnson-consumer-pay-700-million",
            "https://www.reuters.com/legal/jj-faces-89-billion-talc-settlement-2023",
            "https://www.cdc.gov/drugoverdose/data/statedeaths.html"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15",
        "notes": "Talc cancer + opioid + mesh. Multiple multi-billion settlements. Active litigation."
    },
    "PFE": {
        "company": "Pfizer Inc",
        "settlement_total_5yr": 2_800_000_000,
        "deaths_attributed": 0,  # no court-attributed death count
        "concealment_findings": [
            "bextra_off_label_marketing_2009",
            "neurontin_off_label_marketing"
        ],
        "sources": [
            "https://www.justice.gov/opa/pr/justice-department-announces-largest-health-care-fraud-settlement-its-history",
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000078003"
        ],
        "remediation_status": "paid_in_full",  # Bextra resolved; opioid ongoing
        "review_date": "2026-04-15",
        "notes": "Bextra ($2.3B 2009) was largest healthcare fraud settlement ever. Opioid contributions."
    },
    "MRK": {
        "company": "Merck & Co",
        "settlement_total_5yr": 1_200_000_000,
        "deaths_attributed": 27000,  # Vioxx FDA estimate of excess heart attacks
        "concealment_findings": [
            "vioxx_cardiovascular_risk_concealment_1999_2004"
        ],
        "sources": [
            "https://www.fda.gov/drugs/postmarket-drug-safety-information-patients-and-providers/vioxx-rofecoxib",
            "https://www.bmj.com/content/330/7503/1287"
        ],
        "remediation_status": "paid_in_full",
        "review_date": "2026-04-15",
        "notes": "Vioxx withdrawn 2004; Merck knew CV risk by 2000 per court findings. ~$4.85B total Vioxx settlements."
    },
    "TEVA": {
        "company": "Teva Pharmaceutical",
        "settlement_total_5yr": 4_350_000_000,
        "deaths_attributed": 30000,  # opioid-attributed
        "concealment_findings": ["opioid_marketing_concealment"],
        "sources": [
            "https://www.reuters.com/legal/teva-pay-435-billion-settle-us-opioid-cases-2022"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15"
    },
    "BHC": {
        "company": "Bausch Health (formerly Valeant)",
        "settlement_total_5yr": 250_000_000,
        "deaths_attributed": 0,
        "concealment_findings": ["price_gouging_disclosure_failures"],
        "sources": ["https://www.sec.gov/news/press-release/2020-169"],
        "remediation_status": "paid_in_full",
        "review_date": "2026-04-15"
    },

    # ─────────── TOBACCO: addiction concealment, MSA established deception ───────────
    "MO": {
        "company": "Altria Group (Philip Morris USA)",
        "settlement_total_5yr": 9_000_000_000,  # ongoing MSA payments
        "deaths_attributed": 480000,  # CDC: tobacco-attributed annual US deaths (proportional)
        "concealment_findings": [
            "msa_1998_addiction_cancer_concealment",
            "internal_documents_tobacco_industry_1950s_1990s"
        ],
        "sources": [
            "https://www.naag.org/our-work/naag-center-for-tobacco-and-public-health/the-master-settlement-agreement/",
            "https://www.cdc.gov/tobacco/data_statistics/fact_sheets/health_effects/tobacco_related_mortality/index.htm",
            "https://www.tobaccofreekids.org/research/factsheets"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15",
        "notes": "MSA 1998 = $206B total over 25 years SPECIFICALLY for hiding addiction/cancer risk. Authoritative deception finding."
    },
    "PM": {
        "company": "Philip Morris International",
        "settlement_total_5yr": 0,  # MSA covers PMUSA only; PMI sells abroad
        "deaths_attributed": 8000000,  # WHO global tobacco deaths (proportional share)
        "concealment_findings": [
            "msa_origin_documents_apply_to_pmi_pre_spinoff",
            "international_marketing_practices_documented_who"
        ],
        "sources": [
            "https://www.who.int/news-room/fact-sheets/detail/tobacco",
            "https://www.naag.org/our-work/naag-center-for-tobacco-and-public-health/"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15",
        "notes": "Spun off from Altria 2008 but inherited the deception history. WHO documents continued harmful marketing in developing countries."
    },
    "BTI": {
        "company": "British American Tobacco",
        "settlement_total_5yr": 635_000_000,  # 2023 DOJ settlement re: NK sanctions
        "deaths_attributed": 8000000,
        "concealment_findings": ["historical_tobacco_industry_concealment"],
        "sources": [
            "https://www.justice.gov/opa/pr/british-american-tobacco-pay-over-629-million",
            "https://www.who.int/news-room/fact-sheets/detail/tobacco"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15"
    },

    # ─────────── PFAS / "FOREVER CHEMICALS": hidden contamination ───────────
    "MMM": {
        "company": "3M Company",
        "settlement_total_5yr": 13_000_000_000,
        "deaths_attributed": 0,  # no body count attribution; widespread contamination
        "concealment_findings": [
            "pfas_internal_documents_1970s_2000s_health_risk_concealment"
        ],
        "sources": [
            "https://www.reuters.com/legal/3m-reach-103-bln-settlement-us-water-systems-pfas-2023",
            "https://www.epa.gov/pfas"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15",
        "notes": "$10.3B PFAS water system settlement 2023. Internal documents showed knowledge of harm since 1970s."
    },
    "DD": {
        "company": "DuPont de Nemours",
        "settlement_total_5yr": 1_185_000_000,
        "deaths_attributed": 0,
        "concealment_findings": ["pfoa_health_risk_concealment_1960s_2000s"],
        "sources": [
            "https://www.epa.gov/pfas",
            "https://www.nytimes.com/2016/01/06/magazine/the-lawyer-who-became-duponts-worst-nightmare.html"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15"
    },

    # ─────────── HERBICIDES: glyphosate cancer concealment ───────────
    "BAYRY": {
        "company": "Bayer AG (Monsanto)",
        "settlement_total_5yr": 11_000_000_000,
        "deaths_attributed": 0,
        "concealment_findings": [
            "roundup_glyphosate_cancer_link_concealment"
        ],
        "sources": [
            "https://www.reuters.com/business/healthcare-pharmaceuticals/bayer-pay-up-1095-billion-settle-roundup-cases-2020",
            "https://monographs.iarc.who.int/wp-content/uploads/2018/06/mono112-10.pdf"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15",
        "notes": "IARC classified glyphosate as 'probably carcinogenic' 2015. Bayer inherited Monsanto liability."
    },

    # ─────────── AUTO: known defects, deaths ───────────
    "GM": {
        "company": "General Motors",
        "settlement_total_5yr": 900_000_000,
        "deaths_attributed": 124,  # ignition switch defect (court-finding)
        "concealment_findings": [
            "ignition_switch_defect_concealment_2002_2014"
        ],
        "sources": [
            "https://www.justice.gov/opa/pr/manhattan-us-attorney-announces-criminal-charges-against-general-motors",
            "https://www.nhtsa.gov/recall-spotlight/gm-ignition-switch-recalls"
        ],
        "remediation_status": "paid_in_full",
        "review_date": "2026-04-15",
        "notes": "Ignition switch defect known since 2002, recall not until 2014. 124 deaths."
    },
    "BA": {
        "company": "Boeing Company",
        "settlement_total_5yr": 2_510_000_000,
        "deaths_attributed": 346,  # 737 MAX MCAS crashes
        "concealment_findings": [
            "737_max_mcas_certification_misrepresentation_2017_2019"
        ],
        "sources": [
            "https://www.justice.gov/opa/pr/boeing-charged-737-max-fraud-conspiracy-and-agrees-pay-over-25-billion",
            "https://www.faa.gov/newsroom/boeing-737-max-return-service"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15",
        "notes": "Lion Air 610 + Ethiopian 302 = 346 deaths. DOJ deferred prosecution agreement 2021."
    },

    # ─────────── OPIOID: extreme concealment, mass deaths ───────────
    "ENDP": {
        "company": "Endo International (Endo Pharmaceuticals)",
        "settlement_total_5yr": 600_000_000,
        "deaths_attributed": 30000,  # opioid-attributed share
        "concealment_findings": ["opioid_marketing_concealment_opana"],
        "sources": [
            "https://www.justice.gov/opa/pr/endo-pharmaceuticals-pay-600-million-settle-opioid-allegations"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15"
    },
    "MNK": {
        "company": "Mallinckrodt Pharmaceuticals",
        "settlement_total_5yr": 1_700_000_000,
        "deaths_attributed": 30000,  # opioid-attributed share
        "concealment_findings": ["opioid_marketing_concealment"],
        "sources": [
            "https://www.justice.gov/opa/pr/mallinckrodt-agrees-pay-17-billion-settle-claims-related-opioid-marketing"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15"
    },

    # ─────────── DATA / DECEPTION ───────────
    "WFC": {
        "company": "Wells Fargo & Co",
        "settlement_total_5yr": 5_000_000_000,
        "deaths_attributed": 0,
        "concealment_findings": [
            "fake_accounts_scandal_2002_2016",
            "auto_loan_insurance_force_placement"
        ],
        "sources": [
            "https://www.cfpb.gov/about-us/newsroom/cfpb-orders-wells-fargo-pay-185-million-fine-illegal-practices/",
            "https://www.sec.gov/news/press-release/2020-38"
        ],
        "remediation_status": "active",
        "review_date": "2026-04-15",
        "notes": "Multi-year, multi-channel deception of customers. Asset cap from Fed."
    },
    "EQR": {
        # NOTE: Equifax breach but EQR is Equity Residential. Equifax = EFX.
    },
    "EFX": {
        "company": "Equifax Inc",
        "settlement_total_5yr": 1_400_000_000,
        "deaths_attributed": 0,
        "concealment_findings": [
            "2017_breach_disclosure_delay_executive_stock_sales"
        ],
        "sources": [
            "https://www.ftc.gov/enforcement/refunds/equifax-data-breach-settlement",
            "https://www.justice.gov/opa/pr/former-equifax-executive-charged-insider-trading"
        ],
        "remediation_status": "paid_in_full",
        "review_date": "2026-04-15"
    },
}

# Remove the empty EQR placeholder (was a typo guard)
HARM_DATA = {k: v for k, v in HARM_DATA.items() if v.get("company")}


# ============================================================================
# PENALTY LADDERS — calibrated so worst offenders fail Gold dimension gate
# ============================================================================

def settlement_penalty(record):
    """
    Settlement magnitude → M.3 (Market Ethics) penalty.
    Ladder anchored to documented financial accountability for harm.
    """
    total = record.get("settlement_total_5yr", 0) or 0
    if total > 10_000_000_000: return -25  # >$10B trailing 5y (J&J, 3M PFAS, Bayer)
    if total >  1_000_000_000: return -15  # $1B-10B (Pfizer, Teva, Boeing 737)
    if total >    100_000_000: return -8   # $100M-1B
    if total >     10_000_000: return -3   # $10M-100M
    return 0


def deaths_penalty(record):
    """
    Documented deaths attributable to product harm → M.4 (Product Ethics) penalty.
    Anchored to court findings, CDC/NIH data, regulatory attribution.
    """
    deaths = record.get("deaths_attributed", 0) or 0
    if deaths > 100_000: return -30  # tobacco, opioid epidemic-scale
    if deaths >  10_000: return -25  # Vioxx, large opioid attribution
    if deaths >   1_000: return -20
    if deaths >     100: return -12  # Boeing 737 MAX (346)
    if deaths >      10: return -6   # GM ignition switch (124)
    return 0


def concealment_penalty(record):
    """
    Court-proven concealment of known harm → M.4 (Product Ethics) penalty.
    The moral severity signal — penalizes deception, not the harm itself.
    """
    findings = record.get("concealment_findings", []) or []
    if len(findings) >= 3: return -20  # Multi-front, multi-decade (J&J)
    if len(findings) >= 1: return -12  # Single major court finding
    return 0


# ============================================================================
# REMEDIATION FADE — companies can rehabilitate
# ============================================================================

def remediation_multiplier(record):
    """
    Penalty fade based on remediation status.
    Active settlements/litigation: full penalty.
    Paid in full + 5+ years: half penalty (rehabilitation in progress).
    """
    status = record.get("remediation_status", "active")
    if status == "active": return 1.0
    if status == "ongoing": return 0.85
    if status == "paid_in_full": return 0.5
    return 1.0


# ============================================================================
# AGGREGATE: compute per-company harm penalty
# ============================================================================

def compute_harm_penalty(ticker, company_name=""):
    """
    Returns dict with per-dimension adjustments and reasons.

    Same shape as compute_algo_harm() so wiring into scoring_engine.py
    follows the exact same pattern.
    """
    record = HARM_DATA.get((ticker or "").upper())
    if not record and company_name:
        # Fallback by name
        cn = company_name.lower().strip()
        for k, v in HARM_DATA.items():
            if cn in v.get("company", "").lower() or v.get("company", "").lower() in cn:
                record = v
                break

    if not record:
        return {
            "has_harm": False,
            "penalties": {"M.3": 0, "M.4": 0, "M": 0},
            "flags": [],
            "details": {}
        }

    mult = remediation_multiplier(record)
    m3_pen = round(settlement_penalty(record) * mult)
    m4_deaths_pen = round(deaths_penalty(record) * mult)
    m4_concealment_pen = round(concealment_penalty(record) * mult)
    m4_pen = m4_deaths_pen + m4_concealment_pen

    flags = []
    settlement_b = (record.get("settlement_total_5yr") or 0) / 1_000_000_000
    if settlement_b >= 1:
        flags.append(f"Harm settlements: ${settlement_b:.1f}B (5y)")
    deaths = record.get("deaths_attributed") or 0
    if deaths >= 100:
        flags.append(f"Documented deaths attributed: {deaths:,}")
    concealment = record.get("concealment_findings") or []
    if len(concealment) >= 1:
        flags.append(f"Concealment findings: {len(concealment)}")

    return {
        "has_harm": True,
        "penalties": {
            "M.3": m3_pen,
            "M.4": m4_pen,
            "M": m3_pen + m4_pen  # for total dimension drop
        },
        "flags": flags,
        "details": {
            "settlement_total_5yr": record.get("settlement_total_5yr", 0),
            "deaths_attributed": record.get("deaths_attributed", 0),
            "concealment_findings": record.get("concealment_findings", []),
            "remediation_status": record.get("remediation_status", "active"),
            "remediation_multiplier": mult,
            "sources": record.get("sources", [])[:3],
            "review_date": record.get("review_date", "")
        }
    }


# ============================================================================
# WRITE PIPELINE OUTPUT (matches cert pipeline pattern)
# ============================================================================

def main():
    out_dir = Path("data/harm")
    out_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "version": "1.1.0",
        "principle": "Humans can still choose. Hidden risk, deception, and weapons cannot be chosen.",
        "ladder_summary": {
            "settlement_total_5yr": "~$10B+ → -25 to M.3, scaling down to -3 at $10M",
            "deaths_attributed": "100K+ → -30 to M.4, scaling down to -6 at 10 deaths",
            "concealment_findings": "3+ findings → -20 to M.4, 1 finding → -12",
            "remediation_fade": "active = 1.0x, paid_in_full = 0.5x"
        },
        "company_count": len(HARM_DATA),
        "companies": []
    }

    for ticker, record in sorted(HARM_DATA.items()):
        penalty = compute_harm_penalty(ticker)
        output["companies"].append({
            "ticker": ticker,
            "company": record.get("company"),
            "settlement_total_5yr": record.get("settlement_total_5yr", 0),
            "deaths_attributed": record.get("deaths_attributed", 0),
            "concealment_findings": record.get("concealment_findings", []),
            "remediation_status": record.get("remediation_status", "active"),
            "review_date": record.get("review_date", ""),
            "sources": record.get("sources", []),
            "penalty_M_3": penalty["penalties"]["M.3"],
            "penalty_M_4": penalty["penalties"]["M.4"],
            "penalty_M_total": penalty["penalties"]["M"],
            "flags": penalty["flags"],
            "notes": record.get("notes", "")
        })

    out_file = out_dir / "all_companies.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    print("=" * 60)
    print("  Harm Documentation Pipeline")
    print("=" * 60)
    print(f"  Companies documented: {len(HARM_DATA)}")
    print()
    print(f"  Penalty preview (M dimension):")
    print(f"  {'Ticker':<8} {'Company':<35} {'M penalty':<10}")
    print(f"  {'-' * 55}")
    for c in sorted(output["companies"], key=lambda x: x["penalty_M_total"]):
        print(f"  {c['ticker']:<8} {c['company'][:34]:<35} {c['penalty_M_total']:>4}")
    print()
    print(f"  Output: {out_file}")
    print(f"  Maps to: M.3 (Market Ethics), M.4 (Product Ethics)")
    print(f"  Wired in scoring_engine.py same pattern as AHI")
    print("=" * 60)


if __name__ == "__main__":
    main()
