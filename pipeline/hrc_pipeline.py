#!/usr/bin/env python3
"""
HRC — Human Rights Campaign Corporate Equality Index Pipeline
Source: Public "Equality 100" lists (2023-2024 and 2026 CEI)
URL: https://www.hrc.org/resources/corporate-equality-index

Scores 0-100 on LGBTQ+ workplace inclusion.
- 765 companies scored 100 (2025 CEI)
- 545 companies scored 100 (2023-2024 CEI)
- 1,384 total participants (2023-2024)
- Companies scoring 100 earn "Equality 100 Award"

Maps to HUMAN dimensions: U (Understanding & Empathy), M (Moral & Ethical Conduct)
"""

import json, os
from pathlib import Path

# Companies publicly recognized with top CEI scores
# Source: HRC press releases, company announcements, CEI reports
# Using most recent publicly available scores

HRC_COMPANIES = [
    # Equality 100 Award winners — score 100
    {"company": "3M", "ticker": "MMM", "cei_score": 100},
    {"company": "Abbott", "ticker": "ABT", "cei_score": 100},
    {"company": "AbbVie", "ticker": "ABBV", "cei_score": 100},
    {"company": "Accenture", "ticker": "ACN", "cei_score": 100},
    {"company": "Adobe", "ticker": "ADBE", "cei_score": 100},
    {"company": "ADP", "ticker": "ADP", "cei_score": 100},
    {"company": "Airbnb", "ticker": "ABNB", "cei_score": 100},
    {"company": "Allstate", "ticker": "ALL", "cei_score": 100},
    {"company": "Alphabet (Google)", "ticker": "GOOGL", "cei_score": 100},
    {"company": "Amazon", "ticker": "AMZN", "cei_score": 100},
    {"company": "American Airlines", "ticker": "AAL", "cei_score": 100},
    {"company": "American Express", "ticker": "AXP", "cei_score": 100},
    {"company": "Amgen", "ticker": "AMGN", "cei_score": 100},
    {"company": "Apple", "ticker": "AAPL", "cei_score": 100},
    {"company": "AT&T", "ticker": "T", "cei_score": 100},
    {"company": "Bank of America", "ticker": "BAC", "cei_score": 100},
    {"company": "Bayer", "ticker": "BAYRY", "cei_score": 100},
    {"company": "Best Buy", "ticker": "BBY", "cei_score": 100},
    {"company": "BlackRock", "ticker": "BLK", "cei_score": 100},
    {"company": "Bloomberg", "ticker": None, "cei_score": 100},
    {"company": "Boeing", "ticker": "BA", "cei_score": 100},
    {"company": "Bristol-Myers Squibb", "ticker": "BMY", "cei_score": 100},
    {"company": "Capital One", "ticker": "COF", "cei_score": 100},
    {"company": "Chevron", "ticker": "CVX", "cei_score": 100},
    {"company": "Cigna", "ticker": "CI", "cei_score": 100},
    {"company": "Cisco", "ticker": "CSCO", "cei_score": 100},
    {"company": "Citi", "ticker": "C", "cei_score": 100},
    {"company": "Coca-Cola", "ticker": "KO", "cei_score": 100},
    {"company": "Colgate-Palmolive", "ticker": "CL", "cei_score": 100},
    {"company": "Comcast", "ticker": "CMCSA", "cei_score": 100},
    {"company": "ConocoPhillips", "ticker": "COP", "cei_score": 100},
    {"company": "Costco", "ticker": "COST", "cei_score": 100},
    {"company": "Cummins", "ticker": "CMI", "cei_score": 100},
    {"company": "CVS Health", "ticker": "CVS", "cei_score": 100},
    {"company": "Deloitte", "ticker": None, "cei_score": 100},
    {"company": "Dell Technologies", "ticker": "DELL", "cei_score": 100},
    {"company": "Delta Air Lines", "ticker": "DAL", "cei_score": 100},
    {"company": "Dow", "ticker": "DOW", "cei_score": 100},
    {"company": "Eli Lilly", "ticker": "LLY", "cei_score": 100},
    {"company": "Ernst & Young", "ticker": None, "cei_score": 100},
    {"company": "Estee Lauder", "ticker": "EL", "cei_score": 100},
    {"company": "Exelon", "ticker": "EXC", "cei_score": 100},
    {"company": "ExxonMobil", "ticker": "XOM", "cei_score": 100},
    {"company": "FedEx", "ticker": "FDX", "cei_score": 100},
    {"company": "Fidelity", "ticker": None, "cei_score": 100},
    {"company": "Ford Motor", "ticker": "F", "cei_score": 100},
    {"company": "Gap", "ticker": "GAP", "cei_score": 100},
    {"company": "General Electric", "ticker": "GE", "cei_score": 100},
    {"company": "General Mills", "ticker": "GIS", "cei_score": 100},
    {"company": "General Motors", "ticker": "GM", "cei_score": 100},
    {"company": "Goldman Sachs", "ticker": "GS", "cei_score": 100},
    {"company": "Guardian Life", "ticker": None, "cei_score": 100},
    {"company": "Hilton", "ticker": "HLT", "cei_score": 100},
    {"company": "Home Depot", "ticker": "HD", "cei_score": 100},
    {"company": "Honeywell", "ticker": "HON", "cei_score": 100},
    {"company": "HP", "ticker": "HPQ", "cei_score": 100},
    {"company": "HPE", "ticker": "HPE", "cei_score": 100},
    {"company": "IBM", "ticker": "IBM", "cei_score": 100},
    {"company": "Intel", "ticker": "INTC", "cei_score": 100},
    {"company": "Intuit", "ticker": "INTU", "cei_score": 100},
    {"company": "Johnson & Johnson", "ticker": "JNJ", "cei_score": 100},
    {"company": "JPMorgan Chase", "ticker": "JPM", "cei_score": 100},
    {"company": "Kaiser Permanente", "ticker": None, "cei_score": 100},
    {"company": "Kellogg", "ticker": "K", "cei_score": 100},
    {"company": "KPMG", "ticker": None, "cei_score": 100},
    {"company": "Lam Research", "ticker": "LRCX", "cei_score": 100},
    {"company": "Levi Strauss", "ticker": "LEVI", "cei_score": 100},
    {"company": "Lockheed Martin", "ticker": "LMT", "cei_score": 100},
    {"company": "Lowe's", "ticker": "LOW", "cei_score": 100},
    {"company": "Lyft", "ticker": "LYFT", "cei_score": 100},
    {"company": "Marriott", "ticker": "MAR", "cei_score": 100},
    {"company": "Mastercard", "ticker": "MA", "cei_score": 100},
    {"company": "McDonald's", "ticker": "MCD", "cei_score": 100},
    {"company": "Medtronic", "ticker": "MDT", "cei_score": 100},
    {"company": "Merck", "ticker": "MRK", "cei_score": 100},
    {"company": "Meta", "ticker": "META", "cei_score": 100},
    {"company": "MetLife", "ticker": "MET", "cei_score": 100},
    {"company": "Microsoft", "ticker": "MSFT", "cei_score": 100},
    {"company": "Morgan Stanley", "ticker": "MS", "cei_score": 100},
    {"company": "Netflix", "ticker": "NFLX", "cei_score": 100},
    {"company": "Nike", "ticker": "NKE", "cei_score": 100},
    {"company": "Northrop Grumman", "ticker": "NOC", "cei_score": 100},
    {"company": "Oracle", "ticker": "ORCL", "cei_score": 100},
    {"company": "PayPal", "ticker": "PYPL", "cei_score": 100},
    {"company": "PepsiCo", "ticker": "PEP", "cei_score": 100},
    {"company": "Pfizer", "ticker": "PFE", "cei_score": 100},
    {"company": "Procter & Gamble", "ticker": "PG", "cei_score": 100},
    {"company": "Prudential", "ticker": "PRU", "cei_score": 100},
    {"company": "PwC", "ticker": None, "cei_score": 100},
    {"company": "Qualcomm", "ticker": "QCOM", "cei_score": 100},
    {"company": "Raytheon (RTX)", "ticker": "RTX", "cei_score": 100},
    {"company": "Salesforce", "ticker": "CRM", "cei_score": 100},
    {"company": "SAP", "ticker": "SAP", "cei_score": 100},
    {"company": "Starbucks", "ticker": "SBUX", "cei_score": 100},
    {"company": "Synchrony", "ticker": "SYF", "cei_score": 100},
    {"company": "T-Mobile", "ticker": "TMUS", "cei_score": 100},
    {"company": "Target", "ticker": "TGT", "cei_score": 100},
    {"company": "TD Bank", "ticker": "TD", "cei_score": 100},
    {"company": "Toyota", "ticker": "TM", "cei_score": 100},
    {"company": "Uber", "ticker": "UBER", "cei_score": 100},
    {"company": "U.S. Bank", "ticker": "USB", "cei_score": 100},
    {"company": "UnitedHealth Group", "ticker": "UNH", "cei_score": 100},
    {"company": "Verizon", "ticker": "VZ", "cei_score": 100},
    {"company": "Visa", "ticker": "V", "cei_score": 100},
    {"company": "Walmart", "ticker": "WMT", "cei_score": 100},
    {"company": "Walt Disney", "ticker": "DIS", "cei_score": 100},
    {"company": "Wells Fargo", "ticker": "WFC", "cei_score": 100},
    {"company": "Xerox", "ticker": "XRX", "cei_score": 100},
    {"company": "Zillow", "ticker": "Z", "cei_score": 100},
    {"company": "Zoom", "ticker": "ZM", "cei_score": 100},
]


def run_pipeline():
    output_dir = Path("data/hrc")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for c in HRC_COMPANIES:
        records.append({
            "company": c["company"],
            "ticker": c.get("ticker"),
            "cei_score": c["cei_score"],
            "cei_award": "Equality 100" if c["cei_score"] == 100 else None,
            "cei_year": 2024,
            "source": "HRC Corporate Equality Index",
            "source_url": "https://www.hrc.org/resources/corporate-equality-index",
        })

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  HRC Corporate Equality Index Pipeline")
    print(f"{'='*60}")
    print(f"  Companies with public scores: {len(records)}")
    print(f"    Score 100: {sum(1 for r in records if r['cei_score'] == 100)}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: U (Understanding & Empathy), M (Moral & Ethical Conduct)")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
