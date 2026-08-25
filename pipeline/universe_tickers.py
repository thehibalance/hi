"""
Universe Tickers — S&P 500 + Russell 1000 additions
Fed into the pipeline to force-pull data for all major US public companies.
Updated: March 2026
"""

# S&P 500 (503 tickers, current as of March 2026)
SP500 = [
    "NVDA","AAPL","MSFT","AMZN","GOOGL","GOOG","META","AVGO","TSLA","BRK.B",
    "WMT","LLY","JPM","XOM","V","JNJ","MU","ORCL","MA","COST",
    "NFLX","CVX","ABBV","PLTR","PG","BAC","HD","KO","AMD","CAT",
    "GE","CSCO","MRK","LRCX","AMAT","RTX","PM","UNH","MS","GS",
    "IBM","WFC","GEV","TMUS","LIN","INTC","MCD","PEP","VZ","AXP",
    "KLAC","T","C","NEE","AMGN","ABT","CRM","DIS","GILD","TXN",
    "TMO","ANET","TJX","ISRG","SCHW","BA","UBER","APH","PFE","DE",
    "COP","ADI","BLK","APP","LMT","HON","WELL","UNP","ETN","QCOM",
    "BKNG","PANW","DHR","SYK","LOW","CB","SPGI","INTU","PLD","BMY",
    "ACN","NOW","PGR","NEM","PH","CEG","VRTX","MCK","HCA","COF",
    "MDT","GLW","SNDK","CME","CRWD","MO","SO","BSX","SBUX","WDC",
    "NOC","CMCSA","DUK","ADBE","DELL","HWM","EQIX","GD","TT","WM",
    "CVS","STX","ICE","WMB","BX","PWR","MAR","AMT","ADP","MRSH",
    "FDX","UPS","SNPS","JCI","PNC","KKR","CDNS","FCX","USB","NKE",
    "BK","REGN","ABNB","MCO","MSI","SHW","MMM","ITW","CMI","CTAS",
    "ECL","EOG","CSX","ORLY","EMR","RCL","KMI","MNST","MDLZ","DASH",
    "VLO","AEP","CL","CI","MPC","PSX","LHX","RSG","CRH","AON",
    "SLB","WBD","TDG","HLT","HOOD","ROST","GM","ELV","TRV","APO",
    "NSC","COR","APD","SRE","SPG","CARR","AIG","FITB","FAST","ROP",
    "GEHC","CMG","AMP","PAYX","AFL","TFC","DLR","FIS","HES","PSA",
    "MSCI","SQ","FICO","O","OKE","AZO","ODFL","BKR","CTVA","GWW",
    "VRSK","CPRT","NDAQ","D","AJG","MCHP","PCG","ALL","DHI","EW",
    "A","URI","DAL","OTIS","TEL","CTSH","DD","PPG","F","HAL",
    "KDP","AXON","YUM","MTD","IDXX","FANG","ON","ROK","CHTR","BDX",
    "AME","TTWO","EA","RMD","HSY","KEYS","IQV","XEL","ZTS","EXC",
    "SYY","LYV","MRVL","KHC","DXCM","ED","WEC","WTW","GPN","ANSS",
    "IR","HUBB","DOW","TRGP","VST","WAB","CBRE","STZ","HPQ","HPE",
    "DOV","TSCO","MTB","MPWR","ZBRA","FTV","AWK","EFX","VICI","CHD",
    "BR","GLT","WY","TDY","ACGL","IT","PTC","CNC","HBAN","EBAY",
    "EQR","PPL","ETR","LUV","K","NTAP","NUE","BLDR","SMCI","RF",
    "AVB","RJF","IRM","MKC","GPC","WST","PKG","DTE","CAH","LVS",
    "J","WAT","ESS","VTR","SNA","UDR","MAA","KEY","CPT","ARE",
    "CFG","NTRS","TROW","AES","IP","LNT","NI","EVRG","CMA","BRO",
    "MGM","CE","TER","INCY","HRL","TAP","FOXA","FOX","NWSA","NWS",
    "MOS","APA","DVN","CZR","PNW","AIZ","RL","BWA","FRT","GNRC",
    "MTCH","WYNN","SEE","BIO","PAYC","POOL","JBHT","HII","MHK","FMC",
    "IVZ","ALK","BEN","CRL","GL","SOLV","DVA","BBWI","NCLH","PARA",
    "TPR","HSIC","CHRW","CPB","SWK","RHI","FFIV","TXT","TECH","XRAY",
    "ALLE","AOS","AMCR","EMN","LKQ","WBA","DXC","MKTX","BF.B",
]

# Russell 1000 additions (companies NOT in S&P 500 but in Russell 1000)
# These are mid-cap and large-cap companies that add significant coverage
RUSSELL_1000_ADDITIONS = [
    # Tech
    "SNAP","PINS","ZM","DBX","PATH","DDOG","ZS","OKTA","MDB","TWLO",
    "ESTC","NET","BILL","HUBS","VEEV","TEAM","WDAY","COIN","U","RBLX",
    "DUOL","CHGG","ROKU","TTD","SHOP","SE","MELI","SPOT","SQ",
    "DOCU","FIVN","ASAN","ZI","GTLB","CFLT","MNDY","PCOR","S","IOT",
    "CWAN","AI","SOUN","ASTS","IONQ","RGTI","QUBT",
    
    # Fintech / Financial
    "SOFI","AFRM","UPST","LC","PYPL","TOST","MARQ","FI","GPN",
    
    # Healthcare / Biotech
    "MRNA","BIIB","EXAS","HALO","SGEN","IONS","SRPT","ALNY","BMRN",
    "RARE","PCVX","LEGN","CRSP","NTLA","BEAM","EDIT","VERV",
    "INSM","TGTX","RYTM","DAWN","AXSM","CRNX",
    
    # Consumer / Retail
    "LULU","DECK","BIRD","OATLY","BYND","WRBY","CHWY","W","ETSY",
    "COUR","BROS","DTC","YETI","FIGS","SFIX","RENT","POSH",
    "ANF","GPS","AEO","URBN","KSS","M","JWN","DKS","FIVE","DLTR",
    "DG","BBY","GME","BBBY","KR","SFM","CASY","WMK",
    
    # Auto / EV
    "RIVN","LCID","RIVN","FSR","NIO","XPEV","LI","PSNY",
    "QS","BLNK","CHPT","EVGO",
    
    # Energy / Clean
    "ENPH","SEDG","FSLR","RUN","NOVA","ARRY","MAXN",
    "PLUG","BE","BLDP","CLNE","STEM",
    
    # Real Estate / REITs
    "INVH","SUI","ELS","MPW","OHI","STAG","NNN","STOR",
    
    # Industrial
    "GNRC","TTC","SITE","AZEK","TREX","AAON",
    
    # Media / Entertainment
    "PARA","LGF.A","NFLX","ROKU","IMAX","CNK","AMC",
    "DKNG","PENN","RSI","CZR","MGM","WYNN",
    
    # Food / Beverage
    "CELH","MNST","SAM","SJM","GIS","CAG","LMNR","SMPL",
    "HAIN","POST","THS","BGS",
    
    # Crypto / Digital Assets
    "COIN","MSTR","MARA","RIOT","CLSK","HUT","BITF",
    
    # Cybersecurity
    "CRWD","PANW","ZS","FTNT","S","CYBR","QLYS","TENB","RPD",
    
    # Semiconductors  
    "MRVL","SWKS","QRVO","WOLF","SLAB","RMBS","CRUS","SITM",
    "ACLS","LSCC","AMBA","POWI","DIOD","MTSI","ALGM",
    
    # Space / Defense
    "RKLB","LUNR","ASTS","SPCE","RDW","BKSY","MNTS","SPCX",
    "HEI","KTOS","MRCY","AVAV",
    # July 2026 mid-cap expansion (batch 1)
    "SNOW", "PTON", "TDOC", "LMND", "HIMS", "DOCS",
    "BURL", "OATL", "SHAK", "DPZ",

    # August 2026 batch 2 expansion
    "PSTG", "APPN", "GLBE", "FLYW", "ULTA", "BJ",
    "PSMT", "OLLI", "WING", "TXRH", "CAVA", "MOH",
    "UHS", "THC", "PEN", "ILMN", "XYL", "BMBL",
    "IAC", "AEE", "ATO", "CMS", "JBLU", "SAVE",
    "SAIA", "LSTR", "AMH", "IFF", "ALB", "CF",
    "VMC", "WRB", "L", "MMC", "ENTG", "LDOS",
    "BWXT", "CW",

]

def get_all_tickers():
    """Return deduplicated list of all tickers (US + ADRs of international).
    
    v1.2.0: now uses get_us_listed_tickers() so foreign-exchange tickers
    (.L, .T, .DE, .HK etc.) are excluded. SEC EDGAR cannot fetch them, and
    they previously caused ghost records in the SEC aggregate."""
    all_tickers = set()
    for t in SP500 + RUSSELL_1000_ADDITIONS + SP400_MIDCAP:
        t = t.strip().upper()
        if t:
            all_tickers.add(t)
    
    # v1.2.0: US-listed ADRs only (SHEL, BP, HSBC, AZN, GSK, RIO, BHP, etc.)
    try:
        from international_tickers import get_us_listed_tickers
        intl = get_us_listed_tickers()
        for t in intl:
            all_tickers.add(t)
    except ImportError:
        # Fallback to old behavior if get_us_listed_tickers not yet deployed
        try:
            from international_tickers import get_international_tickers
            intl = get_international_tickers()
            for t in intl:
                if "." not in t or t.endswith(".B") or t.endswith(".A"):
                    all_tickers.add(t)
        except ImportError:
            pass
    
    return sorted(all_tickers)

if __name__ == "__main__":
    tickers = get_all_tickers()
    print(f"Total unique tickers: {len(tickers)}")
    print(f"S&P 500: {len(SP500)} tickers")
    print(f"Russell additions: {len(RUSSELL_1000_ADDITIONS)} tickers")


# HI-PATCH:index-sp400:v1
# 335 constituents, each verified against SEC's ticker index at import
SP400_MIDCAP = [
    "AA","AAL","ACI","ACM","ADC","AEIS","AFG","AGCO","AHR","AIT","ALLY","ALSN","ALV","AM",
    "AMG","AMKR","AN","APG","APPF","AR","ARMK","ARW","ARWR","ASB","ASH","ATI","ATR","AVNT",
    "AVT","AVTR","AXTA","AYI","BAH","BC","BCO","BDC","BHF","BKH","BRKR","BRX","BSY","BTSG",
    "BYD","CACI","CAR","CART","CBSH","CBT","CCK","CDE","CDP","CFR","CG","CGNX","CHDN","CHE",
    "CHH","CHRD","CLF","CLH","CMC","CNH","CNM","CNO","CNX","COKE","COLB","COLM","CPRI","CR",
    "CRBG","CROX","CRS","CSL","CTRE","CUBE","CUZ","CVLT","CXT","CYTK","DAR","DCI","DINO",
    "DLB","DOCN","DT","DTM","DY","EEFT","EGP","EHC","ELAN","ELF","ENS","ENSG","EPR","EQH",
    "ESAB","ESNT","EVR","EWBC","EXEL","EXLS","EXP","EXPO","FAF","FBIN","FCFS","FCN","FFIN",
    "FHI","FHN","FLG","FLR","FLS","FN","FNB","FND","FNF","FOUR","FR","FTI","G","GAP","GATX",
    "GBCI","GEF","GGG","GHC","GLPI","GMED","GNTX","GPK","GWRE","GXO","H","HAE","HGV","HL",
    "HLI","HLNE","HOG","HOMB","HQY","HR","HRB","HWC","HXL","IBOC","IDA","IDCC","IESC",
    "INGR","IPGP","IRT","ITT","JAZZ","JEF","JLL","KBH","KBR","KD","KEX","KNF","KNSL","KNX",
    "KRC","KRG","KRYS","LAD","LAMR","LEA","LECO","LFUS","LIVN","LNTH","LOPE","LPX","MANH",
    "MAT","MEDP","MIDD","MKSI","MLI","MMS","MOG.A","MORN","MP","MSA","MSM","MTDR","MTG",
    "MTN","MTZ","MUR","MUSA","MZTI","NBIX","NEU","NFG","NJR","NLY","NOV","NOVT","NTNX",
    "NVST","NVT","NWE","NXST","NXT","NYT","OC","OGE","OGS","OLED","OLN","ONB","ONTO","OPCH",
    "ORA","ORI","OSK","OVV","OZK","P","PAG","PB","PBF","PCTY","PEGA","PFGC","PII","PK",
    "PLNT","PNFP","POR","PPC","PR","PRI","PSN","PVH","R","RBA","RBC","REXR","RGA","RGEN",
    "RGLD","RH","RLI","RNR","ROIV","RPM","RRC","RRX","RS","RYAN","RYN","SAIC","SANM","SARO",
    "SBRA","SCI","SEIC","SF","SGI","SHC","SIGI","SIRI","SLGN","SLM","SMG","SMTC","SN","SNX",
    "SOLS","SON","SPXC","SR","SSB","SSD","ST","STRL","STWD","SWX","SYNA","TCBI","TEX","THG",
    "THO","TKR","TLN","TNL","TOL","TRU","TTEK","TTMI","TXNM","UBSI","UFPI","UGI","ULS",
    "UMBF","UNM","USFD","UTHR","VAL","VC","VFC","VIAV","VICR","VLY","VMI","VNO","VNOM",
    "VNT","VOYA","VVV","WAL","WCC","WEX","WFRD","WH","WHR","WLK","WMG","WMS","WPC","WSO",
    "WTFC","WTRG","WTS","WWD","XPO","ZION",
]
