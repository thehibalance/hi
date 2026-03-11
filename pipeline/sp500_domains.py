#!/usr/bin/env python3
"""
HI. — S&P 500 Domain Mapping
Maps company tickers to website domains for the API.

Usage:
  python sp500_domains.py                    # Print JSON mapping
  python sp500_domains.py --inject           # Inject domains into scored data
"""

# Ticker -> list of domains
DOMAIN_MAP = {
    # Technology
    "AAPL": ["apple.com", "icloud.com", "itunes.apple.com"],
    "MSFT": ["microsoft.com", "office.com", "azure.com", "linkedin.com", "github.com", "bing.com"],
    "GOOGL": ["google.com", "youtube.com", "gmail.com", "android.com", "cloud.google.com", "waymo.com"],
    "AMZN": ["amazon.com", "aws.amazon.com", "wholefoodsmarket.com", "twitch.tv", "imdb.com", "audible.com"],
    "META": ["meta.com", "facebook.com", "instagram.com", "whatsapp.com", "threads.net", "oculus.com"],
    "NVDA": ["nvidia.com"],
    "AVGO": ["broadcom.com"],
    "ORCL": ["oracle.com"],
    "CRM": ["salesforce.com", "slack.com", "heroku.com", "tableau.com", "mulesoft.com"],
    "ADBE": ["adobe.com", "behance.net", "figma.com"],
    "AMD": ["amd.com"],
    "CSCO": ["cisco.com", "webex.com"],
    "INTC": ["intel.com"],
    "IBM": ["ibm.com", "redhat.com"],
    "INTU": ["intuit.com", "turbotax.com", "quickbooks.com", "mailchimp.com", "creditkarma.com"],
    "NOW": ["servicenow.com"],
    "QCOM": ["qualcomm.com"],
    "TXN": ["ti.com"],
    "AMAT": ["appliedmaterials.com"],
    "ADI": ["analog.com"],
    "LRCX": ["lamresearch.com"],
    "KLAC": ["kla.com"],
    "SNPS": ["synopsys.com"],
    "CDNS": ["cadence.com"],
    "MRVL": ["marvell.com"],
    "FTNT": ["fortinet.com"],
    "PANW": ["paloaltonetworks.com"],
    "CRWD": ["crowdstrike.com"],
    "NFLX": ["netflix.com"],
    "SPOT": ["spotify.com"],
    "PLTR": ["palantir.com"],
    "UBER": ["uber.com", "ubereats.com"],
    "ABNB": ["airbnb.com"],
    "SQ": ["squareup.com", "block.xyz", "cash.app", "tidal.com"],
    "SHOP": ["shopify.com"],
    "ZM": ["zoom.us"],
    "COIN": ["coinbase.com"],
    "SNOW": ["snowflake.com"],
    "DDOG": ["datadoghq.com"],
    "MDB": ["mongodb.com"],
    "WDAY": ["workday.com"],
    "TEAM": ["atlassian.com", "bitbucket.org", "trello.com", "jira.com"],
    "HUBS": ["hubspot.com"],
    "TTD": ["thetradedesk.com"],
    "RBLX": ["roblox.com"],
    "U": ["unity.com"],
    "ZS": ["zscaler.com"],
    "NET": ["cloudflare.com"],
    "OKTA": ["okta.com"],
    "TWLO": ["twilio.com"],
    "DOCU": ["docusign.com"],
    "BILL": ["bill.com"],

    # Financials
    "JPM": ["jpmorganchase.com", "chase.com"],
    "BAC": ["bankofamerica.com"],
    "WFC": ["wellsfargo.com"],
    "GS": ["goldmansachs.com", "marcus.com"],
    "MS": ["morganstanley.com"],
    "C": ["citigroup.com", "citi.com"],
    "BLK": ["blackrock.com"],
    "SCHW": ["schwab.com"],
    "AXP": ["americanexpress.com"],
    "V": ["visa.com"],
    "MA": ["mastercard.com"],
    "PYPL": ["paypal.com", "venmo.com"],
    "COF": ["capitalone.com"],
    "USB": ["usbank.com"],
    "PNC": ["pnc.com"],
    "TFC": ["truist.com"],
    "BK": ["bnymellon.com"],
    "STT": ["statestreet.com"],
    "FIS": ["fisglobal.com"],
    "FISV": ["fiserv.com"],
    "AIG": ["aig.com"],
    "MET": ["metlife.com"],
    "PRU": ["prudential.com"],
    "ALL": ["allstate.com"],
    "TRV": ["travelers.com"],
    "CB": ["chubb.com"],
    "MMC": ["marshmclennan.com", "marsh.com", "mercer.com"],
    "AON": ["aon.com"],
    "ICE": ["ice.com", "nyse.com"],
    "CME": ["cmegroup.com"],
    "SPGI": ["spglobal.com"],
    "MCO": ["moodys.com"],
    "MSCI": ["msci.com"],

    # Healthcare
    "UNH": ["unitedhealthgroup.com", "uhc.com", "optum.com"],
    "JNJ": ["jnj.com", "janssen.com"],
    "LLY": ["lilly.com"],
    "PFE": ["pfizer.com"],
    "ABBV": ["abbvie.com"],
    "MRK": ["merck.com"],
    "TMO": ["thermofisher.com"],
    "ABT": ["abbott.com"],
    "DHR": ["danaher.com"],
    "BMY": ["bms.com"],
    "AMGN": ["amgen.com"],
    "GILD": ["gilead.com"],
    "VRTX": ["vrtx.com"],
    "REGN": ["regeneron.com"],
    "ISRG": ["intuitive.com"],
    "EW": ["edwards.com"],
    "DXCM": ["dexcom.com"],
    "IDXX": ["idexx.com"],
    "ZTS": ["zoetis.com"],
    "SYK": ["stryker.com"],
    "BDX": ["bd.com"],
    "BSX": ["bostonscientific.com"],
    "MDT": ["medtronic.com"],
    "HCA": ["hcahealthcare.com"],
    "CVS": ["cvs.com", "cvshealth.com", "aetna.com"],
    "CI": ["cigna.com", "evernorth.com"],
    "ELV": ["elevancehealth.com", "anthem.com"],
    "HUM": ["humana.com"],
    "CNC": ["centene.com"],
    "MCK": ["mckesson.com"],
    "CAH": ["cardinalhealth.com"],

    # Consumer Discretionary
    "TSLA": ["tesla.com"],
    "HD": ["homedepot.com"],
    "LOW": ["lowes.com"],
    "MCD": ["mcdonalds.com"],
    "SBUX": ["starbucks.com"],
    "NKE": ["nike.com", "converse.com", "jordan.com"],
    "TJX": ["tjx.com", "tjmaxx.com", "marshalls.com", "homegoods.com"],
    "ROST": ["rossstores.com"],
    "BKNG": ["booking.com", "priceline.com", "kayak.com", "agoda.com"],
    "MAR": ["marriott.com"],
    "HLT": ["hilton.com"],
    "CMG": ["chipotle.com"],
    "YUM": ["yum.com", "kfc.com", "pizzahut.com", "tacobell.com"],
    "DRI": ["darden.com", "olivegarden.com", "longhorn.com"],
    "DPZ": ["dominos.com"],
    "ORLY": ["oreillyauto.com"],
    "AZO": ["autozone.com"],
    "BBY": ["bestbuy.com"],
    "ETSY": ["etsy.com"],
    "EBAY": ["ebay.com"],
    "W": ["wayfair.com"],
    "GM": ["gm.com", "chevrolet.com", "buick.com", "cadillac.com", "gmc.com"],
    "F": ["ford.com", "lincoln.com"],
    "APTV": ["aptiv.com"],
    "LEN": ["lennar.com"],
    "DHI": ["drhorton.com"],
    "PHM": ["pulte.com"],
    "GPC": ["genpt.com", "napaonline.com"],
    "POOL": ["poolcorp.com"],
    "RCL": ["royalcaribbean.com"],
    "CCL": ["carnival.com", "princess.com", "hollandamerica.com"],
    "NCLH": ["ncl.com"],
    "DIS": ["disney.com", "disneyplus.com", "hulu.com", "espn.com", "abc.com", "marvel.com", "starwars.com"],
    "CMCSA": ["comcast.com", "xfinity.com", "nbcuniversal.com", "peacocktv.com"],
    "CHTR": ["spectrum.com", "charter.com"],
    "PARA": ["paramount.com", "paramountplus.com", "cbs.com", "mtv.com"],
    "WBD": ["wbd.com", "max.com", "hbo.com", "cnn.com", "discoveryplus.com"],
    "LVS": ["venetianlasvegas.com", "marinabaysands.com"],
    "MGM": ["mgmresorts.com"],
    "WYNN": ["wynnresorts.com"],

    # Consumer Staples
    "PG": ["pg.com", "tide.com", "gillette.com", "pampers.com", "olay.com"],
    "KO": ["coca-cola.com", "coca-colacompany.com"],
    "PEP": ["pepsico.com", "pepsi.com", "fritolay.com", "quakeroats.com", "gatorade.com"],
    "COST": ["costco.com"],
    "WMT": ["walmart.com", "samsclub.com"],
    "TGT": ["target.com"],
    "CL": ["colgatepalmolive.com", "colgate.com"],
    "KMB": ["kimberly-clark.com", "huggies.com", "kleenex.com"],
    "MDLZ": ["mondelezinternational.com", "oreo.com", "cadbury.com"],
    "GIS": ["generalmills.com", "cheerios.com"],
    "K": ["kellanova.com"],
    "HSY": ["thehersheycompany.com", "hersheys.com"],
    "SJM": ["jmsmucker.com"],
    "CPB": ["campbellsoupcompany.com", "campbells.com"],
    "HRL": ["hormelfoods.com"],
    "MKC": ["mccormick.com"],
    "STZ": ["cbrands.com"],
    "TAP": ["molsoncoors.com"],
    "MNST": ["monsterenergy.com"],
    "KR": ["kroger.com"],
    "SYY": ["sysco.com"],
    "ADM": ["adm.com"],
    "TSN": ["tysonfoods.com"],
    "KHC": ["kraftheinzcompany.com"],
    "CAG": ["conagrabrands.com"],
    "PM": ["pmi.com"],
    "MO": ["altria.com"],
    "CLX": ["thecloroxcompany.com", "clorox.com"],
    "EL": ["esteelauder.com", "mac.com", "clinique.com"],
    "CHD": ["churchdwight.com", "armandhammer.com", "oxiclean.com"],

    # Energy
    "XOM": ["exxonmobil.com"],
    "CVX": ["chevron.com"],
    "COP": ["conocophillips.com"],
    "EOG": ["eogresources.com"],
    "SLB": ["slb.com"],
    "MPC": ["marathonpetroleum.com"],
    "VLO": ["valero.com"],
    "PSX": ["phillips66.com"],
    "OXY": ["oxy.com"],
    "DVN": ["devonenergy.com"],
    "FANG": ["diamondbackenergy.com"],
    "HAL": ["halliburton.com"],
    "BKR": ["bakerhughes.com"],
    "CTRA": ["coterra.com"],
    "WMB": ["williams.com"],
    "KMI": ["kindermorgan.com"],
    "OKE": ["oneok.com"],
    "TRGP": ["targaresources.com"],

    # Industrials
    "BA": ["boeing.com"],
    "LMT": ["lockheedmartin.com"],
    "RTX": ["rtx.com", "raytheon.com", "prattwhitney.com", "collins.com"],
    "NOC": ["northropgrumman.com"],
    "GD": ["gd.com"],
    "HII": ["huntingtoningalls.com"],
    "CAT": ["caterpillar.com", "cat.com"],
    "DE": ["deere.com", "johndeere.com"],
    "HON": ["honeywell.com"],
    "GE": ["geaerospace.com", "ge.com"],
    "MMM": ["3m.com"],
    "EMR": ["emerson.com"],
    "ITW": ["itw.com"],
    "ROK": ["rockwellautomation.com"],
    "ETN": ["eaton.com"],
    "PH": ["parker.com"],
    "CMI": ["cummins.com"],
    "PCAR": ["paccar.com", "kenworth.com", "peterbilt.com"],
    "FDX": ["fedex.com"],
    "UPS": ["ups.com"],
    "UNP": ["up.com"],
    "CSX": ["csx.com"],
    "NSC": ["norfolksouthern.com"],
    "DAL": ["delta.com"],
    "UAL": ["united.com"],
    "LUV": ["southwest.com"],
    "AAL": ["aa.com"],
    "WM": ["wm.com"],
    "RSG": ["republicservices.com"],
    "JCI": ["johnsoncontrols.com"],
    "TT": ["tranetechnologies.com"],
    "CARR": ["carrier.com"],
    "VRSK": ["verisk.com"],
    "IR": ["irco.com"],
    "DOV": ["dovercorporation.com"],
    "SWK": ["stanleyblackanddecker.com"],
    "GWW": ["grainger.com"],
    "FAST": ["fastenal.com"],
    "CPRT": ["copart.com"],
    "ODFL": ["odfl.com"],
    "CTAS": ["cintas.com"],
    "PAYX": ["paychex.com"],
    "ADP": ["adp.com"],

    # Utilities
    "NEE": ["nexteraenergy.com", "fpl.com"],
    "DUK": ["duke-energy.com"],
    "SO": ["southerncompany.com"],
    "D": ["dominionenergy.com"],
    "AEP": ["aep.com"],
    "EXC": ["exeloncorp.com"],
    "XEL": ["xcelenergy.com"],
    "SRE": ["sempra.com"],
    "ED": ["coned.com"],
    "WEC": ["wecenergygroup.com"],
    "ES": ["eversource.com"],
    "DTE": ["dteenergy.com"],
    "FE": ["firstenergycorp.com"],
    "AEE": ["ameren.com"],
    "CMS": ["cmsenergy.com"],
    "PEG": ["pseg.com"],
    "AWK": ["amwater.com"],
    "ATO": ["atmosenergy.com"],

    # Real Estate
    "PLD": ["prologis.com"],
    "AMT": ["americantower.com"],
    "CCI": ["crowncastle.com"],
    "EQIX": ["equinix.com"],
    "PSA": ["publicstorage.com"],
    "O": ["realtyincome.com"],
    "SPG": ["simon.com"],
    "WELL": ["welltower.com"],
    "DLR": ["digitalrealty.com"],
    "AVB": ["avalonbay.com"],
    "EQR": ["equityresidential.com"],
    "VICI": ["vfreit.com"],
    "IRM": ["ironmountain.com"],
    "MAA": ["maac.com"],
    "ARE": ["are.com"],

    # Materials
    "LIN": ["linde.com"],
    "APD": ["airproducts.com"],
    "SHW": ["sherwin-williams.com"],
    "ECL": ["ecolab.com"],
    "FCX": ["fcx.com"],
    "NEM": ["newmont.com"],
    "NUE": ["nucor.com"],
    "STLD": ["steeldynamics.com"],
    "VMC": ["vulcanmaterials.com"],
    "MLM": ["martinmarietta.com"],
    "DOW": ["dow.com"],
    "DD": ["dupont.com"],
    "PPG": ["ppg.com"],
    "CE": ["celanese.com"],
    "CF": ["cfindustries.com"],
    "MOS": ["mosaicco.com"],
    "ALB": ["albemarle.com"],
    "IFF": ["iff.com"],
    "PKG": ["packagingcorp.com"],
    "IP": ["internationalpaper.com"],
    "BLL": ["ball.com"],

    # Communication Services
    "T": ["att.com"],
    "VZ": ["verizon.com"],
    "TMUS": ["t-mobile.com"],
    "EA": ["ea.com"],
    "TTWO": ["take2games.com", "rockstargames.com"],
    "MTCH": ["match.com", "tinder.com", "hinge.co"],
    "ZG": ["zillow.com"],
    "PINS": ["pinterest.com"],
    "SNAP": ["snapchat.com", "snap.com"],
    "ROKU": ["roku.com"],
}

def get_domains_for_ticker(ticker):
    return DOMAIN_MAP.get(ticker.upper(), [])

def get_all_domain_to_ticker():
    """Build reverse mapping: domain -> ticker."""
    result = {}
    for ticker, domains in DOMAIN_MAP.items():
        for d in domains:
            result[d.lower()] = ticker
    return result


if __name__ == "__main__":
    import json, sys

    total_domains = sum(len(d) for d in DOMAIN_MAP.values())
    total_companies = len(DOMAIN_MAP)

    if "--inject" in sys.argv:
        # Inject domains into scored data
        from pathlib import Path
        scores_file = Path("data/scores/all_scores.json")
        if not scores_file.exists():
            print("No scores file found. Run scoring engine first.")
            sys.exit(1)

        with open(scores_file) as f:
            scores = json.load(f)

        updated = 0
        for company in scores:
            ticker = company.get("ticker", "")
            if ticker and ticker in DOMAIN_MAP:
                company["domains"] = DOMAIN_MAP[ticker]
                updated += 1

        with open(scores_file, "w") as f:
            json.dump(scores, f, indent=2)

        print(f"Injected domains for {updated} companies into {scores_file}")
    else:
        print(f"S&P 500 Domain Map: {total_companies} companies, {total_domains} domains")
        for ticker, domains in sorted(DOMAIN_MAP.items()):
            print(f"  {ticker:6s}  {', '.join(domains)}")
