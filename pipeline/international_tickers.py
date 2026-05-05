"""
International Universe Tickers
FTSE 100, DAX 40, CAC 40, Nikkei 225, and major global companies.
Fed into the pipeline alongside US tickers.
Updated: March 2026

Note: Many international companies trade on US exchanges as ADRs.
Tickers ending in .L (London), .DE (Germany), .PA (Paris), .T (Tokyo)
are for Yahoo Finance / Finnhub. ADR tickers work with all US data sources.
"""

# ═══════════════════════════════════════════════════════════════
# FTSE 100 (London Stock Exchange) — ADR tickers where available
# ═══════════════════════════════════════════════════════════════
FTSE_100 = [
    # ADR tickers (trade on NYSE/NASDAQ — full US data source coverage)
    "SHEL",   # Shell
    "BP",     # BP
    "HSBC",   # HSBC
    "UL",     # Unilever
    "AZN",    # AstraZeneca
    "GSK",    # GSK
    "RIO",    # Rio Tinto
    "BHP",    # BHP Group
    "BTI",    # British American Tobacco
    "DEO",    # Diageo
    "LYG",    # Lloyds Banking
    "BCS",    # Barclays
    "NWG",    # NatWest Group
    "VOD",    # Vodafone
    "WPP",    # WPP
    "LSEG",   # London Stock Exchange Group (OTC)
    "RELX",   # RELX
    "RYCEY",  # Rolls-Royce
    "PUKKY",  # Prudential
    "CMWAY",  # Compass Group
    # London-only (Yahoo Finance handles .L suffix)
    "AAL.L",  # Anglo American
    "ABDN.L", # Abrdn
    "ABF.L",  # Associated British Foods
    "AHT.L",  # Ashtead Group
    "ANTO.L", # Antofagasta
    "AUTO.L", # Auto Trader
    "AV.L",   # Aviva
    "BAE.L",  # BAE Systems
    "BARC.L", # Barclays
    "BDEV.L", # Barratt Developments
    "BKG.L",  # Berkeley Group
    "BNZL.L", # Bunzl
    "CPG.L",  # Compass Group
    "CRDA.L", # Croda International
    "CRH.L",  # CRH
    "DGE.L",  # Diageo
    "ENT.L",  # Entain
    "EXPN.L", # Experian
    "FLTR.L", # Flutter Entertainment
    "GLEN.L", # Glencore
    "GSK.L",  # GSK
    "HIK.L",  # Hikma Pharmaceuticals
    "HLMA.L", # Halma
    "HL.L",   # Hargreaves Lansdown
    "HSBA.L", # HSBC
    "III.L",  # 3i Group
    "IMB.L",  # Imperial Brands
    "INF.L",  # Informa
    "IHG.L",  # InterContinental Hotels
    "ITRK.L", # Intertek
    "JD.L",   # JD Sports
    "KGF.L",  # Kingfisher
    "LAND.L", # Land Securities
    "LGEN.L", # Legal & General
    "LLOY.L", # Lloyds Banking Group
    "LSEG.L", # London Stock Exchange
    "MNG.L",  # M&G
    "MKS.L",  # Marks & Spencer
    "MNDI.L", # Mondi
    "NG.L",   # National Grid
    "NXT.L",  # Next
    "OCDO.L", # Ocado
    "PSON.L", # Pearson
    "PSN.L",  # Persimmon
    "REL.L",  # RELX
    "RKT.L",  # Reckitt Benckiser
    "RMV.L",  # Rightmove
    "RR.L",   # Rolls-Royce
    "RTO.L",  # Rentokil Initial
    "SBRY.L", # Sainsbury's
    "SDR.L",  # Schroders
    "SGE.L",  # Sage Group
    "SGRO.L", # Segro
    "SN.L",   # Smith & Nephew
    "SPX.L",  # Spirax-Sarco
    "SSE.L",  # SSE
    "STAN.L", # Standard Chartered
    "SVT.L",  # Severn Trent
    "TSCO.L", # Tesco
    "TW.L",   # Taylor Wimpey
    "ULVR.L", # Unilever
    "UTG.L",  # Unite Group
    "VOD.L",  # Vodafone
    "WEIR.L", # Weir Group
    "WTB.L",  # Whitbread
    "WPP.L",  # WPP
]

# ═══════════════════════════════════════════════════════════════
# DAX 40 (Frankfurt) — ADR tickers where available
# ═══════════════════════════════════════════════════════════════
DAX_40 = [
    # ADR tickers
    "SAP",    # SAP
    "SSNLF",  # Siemens (OTC)
    "DTEGY",  # Deutsche Telekom
    "DB",     # Deutsche Bank
    "BAYRY",  # Bayer
    "BASFY",  # BASF
    "VWAGY",  # Volkswagen
    "BMWYY",  # BMW
    "DDAIF",  # Mercedes-Benz (OTC)
    "ADDYY",  # Adidas
    "ALIZF",  # Allianz
    "MURGY",  # Munich Re
    "HENKY",  # Henkel
    "IFNNY",  # Infineon
    # Frankfurt-only
    "ADS.DE",  # Adidas
    "ALV.DE",  # Allianz
    "BAS.DE",  # BASF
    "BAYN.DE", # Bayer
    "BEI.DE",  # Beiersdorf
    "BMW.DE",  # BMW
    "BNR.DE",  # Brenntag
    "CON.DE",  # Continental
    "1COV.DE", # Covestro
    "DTG.DE",  # Daimler Truck
    "DBK.DE",  # Deutsche Bank
    "DB1.DE",  # Deutsche Boerse
    "DTE.DE",  # Deutsche Telekom
    "DHL.DE",  # DHL Group
    "ENR.DE",  # Siemens Energy
    "FRE.DE",  # Fresenius
    "HEI.DE",  # Heidelberg Materials
    "HNR1.DE", # Hannover Re
    "IFX.DE",  # Infineon
    "MBG.DE",  # Mercedes-Benz
    "MRK.DE",  # Merck KGaA
    "MTX.DE",  # MTU Aero Engines
    "MUV2.DE", # Munich Re
    "PAH3.DE", # Porsche Auto Holding
    "P911.DE", # Porsche AG
    "QIA.DE",  # Qiagen
    "RHM.DE",  # Rheinmetall
    "RWE.DE",  # RWE
    "SAP.DE",  # SAP
    "SHL.DE",  # Siemens Healthineers
    "SIE.DE",  # Siemens
    "SRT3.DE", # Sartorius
    "SY1.DE",  # Symrise
    "VNA.DE",  # Vonovia
    "VOW3.DE", # Volkswagen
    "ZAL.DE",  # Zalando
]

# ═══════════════════════════════════════════════════════════════
# CAC 40 (Paris)
# ═══════════════════════════════════════════════════════════════
CAC_40 = [
    # ADR tickers
    "TTE",    # TotalEnergies
    "SNY",    # Sanofi
    "LVMUY",  # LVMH
    "OR",     # L'Oreal (OTC)
    "HESAY",  # Hermes
    "BNPQY",  # BNP Paribas
    "DANOY",  # Danone
    "SBGSY",  # Schneider Electric
    "STLA",   # Stellantis
    "PPRUY",  # Kering
    "AXAHY",  # AXA
    "VIVEF",  # Vivendi
    # Paris-only
    "AI.PA",   # Air Liquide
    "AIR.PA",  # Airbus
    "ACA.PA",  # Credit Agricole
    "BN.PA",   # Danone
    "BNP.PA",  # BNP Paribas
    "CAP.PA",  # Capgemini
    "CS.PA",   # AXA
    "DG.PA",   # Vinci
    "DSY.PA",  # Dassault Systemes
    "EL.PA",   # EssilorLuxottica
    "ENGI.PA", # Engie
    "ERF.PA",  # Eurofins Scientific
    "GLE.PA",  # Societe Generale
    "HO.PA",   # Thales
    "KER.PA",  # Kering
    "LR.PA",   # Legrand
    "MC.PA",   # LVMH
    "ML.PA",   # Michelin
    "MT.PA",   # ArcelorMittal
    "OR.PA",   # L'Oreal
    "ORA.PA",  # Orange
    "PUB.PA",  # Publicis
    "RI.PA",   # Pernod Ricard
    "RMS.PA",  # Hermes
    "SAF.PA",  # Safran
    "SAN.PA",  # Sanofi
    "SGO.PA",  # Saint-Gobain
    "SU.PA",   # Schneider Electric
    "STM.PA",  # STMicroelectronics
    "TEP.PA",  # Teleperformance
    "TTE.PA",  # TotalEnergies
    "URW.PA",  # Unibail-Rodamco
    "VIE.PA",  # Veolia
    "VIV.PA",  # Vivendi
]

# ═══════════════════════════════════════════════════════════════
# Nikkei 225 (Tokyo) — Major companies with ADRs or OTC tickers
# ═══════════════════════════════════════════════════════════════
NIKKEI_225 = [
    # ADR tickers (US-listed)
    "TM",     # Toyota
    "SONY",   # Sony
    "HMC",    # Honda
    "MUFG",   # Mitsubishi UFJ Financial
    "SMFG",   # Sumitomo Mitsui Financial
    "NMR",    # Nomura
    "MFG",    # Mizuho Financial
    "IX",     # Orix
    "CAJ",    # Canon
    "SNE",    # Sony (alternate)
    "NTDOY",  # Nintendo
    "NSANY",  # Nissan
    "FUJHY",  # Fujifilm
    "HNDAF",  # Honda (OTC)
    "TOELY",  # Tokyo Electron
    "KYOCY",  # Kyocera
    "PCRFY",  # Panasonic
    "NTDOF",  # Nintendo (OTC)
    "SFTBY",  # SoftBank Group
    "SNEJF",  # Sony (OTC)
    # Tokyo-only (Yahoo Finance .T suffix)
    "7203.T",  # Toyota
    "6758.T",  # Sony
    "6861.T",  # Keyence
    "8306.T",  # Mitsubishi UFJ
    "6501.T",  # Hitachi
    "8035.T",  # Tokyo Electron
    "6902.T",  # Denso
    "7741.T",  # HOYA
    "6098.T",  # Recruit Holdings
    "4063.T",  # Shin-Etsu Chemical
    "9984.T",  # SoftBank Group
    "6367.T",  # Daikin Industries
    "6594.T",  # Nidec
    "7267.T",  # Honda
    "7974.T",  # Nintendo
    "9433.T",  # KDDI
    "9432.T",  # NTT
    "4519.T",  # Chugai Pharmaceutical
    "4568.T",  # Daiichi Sankyo
    "6857.T",  # Advantest
    "8001.T",  # Itochu
    "8058.T",  # Mitsubishi Corp
    "8031.T",  # Mitsui & Co
    "2914.T",  # Japan Tobacco
    "4502.T",  # Takeda
    "4503.T",  # Astellas Pharma
    "6762.T",  # TDK
    "6723.T",  # Renesas Electronics
    "7751.T",  # Canon
    "6981.T",  # Murata Manufacturing
    "9983.T",  # Fast Retailing (Uniqlo)
    "8766.T",  # Tokio Marine
    "8802.T",  # Mitsubishi Estate
    "3382.T",  # Seven & i Holdings
    "4901.T",  # Fujifilm
    "6971.T",  # Kyocera
    "6752.T",  # Panasonic
    "7011.T",  # Mitsubishi Heavy Industries
    "7012.T",  # Kawasaki Heavy Industries
    "7201.T",  # Nissan
    "7269.T",  # Suzuki
    "7270.T",  # Subaru
]

# ═══════════════════════════════════════════════════════════════
# Other Major Global Companies (ADRs and OTC)
# ═══════════════════════════════════════════════════════════════
GLOBAL_MAJORS = [
    # South Korea
    "005930.KS",  # Samsung Electronics
    "000660.KS",  # SK Hynix
    "035420.KS",  # Naver
    "035720.KS",  # Kakao
    "LPL",        # LG Display (ADR)
    
    # Taiwan
    "TSM",    # TSMC (ADR)
    "UMC",    # United Microelectronics (ADR)
    "ASX",    # ASE Technology (ADR)
    
    # China / Hong Kong
    "BABA",   # Alibaba
    "JD",     # JD.com
    "PDD",    # PDD Holdings (Temu)
    "BIDU",   # Baidu
    "NIO",    # NIO
    "XPEV",   # XPeng
    "LI",     # Li Auto
    "BILI",   # Bilibili
    "TME",    # Tencent Music
    "TCEHY",  # Tencent (OTC)
    "BYDDF",  # BYD (OTC)
    "MPNGY",  # Meituan (OTC)
    
    # India
    "INFY",   # Infosys (ADR)
    "WIT",    # Wipro (ADR)
    "HDB",    # HDFC Bank (ADR)
    "IBN",    # ICICI Bank (ADR)
    "TTM",    # Tata Motors (ADR)
    "RDY",    # Dr. Reddy's (ADR)
    "SIFY",   # Sify Technologies
    
    # Australia
    "BHP",    # BHP (dual listed)
    "RIO",    # Rio Tinto (dual listed)
    "WBD",    # Westpac (OTC)
    "CMWAY",  # Commonwealth Bank (OTC)
    "ANZBY",  # ANZ Bank (OTC)
    "ATLKY",  # Atlassian (AU origin, US listed)
    
    # Canada
    "TD",     # Toronto-Dominion Bank
    "RY",     # Royal Bank of Canada
    "BNS",    # Bank of Nova Scotia
    "BMO",    # Bank of Montreal
    "CM",     # CIBC
    "CNQ",    # Canadian Natural Resources
    "SU",     # Suncor Energy
    "ENB",    # Enbridge
    "TRP",    # TC Energy
    "CP",     # Canadian Pacific
    "CNI",    # Canadian National Railway
    "MFC",    # Manulife Financial
    "SLF",    # Sun Life Financial
    "SHOP",   # Shopify (dual listed)
    "LSPD",   # Lightspeed Commerce
    
    # Switzerland
    "NSRGY",  # Nestle (OTC)
    "RHHBY",  # Roche (OTC)
    "NVS",    # Novartis (ADR)
    "ZURVY",  # Zurich Insurance (OTC)
    "UBSG",   # UBS Group
    "CSGN",   # Credit Suisse → now UBS
    "ABBN",   # ABB
    
    # Netherlands
    "ASML",   # ASML (dual listed)
    "ING",    # ING Group (ADR)
    "PHG",    # Philips (ADR)
    "STMHY",  # STMicro (OTC)
    
    # Scandinavia
    "NHYDY",  # Norsk Hydro
    "EQNR",   # Equinor (Norway)
    "VOLVY",  # Volvo (OTC)
    "SPOT",   # Spotify (Sweden, US listed)
    "NOK",    # Nokia (Finland, ADR)
    "NXPI",   # NXP Semiconductors (Netherlands)
    
    # Latin America
    "MELI",   # MercadoLibre (Argentina, US listed)
    "NU",     # Nu Holdings (Brazil, US listed)
    "VALE",   # Vale (Brazil, ADR)
    "PBR",    # Petrobras (Brazil, ADR)
    "ITUB",   # Itau Unibanco (Brazil, ADR)
    "ABEV",   # Ambev (Brazil, ADR)
    "AMX",    # America Movil (Mexico, ADR)
    "FMX",    # FEMSA (Mexico, ADR)
    
    # Middle East / Africa
    "GOLD",   # Gold Fields (South Africa, ADR)
    "SSL",    # Sasol (South Africa, ADR)
    "SCCO",   # Southern Copper (Mexico)
]

# ═══════════════════════════════════════════════════════════════
# Domain mappings for international companies (extension lookups)
# ═══════════════════════════════════════════════════════════════
INTL_DOMAINS = {
    # UK
    "SHEL": ["shell.com"],
    "BP": ["bp.com"],
    "HSBC": ["hsbc.com"],
    "UL": ["unilever.com"],
    "AZN": ["astrazeneca.com"],
    "GSK": ["gsk.com"],
    "VOD": ["vodafone.com"],
    "WPP": ["wpp.com"],
    "RELX": ["relx.com"],
    "DEO": ["diageo.com"],
    "BTI": ["bat.com"],
    "RIO": ["riotinto.com"],
    "BCS": ["barclays.com"],
    
    # Germany
    "SAP": ["sap.com"],
    "ADDYY": ["adidas.com"],
    "VWAGY": ["volkswagen.com", "vw.com"],
    "BMWYY": ["bmw.com"],
    "BAYRY": ["bayer.com"],
    "BASFY": ["basf.com"],
    "DB": ["db.com", "deutschebank.com"],
    "DTEGY": ["telekom.com", "t-mobile.de"],
    
    # France
    "TTE": ["totalenergies.com"],
    "SNY": ["sanofi.com"],
    "LVMUY": ["lvmh.com"],
    "STLA": ["stellantis.com"],
    "BNPQY": ["bnpparibas.com"],
    "DANOY": ["danone.com"],
    "PPRUY": ["kering.com"],
    
    # Japan
    "TM": ["toyota.com", "toyota.co.jp"],
    "SONY": ["sony.com"],
    "HMC": ["honda.com"],
    "NTDOY": ["nintendo.com"],
    "SFTBY": ["softbank.jp"],
    "PCRFY": ["panasonic.com"],
    "FUJHY": ["fujifilm.com"],
    "KYOCY": ["kyocera.com"],
    
    # China
    "BABA": ["alibaba.com", "aliexpress.com"],
    "JD": ["jd.com"],
    "PDD": ["pinduoduo.com", "temu.com"],
    "BIDU": ["baidu.com"],
    "NIO": ["nio.com"],
    "TCEHY": ["tencent.com", "wechat.com"],
    "BYDDF": ["byd.com"],
    
    # India
    "INFY": ["infosys.com"],
    "WIT": ["wipro.com"],
    "TTM": ["tatamotors.com", "tata.com"],
    
    # Other
    "TSM": ["tsmc.com"],
    "ASML": ["asml.com"],
    "NSRGY": ["nestle.com"],
    "NVS": ["novartis.com"],
    "RHHBY": ["roche.com"],
    "NOK": ["nokia.com"],
    "VALE": ["vale.com"],
    "TD": ["td.com"],
    "RY": ["rbcroyalbank.com", "rbc.com"],
    "ENB": ["enbridge.com"],
    "ING": ["ing.com"],
    "MELI": ["mercadolibre.com"],
    "NU": ["nubank.com.br"],
    "EQNR": ["equinor.com"],
    "SPOT": ["spotify.com"],
    "SHOP": ["shopify.com"],
}


def get_international_tickers():
    """Return deduplicated list of ALL international tickers, including foreign-listed.
    Use this for Yahoo Finance / Finnhub which support foreign exchanges (.L, .T, .DE)."""
    all_tickers = set()
    for t in FTSE_100 + DAX_40 + CAC_40 + NIKKEI_225 + GLOBAL_MAJORS:
        t = t.strip()
        if t:
            all_tickers.add(t)
    return sorted(all_tickers)


def get_us_listed_tickers():
    """v1.2.0: Return only US-listed ADRs (no country suffix).
    
    Use this for SEC EDGAR collection — SEC cannot fetch foreign filers, so
    sending it tickers like '7203.T' or 'AAL.L' creates ghost records and
    wastes API calls. ADR tickers (SHEL, BP, HSBC, AZN, etc.) trade on
    NYSE/NASDAQ and have full SEC filings via 20-F (or 10-K for some)."""
    all_tickers = set()
    for t in FTSE_100 + DAX_40 + CAC_40 + NIKKEI_225 + GLOBAL_MAJORS:
        t = t.strip()
        if not t:
            continue
        # Skip tickers with foreign-exchange suffixes
        # (.L London, .T Tokyo, .DE Germany, .PA Paris, .HK Hong Kong, .KS Korea,
        #  .SZ Shenzhen, .SS Shanghai, .AX Australia, .TO Toronto, .MI Milan, etc.)
        if "." in t and not t.endswith(".B") and not t.endswith(".A"):
            # Has a dot AND it's not a US class share (BRK.B, BF.B style)
            continue
        all_tickers.add(t.upper())
    return sorted(all_tickers)


if __name__ == "__main__":
    tickers = get_international_tickers()
    print(f"Total international tickers: {len(tickers)}")
    print(f"  FTSE 100: {len(FTSE_100)}")
    print(f"  DAX 40: {len(DAX_40)}")
    print(f"  CAC 40: {len(CAC_40)}")
    print(f"  Nikkei 225: {len(NIKKEI_225)}")
    print(f"  Global Majors: {len(GLOBAL_MAJORS)}")
    print(f"  Domain mappings: {len(INTL_DOMAINS)} companies")
