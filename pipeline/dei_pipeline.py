#!/usr/bin/env python3
"""
AAPD / Disability:IN — Disability Equality Index Pipeline
Source: Public "Best Places to Work" announcements (2024)
URL: https://disabilityin.org/what-we-do/disability-equality-index/

Scores 0-100. Companies scoring 80+ are publicly recognized.
- 343 companies scored 100
- 87 companies scored 90
- 54 companies scored 80
- Companies below 80 or not participating: unknown (neutral default)

Maps to HUMAN dimensions: U (Understanding & Empathy), M (Moral & Ethical Conduct)
"""

import json, os
from pathlib import Path

# Companies publicly recognized as "Best Places to Work for Disability Inclusion" (2024)
# Source: Press releases, DirectEmployers list, company announcements
# Score tiers: 100, 90, 80. Non-participants get None (neutral).

DEI_COMPANIES = [
    # Score 100 — Top scorers (343 companies total, major ones listed)
    {"company": "Accenture", "ticker": "ACN", "dei_score": 100},
    {"company": "Adobe", "ticker": "ADBE", "dei_score": 100},
    {"company": "ADP", "ticker": "ADP", "dei_score": 100},
    {"company": "Aetna (CVS Health)", "ticker": "CVS", "dei_score": 100},
    {"company": "Allstate", "ticker": "ALL", "dei_score": 100},
    {"company": "Amazon", "ticker": "AMZN", "dei_score": 100},
    {"company": "American Express", "ticker": "AXP", "dei_score": 100},
    {"company": "Apple", "ticker": "AAPL", "dei_score": 100},
    {"company": "AT&T", "ticker": "T", "dei_score": 100},
    {"company": "Bank of America", "ticker": "BAC", "dei_score": 100},
    {"company": "Bayer", "ticker": "BAYRY", "dei_score": 100},
    {"company": "Best Buy", "ticker": "BBY", "dei_score": 100},
    {"company": "Boeing", "ticker": "BA", "dei_score": 100},
    {"company": "Capital One", "ticker": "COF", "dei_score": 100},
    {"company": "Chevron", "ticker": "CVX", "dei_score": 100},
    {"company": "Cigna", "ticker": "CI", "dei_score": 100},
    {"company": "Cisco", "ticker": "CSCO", "dei_score": 100},
    {"company": "Citi", "ticker": "C", "dei_score": 100},
    {"company": "Coca-Cola", "ticker": "KO", "dei_score": 100},
    {"company": "Comcast", "ticker": "CMCSA", "dei_score": 100},
    {"company": "Dell Technologies", "ticker": "DELL", "dei_score": 100},
    {"company": "Deloitte", "ticker": None, "dei_score": 100},
    {"company": "Delta Air Lines", "ticker": "DAL", "dei_score": 100},
    {"company": "Dow", "ticker": "DOW", "dei_score": 100},
    {"company": "Edward Jones", "ticker": None, "dei_score": 100},
    {"company": "Eli Lilly", "ticker": "LLY", "dei_score": 100},
    {"company": "Ernst & Young", "ticker": None, "dei_score": 100},
    {"company": "Experian", "ticker": "EXPGY", "dei_score": 100},
    {"company": "EY", "ticker": None, "dei_score": 100},
    {"company": "Fidelity", "ticker": None, "dei_score": 100},
    {"company": "General Motors", "ticker": "GM", "dei_score": 100},
    {"company": "Google", "ticker": "GOOGL", "dei_score": 100},
    {"company": "Guardian Life", "ticker": None, "dei_score": 100},
    {"company": "Hilton", "ticker": "HLT", "dei_score": 100},
    {"company": "HP", "ticker": "HPQ", "dei_score": 100},
    {"company": "HPE", "ticker": "HPE", "dei_score": 100},
    {"company": "Humana", "ticker": "HUM", "dei_score": 100},
    {"company": "IBM", "ticker": "IBM", "dei_score": 100},
    {"company": "Intel", "ticker": "INTC", "dei_score": 100},
    {"company": "Johnson & Johnson", "ticker": "JNJ", "dei_score": 100},
    {"company": "JPMorgan Chase", "ticker": "JPM", "dei_score": 100},
    {"company": "Kaiser Permanente", "ticker": None, "dei_score": 100},
    {"company": "KPMG", "ticker": None, "dei_score": 100},
    {"company": "Lenovo", "ticker": "LNVGY", "dei_score": 100},
    {"company": "Lockheed Martin", "ticker": "LMT", "dei_score": 100},
    {"company": "Lowe's", "ticker": "LOW", "dei_score": 100},
    {"company": "Mastercard", "ticker": "MA", "dei_score": 100},
    {"company": "Merck", "ticker": "MRK", "dei_score": 100},
    {"company": "Meta", "ticker": "META", "dei_score": 100},
    {"company": "Microsoft", "ticker": "MSFT", "dei_score": 100},
    {"company": "Morgan Stanley", "ticker": "MS", "dei_score": 100},
    {"company": "Nationwide", "ticker": None, "dei_score": 100},
    {"company": "Nike", "ticker": "NKE", "dei_score": 100},
    {"company": "Northrop Grumman", "ticker": "NOC", "dei_score": 100},
    {"company": "Oracle", "ticker": "ORCL", "dei_score": 100},
    {"company": "PepsiCo", "ticker": "PEP", "dei_score": 100},
    {"company": "Pfizer", "ticker": "PFE", "dei_score": 100},
    {"company": "Procter & Gamble", "ticker": "PG", "dei_score": 100},
    {"company": "PwC", "ticker": None, "dei_score": 100},
    {"company": "Raytheon (RTX)", "ticker": "RTX", "dei_score": 100},
    {"company": "Salesforce", "ticker": "CRM", "dei_score": 100},
    {"company": "SAP", "ticker": "SAP", "dei_score": 100},
    {"company": "SAS", "ticker": None, "dei_score": 100},
    {"company": "Starbucks", "ticker": "SBUX", "dei_score": 100},
    {"company": "T-Mobile", "ticker": "TMUS", "dei_score": 100},
    {"company": "Target", "ticker": "TGT", "dei_score": 100},
    {"company": "TD Bank", "ticker": "TD", "dei_score": 100},
    {"company": "Toyota", "ticker": "TM", "dei_score": 100},
    {"company": "U.S. Bank", "ticker": "USB", "dei_score": 100},
    {"company": "UnitedHealth Group", "ticker": "UNH", "dei_score": 100},
    {"company": "Verizon", "ticker": "VZ", "dei_score": 100},
    {"company": "Visa", "ticker": "V", "dei_score": 100},
    {"company": "Walmart", "ticker": "WMT", "dei_score": 100},
    {"company": "Walt Disney", "ticker": "DIS", "dei_score": 100},
    {"company": "Wells Fargo", "ticker": "WFC", "dei_score": 100},

    # Score 90 — Strong performers (87 companies total, major ones listed)
    {"company": "3M", "ticker": "MMM", "dei_score": 90},
    {"company": "Abbott", "ticker": "ABT", "dei_score": 90},
    {"company": "AbbVie", "ticker": "ABBV", "dei_score": 90},
    {"company": "Bristol-Myers Squibb", "ticker": "BMY", "dei_score": 90},
    {"company": "Caterpillar", "ticker": "CAT", "dei_score": 90},
    {"company": "FedEx", "ticker": "FDX", "dei_score": 90},
    {"company": "General Electric", "ticker": "GE", "dei_score": 90},
    {"company": "Goldman Sachs", "ticker": "GS", "dei_score": 90},
    {"company": "Honeywell", "ticker": "HON", "dei_score": 90},
    {"company": "John Deere", "ticker": "DE", "dei_score": 90},
    {"company": "Medtronic", "ticker": "MDT", "dei_score": 90},
    {"company": "Nasdaq", "ticker": "NDAQ", "dei_score": 90},
    {"company": "PayPal", "ticker": "PYPL", "dei_score": 90},
    {"company": "Qualcomm", "ticker": "QCOM", "dei_score": 90},
    {"company": "Uber", "ticker": "UBER", "dei_score": 90},

    # Score 80 — Good performers (54 companies total, major ones listed)
    {"company": "Costco", "ticker": "COST", "dei_score": 80},
    {"company": "Netflix", "ticker": "NFLX", "dei_score": 80},
    {"company": "Spotify", "ticker": "SPOT", "dei_score": 80},
]


def run_pipeline():
    output_dir = Path("data/dei")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for c in DEI_COMPANIES:
        records.append({
            "company": c["company"],
            "ticker": c.get("ticker"),
            "dei_score": c["dei_score"],
            "dei_tier": "Best Place to Work" if c["dei_score"] >= 80 else "Participant",
            "dei_year": 2024,
            "source": "AAPD/Disability:IN Disability Equality Index",
            "source_url": "https://disabilityin.org/what-we-do/disability-equality-index/",
        })

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  AAPD / Disability Equality Index Pipeline")
    print(f"{'='*60}")
    print(f"  Companies with public scores: {len(records)}")
    print(f"    Score 100: {sum(1 for r in records if r['dei_score'] == 100)}")
    print(f"    Score 90:  {sum(1 for r in records if r['dei_score'] == 90)}")
    print(f"    Score 80:  {sum(1 for r in records if r['dei_score'] == 80)}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: U (Understanding & Empathy), M (Moral & Ethical Conduct)")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
