#!/usr/bin/env python3
"""HI Grade — build a ticker -> domain cache from FMP profiles.

load_company_list() hardcodes domains: [] for universe tickers, so ~700 companies
lose a subsignal (HIBP needs a domain). FMP's profile endpoint already returns the
company website and fetch_fmp() already calls that endpoint — the value was being
fetched and thrown away.

Curated multi-domain entries in sp500_domains.DOMAIN_MAP always win; this only
fills the gaps.

  python3 build_domains.py            # build/refresh the cache
  python3 build_domains.py --force    # ignore cache age
"""
import json, os, re, sys, time
from pathlib import Path
from urllib.request import urlopen

CACHE = Path("data/domains_cache.json")
MAX_AGE_DAYS = 30

def to_domain(url):
    if not url or not isinstance(url, str): return None
    u = url.strip().lower()
    u = re.sub(r"^[a-z][a-z0-9+.-]*://", "", u)
    u = u.split("/")[0].split("?")[0].split("#")[0]
    u = u.split("@")[-1].split(":")[0]
    if u.startswith("www."): u = u[4:]
    if not u or "." not in u: return None
    if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", u): return None
    return u

def get_key():
    k = os.environ.get("FMP_KEY") or os.environ.get("FMP_API_KEY") or ""
    if not k and Path("data/fmp_key.txt").exists():
        k = Path("data/fmp_key.txt").read_text().strip()
    return k

def main():
    force = "--force" in sys.argv
    key = get_key()
    if not key:
        print("no FMP key (FMP_KEY / FMP_API_KEY / data/fmp_key.txt)"); return 1

    cache = {}
    if CACHE.exists() and not force:
        age = (time.time() - CACHE.stat().st_mtime) / 86400
        try: cache = json.load(open(CACHE))
        except Exception: cache = {}
        print(f"existing cache: {len(cache)} entries, {age:.1f} days old")

    try:
        import universe_tickers as u
        tickers = set(u.get_all_tickers())
    except Exception as e:
        print(f"cannot load universe: {e}"); return 1
    try:
        from sp500_domains import DOMAIN_MAP
        curated = {k.upper() for k in DOMAIN_MAP}
    except Exception:
        curated = set()

    todo = sorted(t for t in tickers if t not in cache and t not in curated)
    print(f"universe {len(tickers)}  curated {len(curated)}  to fetch {len(todo)}")
    if not todo:
        print("nothing to do"); return 0

    ok = miss = fail = 0
    for i, t in enumerate(todo, 1):
        try:
            url = f"https://financialmodelingprep.com/stable/profile?symbol={t}&apikey={key}"
            d = json.loads(urlopen(url, timeout=15).read())
            rec = d[0] if isinstance(d, list) and d else (d if isinstance(d, dict) else None)
            dom = to_domain((rec or {}).get("website"))
            if dom:
                cache[t] = dom; ok += 1
            else:
                cache[t] = None; miss += 1
        except Exception:
            fail += 1
        if i % 100 == 0:
            print(f"  {i}/{len(todo)}  found {ok}  none {miss}  failed {fail}")
        time.sleep(0.21)          # ~285/min, under the 300/min Starter limit

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(".tmp")
    json.dump(cache, open(tmp, "w"), indent=0, sort_keys=True)
    tmp.replace(CACHE)
    have = sum(1 for v in cache.values() if v)
    print(f"\nwrote {CACHE}: {len(cache)} tickers, {have} with a domain")
    print(f"  found {ok}  no website {miss}  fetch failed {fail}")
    return 0

sys.exit(main())
