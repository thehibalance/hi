"""HI Grade — cached SEC ticker index.  # HI-PATCH:sec-index:v1

One local cache of SEC's company_tickers.json, serving two problems at once:
  1. CIK lookup was re-downloading the full ~794 KB file once per company
     (~700 MB per run) against an API with a published fair-use policy.
  2. 98 tickers reach the collector with no name. SEC has the official name
     for every filer.
Also normalizes share classes: SEC writes BRK-B; universes carry BRK.B.
"""
import atexit, json, time
from pathlib import Path
from urllib.request import Request, urlopen

SEC_URL = "https://www.sec.gov/files/company_tickers.json"
USER_AGENT = "HI-Pipeline/1.0 (thehibalance.org; contact@thehibalance.org)"
CACHE = Path("data/sec_index.json")
MAX_AGE_HOURS = 168
_INDEX = None

# ── Remembered CIKs (v1.8.1) ─────────────────────────────────────────────
# SEC's ticker directory churns. AvalonBay and Equity Residential both dropped
# out of company_tickers.json between two runs a week apart while filing
# normally; 39 universe symbols are unlisted on any given day. A CIK is an
# identifier, not a measurement, so once we have resolved one we keep it and
# say so when we use it. This is not the score ratchet v1.8.0 removed: a score
# must be re-earned every night, a company's CIK does not change because a JSON
# file dropped a row.
LEARNED_PATH = Path("data/cik_map.json")
_LEARNED = None
_LEARNED_DIRTY = False
_NOTED = set()


def _learned():
    global _LEARNED
    if _LEARNED is None:
        try:
            _LEARNED = json.load(open(LEARNED_PATH))
        except Exception:
            _LEARNED = {}
    return _LEARNED


def _remember(ticker, cik, title):
    global _LEARNED_DIRTY
    m = _learned()
    if m.get(ticker, {}).get("cik") != cik:
        m[ticker] = {"cik": cik, "title": title}
        _LEARNED_DIRTY = True


def flush_learned():
    if not _LEARNED_DIRTY or not _LEARNED:
        return
    try:
        LEARNED_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = LEARNED_PATH.with_suffix(".tmp")
        json.dump(_LEARNED, open(tmp, "w"), indent=2, sort_keys=True)
        tmp.replace(LEARNED_PATH)
    except OSError as e:
        print(f"  could not save the CIK map: {e}")


atexit.register(flush_learned)


def _variants(ticker):
    t = str(ticker).strip().upper()
    out = [t]
    if "." in t: out.append(t.replace(".", "-"))
    if "-" in t: out.append(t.replace("-", "."))
    return out

def _download():
    req = Request(SEC_URL, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=45) as r:
        raw = r.read()
    idx = {}
    for e in json.loads(raw.decode()).values():
        t = str(e.get("ticker","")).strip().upper()
        if t:
            idx[t] = {"cik": str(e.get("cik_str","")).zfill(10),
                      "title": str(e.get("title",""))}
    return idx

def load_sec_index(force=False):
    global _INDEX
    if _INDEX is not None and not force:
        return _INDEX
    if not force and CACHE.exists():
        if (time.time() - CACHE.stat().st_mtime)/3600 < MAX_AGE_HOURS:
            try:
                _INDEX = json.load(open(CACHE)); return _INDEX
            except Exception: pass
    try:
        idx = _download()
    except Exception as e:
        if CACHE.exists():
            print(f"  SEC index download failed ({e}); using stale cache")
            _INDEX = json.load(open(CACHE)); return _INDEX
        print(f"  SEC index unavailable: {e}")
        _INDEX = {}; return _INDEX
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(".tmp"); json.dump(idx, open(tmp,"w")); tmp.replace(CACHE)
    _INDEX = idx
    print(f"  SEC index cached: {len(idx):,} tickers")
    return _INDEX

def get_cik(ticker):
    idx = load_sec_index()
    for v in _variants(ticker):
        if v in idx:
            _remember(v, idx[v]["cik"], idx[v]["title"])
            return idx[v]["cik"]
    m = _learned()
    for v in _variants(ticker):
        if v in m:
            if v not in _NOTED:
                _NOTED.add(v)
                print(f"    SEC's directory no longer lists {v}; using the CIK "
                      f"resolved earlier ({m[v]['cik']}) — {m[v].get('title', '')}")
            return m[v]["cik"]
    return None

def get_title(ticker):
    idx = load_sec_index()
    for v in _variants(ticker):
        if v in idx: return idx[v]["title"]
    m = _learned()
    for v in _variants(ticker):
        if v in m: return m[v].get("title")
    return None

def verify(ticker, expected_name):
    """Does this ticker still belong to the company we think it does?
    PARA was Paramount Global; it is now Banzai International. Conservative:
    unknown ticker or missing name returns ok, so it never blocks on thin
    evidence. Returns (ok, sec_title)."""
    title = get_title(ticker)
    if not title or not expected_name: return True, title
    stop = {"inc","corp","corporation","co","company","companies","ltd","limited",
            "plc","lp","llc","the","group","holdings","holding","class","trust",
            "international","cos","and"}
    def toks(s):
        s = "".join(c if c.isalnum() else " " for c in str(s).lower())
        return {w for w in s.split() if len(w) > 1 and w not in stop}
    a, b = toks(expected_name), toks(title)
    if not a or not b: return True, title
    if a & b: return True, title
    ja, jb = "".join(sorted(a)), "".join(sorted(b))
    if ja in jb or jb in ja: return True, title
    for x in a:
        for y in b:
            if x.startswith(y) or y.startswith(x): return True, title
    return False, title

if __name__ == "__main__":
    import sys
    idx = load_sec_index(force="--force" in sys.argv)
    print(f"{len(idx):,} tickers in index")
    for t in [a for a in sys.argv[1:] if not a.startswith("--")] or ["AAPL","BRK.B","MMC","PARA","XYZ"]:
        print(f"  {t:8} cik={get_cik(t) or '-':12} {get_title(t) or 'NOT FOUND'}")
