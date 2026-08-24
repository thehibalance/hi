#!/usr/bin/env python3
"""HI Grade — Ticker Universe Audit v2. Read-only.
  OK / FORMAT (dot vs dash) / RENAMED (recoverable) / MISMATCH (danger) / DEAD (prune)
"""
import argparse, json, re, sys
from pathlib import Path
from urllib.request import Request, urlopen

UA = "HI-Pipeline/1.0 (thehibalance.org; contact@thehibalance.org)"
STOP = {"inc","inc.","incorporated","corp","corp.","corporation","co","co.","company",
        "companies","ltd","ltd.","limited","plc","lp","llc","the","group","holdings",
        "holding","class","a","b","c","&","and","sa","nv","ag","se","trust",
        "international","intl","new","common","stock","cos"}

def tokens(name):
    return {t for t in re.sub(r"[^a-z0-9 ]"," ",str(name).lower()).split()
            if t and t not in STOP and len(t) > 1}

def variants(t):
    t = t.strip().upper(); out = {t}
    if "." in t: out.add(t.replace(".","-"))
    if "-" in t: out.add(t.replace("-","."))
    return out

def fetch_index():
    req = Request("https://www.sec.gov/files/company_tickers.json",
                  headers={"User-Agent": UA, "Accept":"application/json"})
    raw = urlopen(req, timeout=45).read()
    by_ticker, by_token = {}, {}
    for e in json.loads(raw.decode()).values():
        t = str(e.get("ticker","")).strip().upper(); title = str(e.get("title",""))
        if not t: continue
        by_ticker[t] = {"cik": e.get("cik_str"), "title": title}
        key = frozenset(tokens(title))
        if key: by_token.setdefault(key, []).append((t, title, e.get("cik_str")))
    return by_ticker, by_token, len(raw)

def find_by_name(name, by_token):
    a = tokens(name)
    if not a: return []
    best = []
    for key, entries in by_token.items():
        if not key: continue
        ov = len(a & key)
        if ov and ov >= min(len(a), len(key)) * 0.6:
            best.extend((ov, t, title, cik) for t, title, cik in entries)
    best.sort(key=lambda x: -x[0]); return best[:3]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    by_ticker, by_token, nbytes = fetch_index()
    print(f"SEC index: {len(by_ticker):,} tickers ({nbytes:,} bytes)\n")

    pairs = {}
    def put(t, name):
        t = str(t).strip().upper()
        if not t: return
        name = str(name or "").strip(); cur = pairs.get(t, "")
        if not cur or cur.upper() == t: pairs[t] = name
    sp = Path("data/scores/all_scores.json")
    if sp.exists():
        for r in json.load(open(sp)): put(r.get("ticker"), r.get("company"))
    try:
        from sp500_companies import SP500
        for it in SP500:
            if isinstance(it,(tuple,list)) and len(it)>=2: put(it[0], it[1])
            elif isinstance(it,str): put(it, "")
    except Exception as e: print(f"  sp500_companies unavailable: {e}")
    try:
        import universe_tickers as u
        for t in list(getattr(u,"SP500",[]))+list(getattr(u,"RUSSELL_1000_ADDITIONS",[])):
            if isinstance(t,str): put(t, "")
    except Exception as e: print(f"  universe_tickers unavailable: {e}")
    print(f"universe: {len(pairs):,} tickers\n")

    ok=[]; fmt=[]; renamed=[]; mismatch=[]; dead=[]; noname=[]
    for t, name in sorted(pairs.items()):
        hit=None; used=None
        for v in variants(t):
            if v in by_ticker: hit, used = by_ticker[v], v; break
        if hit:
            if used != t: fmt.append((t, used, hit["title"])); continue
            if not name or name.upper()==t: noname.append(t); continue
            a,b = tokens(name), tokens(hit["title"])
            if a and b and not (a&b): mismatch.append((t,name,hit["title"],hit["cik"]))
            else: ok.append(t)
            continue
        if name and name.upper()!=t:
            c = find_by_name(name, by_token)
            if c: renamed.append((t, name, c[0][1], c[0][2])); continue
        dead.append((t,name))

    print("="*74); print("  RESULTS"); print("="*74)
    print(f"  OK        {len(ok)}")
    print(f"  no name   {len(noname)}   (in SEC, no name to verify against)")
    print(f"  FORMAT    {len(fmt)}   dot/dash only — normalize and they work")
    print(f"  RENAMED   {len(renamed)}   filing under a DIFFERENT ticker — update these")
    print(f"  MISMATCH  {len(mismatch)}   resolves to a DIFFERENT company — danger")
    print(f"  DEAD      {len(dead)}   not found by ticker or name — prune")

    if fmt:
        print(f"\n{'='*74}\n  FORMAT\n{'='*74}")
        for t,u2,title in fmt: print(f"  {t:8} -> {u2:8} {title[:44]}")
    if renamed:
        print(f"\n{'='*74}\n  RENAMED — RECOVERABLE, update the ticker\n{'='*74}")
        print(f"  {'old':8} {'new':8} company")
        for t,name,newt,cik in renamed: print(f"  {t:8} {newt:8} {name[:44]}")
    if mismatch:
        print(f"\n{'='*74}\n  MISMATCH — would attach the WRONG company\n{'='*74}")
        for t,ours,theirs,cik in mismatch: print(f"  {t:8} ours={ours[:26]:26} SEC={theirs[:30]}")
    if dead:
        print(f"\n{'='*74}\n  DEAD — prune\n{'='*74}")
        show = dead if args.verbose else dead[:30]
        for t,name in show: print(f"  {t:8} {name[:50]}")
        if len(dead)>len(show): print(f"  ... and {len(dead)-len(show)} more (--verbose)")
    print()
    return 0
sys.exit(main())
