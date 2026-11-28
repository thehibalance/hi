#!/usr/bin/env python3
"""OSHA ITA -> U.2 (worker safety). Run once a year, commit the output. From pipeline/:

    python3 osha_ita_u2.py \
        --bls ~/Downloads/table-1-injury-and-illness-rates-by-industry-2024-national.xlsx \
        --q2  ~/Downloads/quartile-table-2-days-away-restriction-and-job-transfer-cases-2024-national.xlsx

    writes data/gov/osha_ita_u2_2024.json, which scoring_engine.py reads into U.2

INPUTS, all public

    OSHA Injury Tracking Application, Form 300A summary data, 2024
        https://www.osha.gov/Establishment-Specific-Injury-and-Illness-Data
        downloaded once into ~/.hi_cache/osha/
    BLS SOII 2024, Table 1 (DART by detailed industry) and quartile table Q2 (DART by industry
    and establishment size)
        https://www.bls.gov/iif/nonfatal-injuries-and-illnesses-tables/soii-summary-historical.htm
        BLS refuses scripted downloads (403); download both in a browser and pass the paths
    data/scores/all_scores.json, for company names, tickers and headcounts

THE RULE (DECISION-u2-is-scored-against-peers-at-the-same-industry-and-size.md, option C)

    expected DART cases = sum over a company's establishments of
                          hours x BLS rate for that establishment's industry AT ITS SIZE / 200,000
    ratio  = (observed + 5) / (expected + 5)
    ratio >= 1:  score = 50 - 25.00 x log2(ratio)          full penalty
    ratio <  1:  score = 50 -  6.25 x log2(ratio), max 60   quarter credit: a low number can also
                                                            mean injuries went unreported
    zero recorded cases: max 50.  Clipped to 5-95.

    50 is the industry's rate for workplaces of the same size.

EVERY GUARD, AND THE DOCUMENT THAT EARNED IT

    row guards: 500-4,000 hours per employee, <= 60,000 employees per site, hours and employees > 0
        (MEASUREMENT-osha-reaches-339-companies-and-four-of-its-biggest-numbers-are-impossible)
    a company name equal to its ticker is a placeholder and is skipped (#92)
    names cleaned: accents, apostrophes, legal suffixes cut, "and" dangling
    strict match; loose matches ONLY through the 60 reviewed decisions below
        (MEASUREMENT-osha-v2-...; approved by Aaron 2026-11-25)
    word-boundary rule for spaces-removed matches; last word of a multi-word name may be a prefix
    reviewed aliases for legal names a brand cannot reach (FedEx -> Federal Express)
        (MEASUREMENT-u2-v7-fedex-was-load-bearing-...)
    rows at one address: identical numbers kept once; same name, latest kept; different names kept
    excluded: hours above 2x headcount x 2,000 (Netflix)
    review:   hours above 130% of headcount x 2,000
    below the floor: under 1,000,000 hours
    below share: under 10% of headcount x 2,000
    keyed by ticker, or company name when there is none, so tickerless companies never share a record

OUTPUT

    every matched company with its status, evidence and, if scored, its score. Only records whose
    status begins "scored" set U.2. Everything else is recorded so the reason for an absence is
    visible. No per-record timestamps, so an unchanged input produces an unchanged file.
"""
import argparse
import collections as C
import csv
import io
import json
import math
import re
import statistics as st
import unicodedata
import zipfile
from pathlib import Path

# Approved 2026-11-25 by Aaron ("they make sense for a baseline"). Keyed by (ticker, or the
# company name when there is no ticker; OSHA core name as v2 printed it).
DECISIONS = {
    ('AMZN', 'amazon com services'): ('accept', "Amazon.com Services LLC is Amazon's main US operating subsidiary (fulfilment)"),
    ('WMT', 'walmart stores east'): ('accept', 'Wal-Mart Stores East, LP is a Walmart operating subsidiary'),
    ('Publix', 'publix super markets'): ('accept', 'Publix Super Markets, Inc. is Publix itself; universe row has no ticker'),
    ('WMT', 'walmart stores texas'): ('accept', 'Walmart Stores Texas, LLC is a Walmart operating subsidiary'),
    ('WMT', 'wal mart stores east'): ('accept', 'hyphenated spelling of Wal-Mart Stores East'),
    ('NOC', 'northrop grumman systems'): ('accept', 'Northrop Grumman Systems Corp is the principal operating subsidiary'),
    ('CMCSA', 'comcast cable communications management'): ('accept', 'Comcast Cable Communications Management, LLC is a Comcast subsidiary'),
    ('FDX', 'fedex freight'): ('accept', 'FedEx Freight was a FedEx subsidiary in the 2024 data year. FedEx planned to spin it off; if that has completed, accept for 2024 data only'),
    ('Wegmans', 'wegmans food markets'): ('accept', 'Wegmans Food Markets, Inc. is Wegmans itself; no ticker'),
    ('DLTR', 'dollar tree stores'): ('accept', 'Dollar Tree Stores, Inc. is the operating subsidiary'),
    ('KR', 'kroger texas'): ('accept', 'Kroger Texas L.P., a Kroger division'),
    ('WMT', 'wal mart stores texas'): ('accept', 'hyphenated spelling of Walmart Stores Texas'),
    ('SO', 'southern glazers wine and spirits'): ('reject', "NAMESAKE: Southern Glazer's is a private drinks distributor, unrelated to Southern Co"),
    ('KR', 'kroger atlanta kma'): ('accept', 'Kroger division'),
    ('GPK', 'graphic packaging international'): ('accept', 'Graphic Packaging International, LLC is the operating subsidiary'),
    ('KO', 'coca cola consolidated'): ('reject', 'SEPARATE COMPANY: Coca-Cola Consolidated (NASDAQ: COKE) is an independent listed bottler, not controlled by KO'),
    ('SO', 'southern california edison'): ('reject', 'NAMESAKE: SCE belongs to Edison International'),
    ('KR', 'kroger cincinnati dayton kma'): ('accept', 'Kroger division'),
    ('DE', 'deere and'): ('accept', "'Deere & Company' with the company word cut; it is Deere"),
    ('KR', 'kroger louisville kma'): ('accept', 'Kroger division'),
    ('KR', 'kroger columbus kma'): ('accept', 'Kroger division'),
    ('GXO', 'gxo logistics supply chain'): ('accept', 'GXO Logistics Supply Chain, Inc. is a GXO subsidiary'),
    ('ALK', 'alaska airlines'): ('accept', "Alaska Airlines, Inc. is Alaska Air Group's operating subsidiary"),
    ('KR', 'kroger central kma'): ('accept', 'Kroger division'),
    ('KR', 'kroger michigan kma'): ('accept', 'Kroger division'),
    ('TXT', 'textron aviation'): ('accept', 'Textron Aviation Inc. is a Textron subsidiary'),
    ('KR', 'kroger mid atlantic kma'): ('accept', 'Kroger division'),
    ('ESNT', 'essentia health'): ('reject', 'NAMESAKE: Essentia Health is a nonprofit health system; Essent is a mortgage insurer. A word-boundary error, which v3 removes mechanically'),
    ('KR', 'kroger nashville kma'): ('accept', 'Kroger division'),
    ('KR', 'kroger delta kma'): ('accept', 'Kroger division'),
    ('WMT', 'walmart puerto rico'): ('accept', 'Walmart Puerto Rico, Inc. is a Walmart subsidiary'),
    ('GD', 'general dynamics mission systems'): ('accept', 'General Dynamics business unit'),
    ('SO', 'southern california gas'): ('reject', 'NAMESAKE: SoCalGas belongs to Sempra'),
    ('WMB', 'williams sonoma'): ('reject', 'NAMESAKE: Williams-Sonoma is a separate retailer'),
    ('Nestlé', 'nestle'): ('accept', "Nestlé; matched loosely only because the accent cut the universe name to 'nestl', which v3 fixes"),
    ('M', 'macys logistics and operations'): ('accept', "Macy's logistics division"),
    ('NVS', 'novartis pharmaceuticals'): ('accept', 'Novartis Pharmaceuticals Corporation is the US subsidiary'),
    ('LCID', 'lucid motors'): ('accept', "Lucid Motors is Lucid Group's operating company"),
    ('WMB', 'williamson county board of education'): ('reject', 'NAMESAKE: a Tennessee school system. A word-boundary error, which v3 removes mechanically'),
    ('Subaru', 'subaru of indiana automotive'): ('accept', 'Subaru of Indiana Automotive, Inc. is a Subaru Corporation subsidiary; no ticker'),
    ('GD', 'general dynamics bath iron works'): ('accept', 'General Dynamics shipyard'),
    ('FE', 'firstenergy service'): ('accept', 'FirstEnergy Service Company is a FirstEnergy subsidiary'),
    ('KR', 'kroger fulfillment network'): ('accept', 'Kroger division'),
    ('SYK', 'stryker employment'): ('accept', "Stryker Employment Company, LLC is Stryker's US employing entity"),
    ('XOM', 'exxonmobil'): ('accept', 'ExxonMobil written as one word; v3 treats a spaces-removed exact match as strict'),
    ('Nestlé', 'nestle purina petcare'): ('accept', 'Nestlé Purina PetCare is a Nestlé subsidiary'),
    ('LHX', 'l3harris technologies integrated systems'): ('accept', 'L3Harris business unit'),
    ('GXO', 'gxo logistics worldwide'): ('accept', 'GXO subsidiary'),
    ('SYK', 'stryker howmedica'): ('accept', 'Howmedica Osteonics is a Stryker subsidiary'),
    ('KO', 'coca cola beverages florida'): ('reject', 'SEPARATE COMPANY: an independent, privately held bottler, not KO'),
    ('INTU', 'intuitive'): ('reject', "NAMESAKE: 'intuitive' is not Intuit. A word-boundary error, which v3 removes mechanically"),
    ('MDT', 'medtronic sofamor danek'): ('accept', 'Medtronic subsidiary'),
    ('CLF', 'cleveland cliffs steel'): ('accept', 'Cleveland-Cliffs Steel LLC is the operating subsidiary'),
    ('L', 'loews hotels'): ('accept', 'Loews Hotels is owned by Loews Corp'),
    ('LOW', 'lowes foods'): ('reject', "NAMESAKE: Lowes Foods is a grocery chain unrelated to Lowe's"),
    ('MTZ', 'mastec mns wireline'): ('accept', 'MasTec subsidiary'),
    ('POST', 'post consumer brands'): ('accept', 'Post Consumer Brands is a Post Holdings subsidiary'),
    ('AEE', 'ameren missouri'): ('accept', 'Ameren Missouri is an Ameren subsidiary'),
    ('GD', 'general dynamics nassco'): ('accept', 'General Dynamics shipyard'),
    ('ULTA', 'ulta beauty distribution'): ('accept', 'Ulta distribution operation'),
}

ap = argparse.ArgumentParser()
ap.add_argument("--year", type=int, default=2024)
ap.add_argument("--zip", default=None)
ap.add_argument("--scores", default="data/scores/all_scores.json")
ap.add_argument("--floor-hours", type=int, default=1_000_000)
ap.add_argument("--min-share", type=float, default=0.10)
ap.add_argument("--k", type=float, default=5.0, help="credibility constant, in cases")
ap.add_argument("--bls", default=None, help="path to BLS Table 1 2024 xlsx, if downloaded by hand")
ap.add_argument("--full", action="store_true", help="also print v4's audit sections")
ap.add_argument("--q2", default=None, help="BLS quartile table Q2 (DART by industry and size), xlsx")
ap.add_argument("--out", default=None, help="default data/gov/osha_ita_u2_<year>.json")
args = ap.parse_args()
say = print if args.full else (lambda *a, **k: None)

CACHE = Path.home() / ".hi_cache" / "osha"
CACHE.mkdir(parents=True, exist_ok=True)
FILES = {2024: "ITA_300A_Summary_Data_2024_through_12-31-2025.zip",
         2023: "ITA_300A_Summary_Data_2023_through_12-31-2024.zip"}
path = Path(args.zip) if args.zip else CACHE / FILES.get(args.year, "")
OSHA_FILE = path.name     # captured now: the scoring loop below reuses the name `path`
if not path.exists():
    raise SystemExit(f"  {path} not found. Run measure_osha_ita_reach.py once, or pass --zip.")
SCORES = Path(args.scores)
if not SCORES.exists():
    raise SystemExit(f"  {SCORES} not found — run from pipeline/")
HPE_LO, HPE_HI, MAX_EMP = 500, 4000, 60_000


def num(x):
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return 0.0


# ── 1. read, dedupe, row guards (as v2) ─────────────────────────────────────────────
def rows_from(p):
    if p.suffix.lower() == ".zip":
        z = zipfile.ZipFile(p)
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        fh = io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace")
    else:
        fh = open(p, encoding="utf-8", errors="replace")
    for r in csv.DictReader(fh):
        yield {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}


estabs = {}
for r in rows_from(path):
    key = r.get("establishment_id") or (r.get("ein"), r.get("establishment_name"),
                                        r.get("zip_code"))
    if key in estabs and r.get("created_timestamp", "") < estabs[key].get("created_timestamp", ""):
        continue
    estabs[key] = r
kept, dropped = [], 0
for e in estabs.values():
    h, emp = num(e.get("total_hours_worked")), num(e.get("annual_average_employees"))
    if h <= 0 or emp <= 0 or emp > MAX_EMP or not (HPE_LO <= h / emp <= HPE_HI):
        dropped += 1
        continue
    kept.append(e)
print(f"{path.name}: {len(estabs):,} establishments, {dropped:,} dropped by the row guards, "
      f"{len(kept):,} kept")


# ── 2. names, with the four fixes ───────────────────────────────────────────────────
LEGAL = {"inc", "incorporated", "corp", "corporation", "co", "company", "companies", "llc",
         "ltd", "limited", "lp", "llp", "plc", "holdings", "holding", "group", "sa", "nv", "ag",
         "de", "usa", "us", "na"}
DANGLING = {"and", "of", "the"}


def core(name):
    n = unicodedata.normalize("NFKD", name or "")
    n = "".join(ch for ch in n if not unicodedata.combining(ch))      # Nestlé -> Nestle
    n = n.lower().replace("\\", "/")
    n = re.sub(r"/\s*[a-z]{2,3}\s*/?\s*$", "", n)
    n = re.sub(r"['’]", "", n)
    n = n.replace("&", " and ")
    n = re.sub(r"[^a-z0-9 ]+", " ", n)
    toks = n.split()
    while toks and toks[0] == "the":
        toks = toks[1:]
    for i, t in enumerate(toks[1:], start=1):
        if t in LEGAL:
            toks = toks[:i]
            break
    while toks and (toks[-1] in LEGAL or toks[-1] in DANGLING):   # "deere and" -> "deere"
        toks = toks[:-1]
    return " ".join(toks)


def despace(s):
    return s.replace(" ", "")


def boundary_prefix(k, d):
    """True if whole leading tokens of k, joined without spaces, spell exactly d.
    "wal mart stores east" spells "walmart" after two tokens; "essentia health" never spells
    "essent", because "essentia" overshoots it inside a single word."""
    acc = ""
    for t in k.split():
        acc += t
        if acc == d:
            return True
        if len(acc) >= len(d):
            return False
    return False


# ── BLS Table 1, read with the standard library only ───────────────────────────────
import urllib.request
import xml.etree.ElementTree as ET

BLS_URL = ("https://www.bls.gov/iif/nonfatal-injuries-and-illnesses-tables/"
           "table-1-injury-and-illness-rates-by-industry-2024-national.xlsx")
BLS_DIR = Path.home() / ".hi_cache" / "bls"
BLS_DIR.mkdir(parents=True, exist_ok=True)
bls_path = Path(args.bls) if args.bls else BLS_DIR / BLS_URL.rsplit("/", 1)[1]
if not bls_path.exists():
    print(f"downloading BLS Table 1 (2024)\n   {BLS_URL}")
    try:
        req = urllib.request.Request(BLS_URL, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*"})
        with urllib.request.urlopen(req, timeout=120) as r, open(bls_path, "wb") as f:
            f.write(r.read())
    except Exception as e:                                          # noqa: BLE001
        if bls_path.exists():
            bls_path.unlink()
        raise SystemExit(f"  BLS download failed ({type(e).__name__}: {e}).\n"
                         f"  Open the URL above in your browser, save the file into\n"
                         f"  {BLS_DIR}/\n  and run this again.")
NSX = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def xlsx_rows(p):
    z = zipfile.ZipFile(p)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(NSX + "si"):
            ss.append("".join(t.text or "" for t in si.iter(NSX + "t")))
    sheet = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))[0]
    for row in ET.fromstring(z.read(sheet)).iter(NSX + "row"):
        cells = {}
        for c in row.iter(NSX + "c"):
            col = re.match(r"[A-Z]+", c.get("r", "A")).group(0)
            idx = 0
            for ch in col:
                idx = idx * 26 + (ord(ch) - 64)
            v, t = c.find(NSX + "v"), c.get("t")
            if t == "s" and v is not None:
                val = ss[int(v.text)]
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter(NSX + "t"))
            else:
                val = v.text if v is not None else ""
            cells[idx] = (val or "").strip()
        if cells:
            yield [cells.get(i, "") for i in range(1, max(cells) + 1)]


def clean(x):
    return re.sub(r"\(\d+\)", "", x or "").strip()


def fnum(x):
    x = clean(x)
    try:
        return float(x)
    except ValueError:
        return None


BLS, private_dart = {}, None
for row in xlsx_rows(bls_path):
    if len(row) < 7:
        continue
    name, code = clean(row[0]), clean(row[1])
    vals = [fnum(v) for v in row[2:7]]          # TRC, DART, DAFW, DJTR, other
    if vals[1] is None:
        continue
    if name.lower().startswith("private industry") and not code:
        private_dart = vals[1]
    m = re.match(r"^(\d{2})-(\d{2})$", code)
    if m:                                        # "44-45", "31-33", "48-49"
        for c2 in range(int(m.group(1)), int(m.group(2)) + 1):
            BLS.setdefault(str(c2), vals[1])
    elif re.match(r"^\d{2,6}$", code):
        BLS[code] = vals[1]
CHECKS = {"336411": 1.4, "32411": 0.2, "452": 2.5, "44511": 2.7, "336111": 4.2}
bad = {k: (BLS.get(k), v) for k, v in CHECKS.items() if BLS.get(k) != v}
print(f"BLS Table 1 (2024): {len(BLS):,} NAICS codes with a DART rate; private industry "
      f"{private_dart}")
if private_dart != 1.4 or bad:
    raise SystemExit(f"  the table did not read as expected (private {private_dart}, checks {bad});"
                     f" stopping rather than scoring from a misread table")
print("   checks against rows read from the BLS page: private 1.4, aircraft 1.4, refineries 0.2,"
      " general merchandise 2.5, supermarkets 2.7, autos 4.2 -- all match")


def to_2017(code):
    """NAICS 2022 retail and publishing codes the 2024 table does not have."""
    if code.startswith("4551"):
        return "4522" + code[4:]
    if code.startswith("4552"):
        return "4523" + code[4:]
    if code.startswith("455"):
        return "452" + code[3:]
    if code.startswith("5132"):
        return "5112" + code[4:]
    return code


def bls_rate(naics):
    """Most specific level first, trying the code as filed AND its 2017 equivalent at each level.
    Trying every level of the filed code first would let "45" (all retail) win before the
    2017 equivalent's 6-digit "452311" (warehouse clubs) was ever tried."""
    code = re.sub(r"\D", "", naics or "")
    for L in (6, 5, 4, 3, 2):
        for cand in (code, to_2017(code)):
            if len(cand) >= L and cand[:L] in BLS:
                return BLS[cand[:L]], L
    return None, None


# ── BLS Q2: DART by industry AND establishment size ────────────────────────────────
Q2_NAME = "quartile-table-2-days-away-restriction-and-job-transfer-cases-2024-national.xlsx"
q2_path = Path(args.q2) if args.q2 else BLS_DIR / Q2_NAME
if not q2_path.exists():
    alt = Path.home() / "Downloads" / Q2_NAME
    q2_path = alt if alt.exists() else q2_path
if not q2_path.exists():
    raise SystemExit(f"  Q2 not found. Download it in a browser:\n  https://www.bls.gov/iif/"
                     f"nonfatal-injuries-and-illnesses-tables/{Q2_NAME}\n  and pass --q2 <path>")
SIZES = {"total all sizes": "all", "1 - 10": "1-10", "11 - 49": "11-49", "50 - 249": "50-249",
         "250 - 999": "250-999", "1,000+": "1000+"}
Q2, heading, q2_headings = {}, None, 0
for row in xlsx_rows(q2_path):
    first = (row[0] if row else "").replace("\xa0", " ").strip()
    if first and not any(x for x in row[1:]):
        m = re.search(r"\(NAICS\s*([\d\-]+)\)", first)
        if m:
            q2_headings += 1
            code = m.group(1)
            heading = code if "-" in code else (code.rstrip("0") or code)
        elif re.match(r"Private industry\d*$", first):
            heading = "PRIVATE"
        else:
            heading = None                 # sector groupings without a code, and footnotes
        continue
    lab = SIZES.get(first.lower())
    if lab and heading and len(row) > 1:
        v = fnum(row[1])
        if v is None:
            continue
        r_ = re.match(r"^(\d{2})-(\d{2})$", heading)
        codes = [str(c) for c in range(int(r_.group(1)), int(r_.group(2)) + 1)] if r_ else [heading]
        for c_ in codes:
            Q2.setdefault(c_, {})[lab] = v
P = Q2.get("PRIVATE", {})
want = {"all": 1.4, "1-10": 0.5, "250-999": 1.7, "1000+": 1.6}
if any(P.get(k) != v for k, v in want.items()):
    raise SystemExit(f"  Q2 did not read as expected: private industry {P}; stopping")
SIZE_FACTOR = {k: P[k] / P["all"] for k in ("1-10", "11-49", "50-249", "250-999", "1000+")}
both = [c for c in Q2 if c in BLS and "all" in Q2[c]]
agree = sum(1 for c in both if abs(Q2[c]["all"] - BLS[c]) <= 0.05)
print(f"BLS Q2 (2024): {q2_headings:,} industry headings, {len(Q2):,} codes with a size breakdown")
print(f"   private industry by size: " + "  ".join(f"{k} {P[k]}" for k in
      ("all", "1-10", "11-49", "50-249", "250-999", "1000+")))
print(f"   Q2 all-sizes agrees with Table 1 for {agree} of {len(both)} codes in both")
if not both or agree < 0.9 * len(both):
    raise SystemExit("  the two BLS tables disagree; the code mapping is wrong; stopping")


def size_class(emp):
    return ("1-10" if emp <= 10 else "11-49" if emp <= 49 else "50-249" if emp <= 249
            else "250-999" if emp <= 999 else "1000+")


def size_rate(naics, emp):
    """(rate, level, path). Most specific level first; at each level the size cell from Q2 if
    published, else Table 1's all-sizes rate times the national factor for that size class."""
    code, sc = re.sub(r"\D", "", naics or ""), size_class(emp)
    for L in (6, 5, 4, 3, 2):
        for cand in (code, to_2017(code)):
            k = cand[:L] if len(cand) >= L else None
            if not k:
                continue
            if k in Q2 and sc in Q2[k]:
                return Q2[k][sc], L, "size cell"
            if k in BLS:
                return BLS[k] * SIZE_FACTOR[sc], L, "industry x size factor"
    return None, None, None


def score_of(obs, ratio, fav_cap=70.0):
    if ratio is None:
        return None, ""
    sc_ = max(5.0, min(95.0, 50 - 25 * math.log2(ratio)))
    if obs == 0 and sc_ > 50:
        return 50.0, "zero capped at industry"
    if ratio < 1 and sc_ > fav_cap:
        return fav_cap, f"below-industry capped at {fav_cap:g}"
    return sc_, ""


# Reviewed 2026-11-27. A legal name the brand name cannot reach. Matched strictly, never loosely.
ALIASES = {
    "FDX": [("Federal Express Corporation",
             "FedEx Express's legal name; v6 showed FDX matched FedEx Freight alone")],
}


def partial_last(k, toks):
    """A multi-word name whose last word is the start of the OSHA word in that position:
    "alaska air" -> "alaska airlines". One-word names never qualify, so "intuit" cannot reach
    "intuitive" and "essent" cannot reach "essentia"."""
    kt = k.split()
    n = len(toks)
    return (n >= 2 and len(kt) >= n and kt[:n - 1] == toks[:-1]
            and kt[n - 1] != toks[-1] and kt[n - 1].startswith(toks[-1]))


def norm_addr(e):
    a = re.sub(r"[^a-z0-9 ]+", " ", (e.get("street_address") or "").lower())
    a = re.sub(r"\b(street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|highway|hwy|suite|ste)\b",
               "", a)
    return " ".join(a.split()), (e.get("zip_code") or "")[:5]


def lookup(key, k):
    """(decision, how). Exact first; then a stored name that v2's display cut at 40 characters."""
    dec = DECISIONS.get((key, k))
    if dec:
        return dec, (key, k), "exact"
    for (dk, dn), dv in DECISIONS.items():
        if dk == key and len(dn) == 40 and k.startswith(dn) and k != dn:
            return dv, (dk, dn), "display-truncated key"
    return None, None, None


raw = json.load(open(SCORES))
universe = raw if isinstance(raw, list) else list(raw.values())
universe = [u for u in universe if isinstance(u, dict) and (u.get("company") or "").strip()]


def headcount_of(u):
    stack = [u]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            for k, v in o.items():
                if str(k).lower() in ("headcount", "employees", "full_time_employees") and \
                        isinstance(v, (int, float)) and v > 0:
                    return float(v)
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(o, list):
            stack.extend(o)
    return None


ucore = C.defaultdict(list)
for u in universe:
    if u["company"].strip() == (u.get("ticker") or "").strip():
        continue
    u["_hc"] = headcount_of(u)
    u["_key"] = (u.get("ticker") or "").strip() or u["company"].strip()
    c = core(u["company"])
    if c:
        ucore[c].append(u)

by_osha = C.defaultdict(list)
for e in kept:
    c = core(e.get("company_name"))
    if c:
        by_osha[c].append(e)
by_despaced, by_prefix = C.defaultdict(list), C.defaultdict(list)
for k in by_osha:
    by_despaced[despace(k)].append(k)
    by_prefix[despace(k)[:4]].append(k)


# ── 3. match: strict, then reviewed loose ───────────────────────────────────────────
used_decisions, out_rows, truncated_hits, alias_hits = set(), [], [], []
path_hours, size_hours = C.Counter(), C.Counter()
level_hours, unrated_codes = C.Counter(), C.Counter()
stats = C.Counter()
loose_unreviewed_hours = 0.0
for c, us in ucore.items():
    if len(us) != 1:
        continue
    u, toks, d = us[0], c.split(), despace(c)
    strict_keys = sorted(set([c] if c in by_osha else []) |
                         {k for k in by_despaced.get(d, []) if k != c})
    for alias, why in ALIASES.get(u["_key"], []):
        ac = core(alias)
        hit = sorted({k for k in ([ac] if ac in by_osha else []) + by_despaced.get(despace(ac), [])})
        for k in hit:
            if k not in strict_keys:
                strict_keys.append(k)
                alias_hits.append((u["_key"], alias, k, len(by_osha[k])))
    loose = [k for k in by_prefix.get(d[:4], []) if k not in strict_keys and k != c and (
        k.split()[:len(toks)] == toks or boundary_prefix(k, d) or partial_last(k, toks))]
    accepted, rejected = [], []
    for k in loose:
        dec, dkey, how = lookup(u["_key"], k)
        if dec:
            used_decisions.add(dkey)
            if how != "exact":
                truncated_hits.append((u["_key"], k))
            (accepted if dec[0] == "accept" else rejected).append(k)
        else:
            loose_unreviewed_hours += sum(num(e.get("total_hours_worked")) for e in by_osha[k])
            stats["loose names left unreviewed"] += 1
    names = strict_keys + accepted
    if not names:
        continue
    es_all = [e for k in names for e in by_osha[k]]
    # rows sharing a street address + ZIP, resolved three ways (see the docstring)
    groups, es = C.defaultdict(list), []
    for e in es_all:
        a = norm_addr(e)
        if not a[0]:
            es.append(e)
            continue
        groups[a].append(e)
    same_grp = resub = distinct_kept = diff_grp = 0
    for g_ in groups.values():
        if len(g_) == 1:
            es.append(g_[0])
            continue
        uniq = {}
        for x in g_:
            sig = (num(x.get("total_hours_worked")), num(x.get("annual_average_employees")),
                   num(x.get("total_dafw_cases")), num(x.get("total_djtr_cases")))
            uniq.setdefault(sig, x)
        if len(uniq) == 1:
            same_grp += 1
            es.append(next(iter(uniq.values())))
            continue
        diff_grp += 1
        by_name = {}
        for x in uniq.values():
            nm = re.sub(r"[^a-z0-9]+", " ", (x.get("establishment_name") or "").lower()).strip()
            if nm in by_name:
                resub += 1
                if x.get("created_timestamp", "") > by_name[nm].get("created_timestamp", ""):
                    by_name[nm] = x
            else:
                by_name[nm] = x
        es.extend(by_name.values())
        distinct_kept += len(by_name) - 1
    addr_dupes = len(es_all) - len(es)
    hours = sum(num(e.get("total_hours_worked")) for e in es)
    emp = sum(num(e.get("annual_average_employees")) for e in es)
    dart = sum(num(e.get("total_dafw_cases")) + num(e.get("total_djtr_cases")) for e in es)
    # expected cases from each establishment's own industry, on the establishments BLS can rate
    obs = exp = rated_h = 0.0
    for e in es:
        r, L = bls_rate(e.get("naics_code"))
        h = num(e.get("total_hours_worked"))
        level_hours[L] += h
        if r is None:
            unrated_codes[re.sub(r"\D", "", e.get("naics_code") or "") or "(blank)"] += h
            continue
        rated_h += h
        exp += h * r / 200_000
        obs += num(e.get("total_dafw_cases")) + num(e.get("total_djtr_cases"))
    ratio = (obs + args.k) / (exp + args.k) if rated_h else None
    score, cap = score_of(obs, ratio)
    # the size-matched expected, on the same establishments
    exp_s, paths, by_code = 0.0, C.Counter(), C.defaultdict(lambda: [0.0, 0.0])
    for e in es:
        h = num(e.get("total_hours_worked"))
        r_s, L_s, path = size_rate(e.get("naics_code"), num(e.get("annual_average_employees")))
        if r_s is None or bls_rate(e.get("naics_code"))[0] is None:
            continue
        exp_s += h * r_s / 200_000
        paths[path] += h
        path_hours[path] += h
        size_hours[size_class(num(e.get("annual_average_employees")))] += h
        cd = re.sub(r"\D", "", e.get("naics_code") or "") or "?"
        by_code[cd][0] += h
        by_code[cd][1] += h * r_s / 200_000
    ratio_s = (obs + args.k) / (exp_s + args.k) if rated_h else None
    score_s, cap_s = score_of(obs, ratio_s)
    hc = u["_hc"]
    share = hours / (hc * 2000) if hc else None
    if hc and hours > 2 * hc * 2000:
        status = "excluded: hours exceed twice headcount"
    elif share is not None and share > 1.3:
        status = "review: hours exceed headcount"
    elif hours < args.floor_hours:
        status = "below hours floor"
    elif share is not None and share < args.min_share:
        status = "below workforce share"
    else:
        status = "scored" if share is not None else "scored, headcount unknown"
    if status.startswith("scored") and not rated_h:
        status = "no BLS industry rate for its NAICS codes"
    stats[status] += 1
    out_rows.append({"key": u["_key"], "ticker": u.get("ticker") or "", "company": u["company"],
                     "industry": u.get("industry") or "", "estabs": len(es), "hours": hours,
                     "osha_us_employees": emp, "headcount": hc, "workforce_share": share,
                     "dart_cases": dart, "dart_rate": dart * 200_000 / hours if hours else None,
                     "status": status, "strict_names": len(strict_keys),
                     "estabs_before_address_dedupe": len(es_all), "address_dupes": addr_dupes,
                     "raw_names": C.Counter(e.get("company_name", "") for e in es_all),
                     "accepted_names": len(accepted), "rejected_names": len(rejected),
                     "observed_cases": obs, "expected_cases": exp, "rated_hours": rated_h,
                     "expected_rate": exp * 200_000 / rated_h if rated_h else None,
                     "ratio": ratio, "score": score, "cap": cap,
                     "expected_cases_size": exp_s,
                     "expected_rate_size": exp_s * 200_000 / rated_h if rated_h else None,
                     "ratio_size": ratio_s, "score_size": score_s, "cap_size": cap_s,
                     "dedupe_identical_groups": same_grp, "dedupe_differing_groups": diff_grp,
                     "dedupe_resubmissions": resub, "dedupe_distinct_kept": distinct_kept,
                     "top_codes": sorted(((h_, x_, cd) for cd, (h_, x_) in by_code.items()),
                                         reverse=True)[:3],
                     "current_u2": ((u.get("genome") or {}).get("U") or {}).get("scores", {})
                                   .get("U.2")})


# ── RULE C, AND THE OUTPUT FILE ─────────────────────────────────────────────────────
RULE = {"above_slope": 25.0, "below_slope": 6.25, "below_cap": 60.0, "zero_cap": 50.0,
        "clip_low": 5.0, "clip_high": 95.0, "credibility_k": args.k}


def score_c(obs, ratio):
    if ratio is None:
        return None
    lg = math.log2(ratio)
    s = 50 - (RULE["above_slope"] if ratio >= 1 else RULE["below_slope"]) * lg
    s = max(RULE["clip_low"], min(RULE["clip_high"], s))
    if obs == 0:
        s = min(s, RULE["zero_cap"])
    if ratio < 1:
        s = min(s, RULE["below_cap"])
    return round(s, 1)


def rnd(x, n):
    return None if x is None else round(x, n)


companies = {}
for r in sorted(out_rows, key=lambda r: r["key"]):
    scored = r["status"].startswith("scored")
    rh = r["rated_hours"] or 0
    companies[r["key"]] = {
        "ticker": r["ticker"], "company": r["company"], "status": r["status"],
        "score": score_c(r["observed_cases"], r["ratio_size"]) if scored else None,
        "establishments": r["estabs"], "hours": round(r["hours"]), "rated_hours": round(rh),
        "osha_us_employees": round(r["osha_us_employees"]), "headcount": r["headcount"],
        "workforce_share": rnd(r["workforce_share"], 4),
        "observed_dart_cases": int(r["observed_cases"]),
        "expected_dart_cases": rnd(r["expected_cases_size"], 2),
        "dart_rate": rnd(r["observed_cases"] * 200_000 / rh, 3) if rh else None,
        "expected_dart_rate": rnd(r["expected_rate_size"], 3),
        "ratio": rnd(r["ratio_size"], 4),
        "ratio_national_all_sizes": rnd(r["ratio"], 4),
        "industries": [[cd, round(h / rh, 3), round(x * 200_000 / h, 3)]
                       for h, x, cd in r["top_codes"] if h and rh],
    }
bad = [k for k, v in companies.items() if v["status"].startswith("scored") and v["score"] is None]
if bad:
    raise SystemExit(f"  scored records without a score: {bad[:5]}; nothing written")

counts = C.Counter(v["status"] for v in companies.values())
from datetime import date
meta = {
    "source": "OSHA Injury Tracking Application, Form 300A summary data",
    "data_year": args.year, "osha_file": OSHA_FILE,
    "bls_table1": bls_path.name, "bls_q2": q2_path.name,
    "bls_private_industry_dart_by_size": P,
    "rule": RULE, "rule_doc": "DECISION-u2-is-scored-against-peers-at-the-same-industry-and-size.md",
    "guards": {"hours_per_employee": [HPE_LO, HPE_HI], "max_employees_per_site": MAX_EMP,
               "floor_hours": args.floor_hours, "min_workforce_share": args.min_share,
               "review_above_share": 1.3, "exclude_above_share": 2.0},
    "reviewed_loose_decisions": len(DECISIONS), "aliases": {k: [a for a, _ in v] for k, v in ALIASES.items()},
    "counts": dict(sorted(counts.items())),
    "generated": date.today().isoformat(), "collector": "osha_ita_u2.py v1",
}
OUT = Path(args.out) if args.out else Path("data/gov") / f"osha_ita_u2_{args.year}.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w") as f:
    json.dump({"meta": meta, "companies": companies}, f, indent=1, sort_keys=True, ensure_ascii=False)
    f.write("\n")

sc = [v for v in companies.values() if v["score"] is not None]
print(f"\n\nWROTE {OUT}  ({OUT.stat().st_size/1e6:.1f} MB, {len(companies)} companies)\n")
for k_, n_ in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"   {k_:44} {n_:>5}")
if sc:
    ss = sorted(v["score"] for v in sc)
    pick = lambda p: ss[min(len(ss) - 1, int(p * (len(ss) - 1) + 0.5))]
    print(f"\n   U.2 among scored: p10 {pick(.1):.0f}  p50 {pick(.5):.0f}  p90 {pick(.9):.0f}  "
          f"at the 60 cap {sum(1 for x in ss if x == 60)}  below 35 {sum(1 for x in ss if x < 35)}")
    print("\n   " + "  ".join(f"{t} {companies[t]['score']:.0f}" for t in
          ("WMT", "AMZN", "UPS", "HD", "LOW", "KR", "TGT", "FDX", "COST")
          if t in companies and companies[t]["score"] is not None))
print("\nNothing else in the repository was touched. Commit the file above with the collector.")
