#!/usr/bin/env python3
"""
HI. — S&P 500 Company List
Complete ticker list for SEC EDGAR pipeline.
Run: python sp500_companies.py > data/sp500_tickers.json
"""

# S&P 500 companies as of early 2026
# Format: (ticker, company_name)
SP500 = [
    # Technology
    ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("GOOGL", "Alphabet (Google)"), ("AMZN", "Amazon"),
    ("META", "Meta Platforms"), ("NVDA", "NVIDIA"), ("AVGO", "Broadcom"), ("ORCL", "Oracle"),
    ("CRM", "Salesforce"), ("ADBE", "Adobe"), ("AMD", "AMD"), ("CSCO", "Cisco"),
    ("INTC", "Intel"), ("IBM", "IBM"), ("INTU", "Intuit"), ("NOW", "ServiceNow"),
    ("QCOM", "Qualcomm"), ("TXN", "Texas Instruments"), ("AMAT", "Applied Materials"),
    ("ADI", "Analog Devices"), ("LRCX", "Lam Research"), ("KLAC", "KLA Corporation"),
    ("SNPS", "Synopsys"), ("CDNS", "Cadence Design"), ("MRVL", "Marvell Technology"),
    ("FTNT", "Fortinet"), ("PANW", "Palo Alto Networks"), ("CRWD", "CrowdStrike"),
    ("NFLX", "Netflix"), ("SPOT", "Spotify"), ("PLTR", "Palantir"),
    ("UBER", "Uber"), ("ABNB", "Airbnb"), ("SQ", "Block (Square)"),
    ("SHOP", "Shopify"), ("ZM", "Zoom"), ("COIN", "Coinbase"),
    ("SNOW", "Snowflake"), ("DDOG", "Datadog"), ("MDB", "MongoDB"),
    ("WDAY", "Workday"), ("TEAM", "Atlassian"), ("HUBS", "HubSpot"),
    ("TTD", "The Trade Desk"), ("RBLX", "Roblox"), ("U", "Unity Software"),
    ("ZS", "Zscaler"), ("NET", "Cloudflare"), ("OKTA", "Okta"),
    ("TWLO", "Twilio"), ("DOCU", "DocuSign"), ("BILL", "Bill Holdings"),

    # Financials
    ("JPM", "JPMorgan Chase"), ("BAC", "Bank of America"), ("WFC", "Wells Fargo"),
    ("GS", "Goldman Sachs"), ("MS", "Morgan Stanley"), ("C", "Citigroup"),
    ("BLK", "BlackRock"), ("SCHW", "Charles Schwab"), ("AXP", "American Express"),
    ("V", "Visa"), ("MA", "Mastercard"), ("PYPL", "PayPal"),
    ("COF", "Capital One"), ("USB", "U.S. Bancorp"), ("PNC", "PNC Financial"),
    ("TFC", "Truist Financial"), ("BK", "Bank of New York Mellon"),
    ("STT", "State Street"), ("FIS", "Fidelity National Info"), ("FISV", "Fiserv"),
    ("AIG", "American International Group"), ("MET", "MetLife"), ("PRU", "Prudential Financial"),
    ("ALL", "Allstate"), ("TRV", "Travelers"), ("CB", "Chubb"),
    ("MMC", "Marsh McLennan"), ("AON", "Aon"), ("ICE", "Intercontinental Exchange"),
    ("CME", "CME Group"), ("SPGI", "S&P Global"), ("MCO", "Moody's"),
    ("MSCI", "MSCI"),

    # Healthcare
    ("UNH", "UnitedHealth"), ("JNJ", "Johnson & Johnson"), ("LLY", "Eli Lilly"),
    ("PFE", "Pfizer"), ("ABBV", "AbbVie"), ("MRK", "Merck"),
    ("TMO", "Thermo Fisher Scientific"), ("ABT", "Abbott Laboratories"),
    ("DHR", "Danaher"), ("BMY", "Bristol-Myers Squibb"), ("AMGN", "Amgen"),
    ("GILD", "Gilead Sciences"), ("VRTX", "Vertex Pharmaceuticals"),
    ("REGN", "Regeneron"), ("ISRG", "Intuitive Surgical"), ("EW", "Edwards Lifesciences"),
    ("DXCM", "DexCom"), ("IDXX", "IDEXX Laboratories"), ("ZTS", "Zoetis"),
    ("SYK", "Stryker"), ("BDX", "Becton Dickinson"), ("BSX", "Boston Scientific"),
    ("MDT", "Medtronic"), ("HCA", "HCA Healthcare"), ("CVS", "CVS Health"),
    ("CI", "Cigna"), ("ELV", "Elevance Health"), ("HUM", "Humana"),
    ("CNC", "Centene"), ("MCK", "McKesson"), ("CAH", "Cardinal Health"),

    # Consumer Discretionary
    ("TSLA", "Tesla"), ("HD", "Home Depot"), ("LOW", "Lowe's"),
    ("MCD", "McDonald's"), ("SBUX", "Starbucks"), ("NKE", "Nike"),
    ("TJX", "TJX Companies"), ("ROST", "Ross Stores"), ("BKNG", "Booking Holdings"),
    ("MAR", "Marriott"), ("HLT", "Hilton"), ("CMG", "Chipotle"),
    ("YUM", "Yum! Brands"), ("DRI", "Darden Restaurants"), ("DPZ", "Domino's Pizza"),
    ("ORLY", "O'Reilly Automotive"), ("AZO", "AutoZone"), ("BBY", "Best Buy"),
    ("ETSY", "Etsy"), ("EBAY", "eBay"), ("W", "Wayfair"),
    ("GM", "General Motors"), ("F", "Ford"), ("APTV", "Aptiv"),
    ("LEN", "Lennar"), ("DHI", "D.R. Horton"), ("PHM", "PulteGroup"),
    ("GPC", "Genuine Parts"), ("POOL", "Pool Corporation"),
    ("RCL", "Royal Caribbean"), ("CCL", "Carnival"), ("NCLH", "Norwegian Cruise Line"),
    ("DIS", "Walt Disney"), ("CMCSA", "Comcast"), ("CHTR", "Charter Communications"),
    ("PARA", "Paramount Global"), ("WBD", "Warner Bros Discovery"),
    ("LVS", "Las Vegas Sands"), ("MGM", "MGM Resorts"), ("WYNN", "Wynn Resorts"),

    # Consumer Staples
    ("PG", "Procter & Gamble"), ("KO", "Coca-Cola"), ("PEP", "PepsiCo"),
    ("COST", "Costco"), ("WMT", "Walmart"), ("TGT", "Target"),
    ("CL", "Colgate-Palmolive"), ("KMB", "Kimberly-Clark"), ("MDLZ", "Mondelez"),
    ("GIS", "General Mills"), ("K", "Kellanova"), ("HSY", "Hershey"),
    ("SJM", "J.M. Smucker"), ("CPB", "Campbell Soup"), ("HRL", "Hormel Foods"),
    ("MKC", "McCormick"), ("STZ", "Constellation Brands"), ("BF.B", "Brown-Forman"),
    ("TAP", "Molson Coors"), ("SAM", "Boston Beer"), ("MNST", "Monster Beverage"),
    ("KR", "Kroger"), ("SYY", "Sysco"), ("ADM", "Archer-Daniels-Midland"),
    ("TSN", "Tyson Foods"), ("KHC", "Kraft Heinz"), ("CAG", "Conagra Brands"),
    ("PM", "Philip Morris"), ("MO", "Altria"), ("CLX", "Clorox"),
    ("EL", "Estee Lauder"), ("CHD", "Church & Dwight"),

    # Energy
    ("XOM", "ExxonMobil"), ("CVX", "Chevron"), ("COP", "ConocoPhillips"),
    ("EOG", "EOG Resources"), ("SLB", "Schlumberger"), ("PXD", "Pioneer Natural Resources"),
    ("MPC", "Marathon Petroleum"), ("VLO", "Valero Energy"), ("PSX", "Phillips 66"),
    ("OXY", "Occidental Petroleum"), ("DVN", "Devon Energy"), ("FANG", "Diamondback Energy"),
    ("HAL", "Halliburton"), ("BKR", "Baker Hughes"), ("CTRA", "Coterra Energy"),
    ("WMB", "Williams Companies"), ("KMI", "Kinder Morgan"), ("OKE", "ONEOK"),
    ("TRGP", "Targa Resources"),

    # Industrials
    ("BA", "Boeing"), ("LMT", "Lockheed Martin"), ("RTX", "RTX (Raytheon)"),
    ("NOC", "Northrop Grumman"), ("GD", "General Dynamics"), ("HII", "Huntington Ingalls"),
    ("CAT", "Caterpillar"), ("DE", "John Deere"), ("HON", "Honeywell"),
    ("GE", "GE Aerospace"), ("MMM", "3M"), ("EMR", "Emerson Electric"),
    ("ITW", "Illinois Tool Works"), ("ROK", "Rockwell Automation"),
    ("ETN", "Eaton"), ("PH", "Parker-Hannifin"), ("CMI", "Cummins"),
    ("PCAR", "PACCAR"), ("FDX", "FedEx"), ("UPS", "United Parcel Service"),
    ("UNP", "Union Pacific"), ("CSX", "CSX"), ("NSC", "Norfolk Southern"),
    ("DAL", "Delta Air Lines"), ("UAL", "United Airlines"), ("LUV", "Southwest Airlines"),
    ("AAL", "American Airlines"), ("WM", "Waste Management"), ("RSG", "Republic Services"),
    ("JCI", "Johnson Controls"), ("TT", "Trane Technologies"), ("CARR", "Carrier Global"),
    ("VRSK", "Verisk Analytics"), ("IR", "Ingersoll Rand"), ("DOV", "Dover"),
    ("SWK", "Stanley Black & Decker"), ("GWW", "W.W. Grainger"),
    ("FAST", "Fastenal"), ("CPRT", "Copart"), ("ODFL", "Old Dominion Freight"),
    ("CTAS", "Cintas"), ("PAYX", "Paychex"), ("ADP", "Automatic Data Processing"),

    # Utilities
    ("NEE", "NextEra Energy"), ("DUK", "Duke Energy"), ("SO", "Southern Company"),
    ("D", "Dominion Energy"), ("AEP", "American Electric Power"), ("EXC", "Exelon"),
    ("XEL", "Xcel Energy"), ("SRE", "Sempra"), ("ED", "Consolidated Edison"),
    ("WEC", "WEC Energy"), ("ES", "Eversource Energy"), ("DTE", "DTE Energy"),
    ("FE", "FirstEnergy"), ("AEE", "Ameren"), ("CMS", "CMS Energy"),
    ("PEG", "PSEG"), ("AWK", "American Water Works"), ("ATO", "Atmos Energy"),

    # Real Estate
    ("PLD", "Prologis"), ("AMT", "American Tower"), ("CCI", "Crown Castle"),
    ("EQIX", "Equinix"), ("PSA", "Public Storage"), ("O", "Realty Income"),
    ("SPG", "Simon Property Group"), ("WELL", "Welltower"), ("DLR", "Digital Realty"),
    ("AVB", "AvalonBay"), ("EQR", "Equity Residential"), ("VICI", "VICI Properties"),
    ("IRM", "Iron Mountain"), ("MAA", "Mid-America Apartment"), ("ARE", "Alexandria Real Estate"),

    # Materials
    ("LIN", "Linde"), ("APD", "Air Products"), ("SHW", "Sherwin-Williams"),
    ("ECL", "Ecolab"), ("FCX", "Freeport-McMoRan"), ("NEM", "Newmont"),
    ("NUE", "Nucor"), ("STLD", "Steel Dynamics"), ("VMC", "Vulcan Materials"),
    ("MLM", "Martin Marietta"), ("DOW", "Dow"), ("DD", "DuPont"),
    ("PPG", "PPG Industries"), ("CE", "Celanese"), ("CF", "CF Industries"),
    ("MOS", "Mosaic"), ("ALB", "Albemarle"), ("IFF", "IFF"),
    ("PKG", "Packaging Corp"), ("IP", "International Paper"), ("BLL", "Ball Corporation"),

    # Communication Services
    ("T", "AT&T"), ("VZ", "Verizon"), ("TMUS", "T-Mobile"),
    ("ATVI", "Activision Blizzard"), ("EA", "Electronic Arts"), ("TTWO", "Take-Two Interactive"),
    ("MTCH", "Match Group"), ("ZG", "Zillow"), ("PINS", "Pinterest"),
    ("SNAP", "Snap"), ("ROKU", "Roku"),
]

if __name__ == "__main__":
    import json
    print(json.dumps([{"ticker": t, "name": n} for t, n in SP500], indent=2))
    print(f"\n# Total: {len(SP500)} companies", file=__import__('sys').stderr)
