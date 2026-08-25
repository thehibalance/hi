#!/usr/bin/env python3
"""HI Grade — Validated Index Expansion.

Adds an index's constituents to universe_tickers.py, but ONLY tickers that:
  1. resolve in SEC's ticker index (cached via sec_index.py)
  2. have a SEC company name matching the index's company name
Everything else is REJECTED with a reason and never enters the universe.
A ticker that does not resolve scores nothing; a name mismatch means the ticker
was REASSIGNED and scoring it publishes one company's filings under another's name.

  python3 add_index.py --index sp400            # dry run
  python3 add_index.py --index sp400 --apply    # write
"""
import argparse, re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

UA = "Mozilla/5.0 (compatible; HI-Pipeline/1.0; +https://thehibalance.org)"
INDEXES = {
    "sp400": ("https://en.wikipedia.org/wiki/List_of_S%26P_400_companies", "SP400_MIDCAP"),
    "sp600": ("https://en.wikipedia.org/wiki/List_of_S%26P_600_companies", "SP600_SMALLCAP"),
}
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{0,4}([.\-][A-Z])?$")

class Tables(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self._t=None; self._r=None; self._c=None; self._d=0
    def handle_starttag(self, tag, attrs):
        if tag=="table":
            self._d+=1
            if self._d==1: self._t=[]
        elif tag=="tr" and self._t is not None: self._r=[]
        elif tag in ("td","th") and self._r is not None: self._c=[]
    def handle_endtag(self, tag):
        if tag=="table":
            if self._d==1 and self._t is not None: self.tables.append(self._t); self._t=None
            self._d=max(0,self._d-1)
        elif tag=="tr" and self._r is not None:
            if self._r: self._t.append(self._r)
            self._r=None
        elif tag in ("td","th") and self._c is not None:
            self._r.append(" ".join("".join(self._c).split())); self._c=None
    def handle_data(self, data):
        if self._c is not None: self._c.append(data)

def fetch_tables(url):
    with urlopen(Request(url, headers={"User-Agent": UA}), timeout=45) as r:
        html = r.read().decode("utf-8", errors="replace")
    p = Tables(); p.feed(html)
    return p.tables

def extract_pairs(tables):
    """Pick the CONSTITUENTS table by its HEADERS, not by size.

    Wikipedia index pages carry a second, often LARGER table of historical
    additions/removals with Date and Reason columns. Picking the biggest table
    grabs that one, and the longest-text column is then "Reason" rather than a
    company name — which is what produced 189 bogus name mismatches.
    """
    SYM  = ("symbol", "ticker")
    NAME = ("security", "company", "name")
    BAD  = ("reason", "date", "added", "removed")
    best = None
    for t in tables:
        if len(t) < 50: continue
        hdr = [c.strip().lower() for c in t[0]]
        if any(any(b in h for b in BAD) for h in hdr): continue
        si = next((k for k,h in enumerate(hdr) if any(x in h for x in SYM)), None)
        ni = next((k for k,h in enumerate(hdr) if any(x in h for x in NAME)), None)
        if si is None or ni is None: continue
        if best is None or len(t) > len(best[0]): best = (t, si, ni)
    if best is None:
        return [], "no table with Symbol + Security headers found"
    rows, si, ni = best
    pairs = []
    for r in rows[1:]:
        if len(r) <= max(si, ni): continue
        tk = r[si].strip().upper()
        if not TICKER_RE.match(tk): continue
        pairs.append((tk, r[ni].strip()))
    return pairs, None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--index", default="sp400", choices=sorted(INDEXES))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--show-rejects", action="store_true")
    a=ap.parse_args()
    url, listname = INDEXES[a.index]
    print(f"HI Grade — Validated Index Expansion: {a.index.upper()}\nsource: {url}\n")
    try: import sec_index
    except ImportError: print("  sec_index.py not found — run from ~/Desktop/repo/pipeline"); return 1
    pairs, err = extract_pairs(fetch_tables(url))
    if err: print(f"  could not parse constituents: {err}"); return 1
    print(f"  constituents found: {len(pairs)}")
    sec_index.load_sec_index()
    try:
        import universe_tickers as u
        existing={str(t).strip().upper() for t in list(getattr(u,"SP500",[]))
                  +list(getattr(u,"RUSSELL_1000_ADDITIONS",[]))+list(getattr(u,listname,[]))}
    except Exception: existing=set()
    print(f"  already in universe: {len(existing)}\n")
    accept=[]; rej_un=[]; rej_nm=[]; already=[]
    for t,name in pairs:
        if t in existing: already.append(t); continue
        if not sec_index.get_title(t): rej_un.append((t,name)); continue
        ok, sec_title = sec_index.verify(t, name)
        if not ok: rej_nm.append((t,name,sec_title)); continue
        accept.append((t,name))
    print("="*74); print("  VALIDATION"); print("="*74)
    print(f"  ACCEPT          {len(accept):>4}   resolve in SEC and the name matches")
    print(f"  already present {len(already):>4}")
    print(f"  REJECT (no SEC) {len(rej_un):>4}   not an SEC filer under this ticker")
    print(f"  REJECT (name)   {len(rej_nm):>4}   ticker resolves to a DIFFERENT company")
    if rej_nm:
        print(f"\n{'='*74}\n  NAME MISMATCHES — would publish the wrong company\n{'='*74}")
        for t,ours,theirs in rej_nm:
            print(f"  {t:8} index says {ours[:26]:26} SEC says {str(theirs)[:28]}")
    if rej_un:
        if a.show_rejects:
            print(f"\n{'='*74}\n  UNRESOLVED\n{'='*74}")
            for t,name in rej_un: print(f"  {t:8} {name[:50]}")
        else: print(f"\n  ({len(rej_un)} unresolved — --show-rejects to list)")
    if not a.apply:
        print(f"\n{'='*74}\n  DRY RUN — would add {len(accept)} validated tickers to {listname}"
              f"\n  re-run with --apply to write\n{'='*74}\n"); return 0
    if not accept: print("\n  nothing to add"); return 0
    p=Path("universe_tickers.py"); src=p.read_text()
    marker=f"# HI-PATCH:index-{a.index}:v1"
    if marker in src: print(f"\n  {listname} already added"); return 0
    import shutil, py_compile
    shutil.copy2(p, str(p)+".bak")
    block=[f"\n\n{marker}",
           f"# {len(accept)} constituents, each verified against SEC's ticker index at import",
           f"{listname} = ["]
    line="    "
    for t,_ in sorted(accept):
        piece=f'"{t}",'
        if len(line)+len(piece)>92: block.append(line.rstrip()); line="    "
        line+=piece
    if line.strip(): block.append(line.rstrip())
    block.append("]")
    src += "\n".join(block)+"\n"
    old="for t in SP500 + RUSSELL_1000_ADDITIONS:"
    wired = old in src
    if wired: src = src.replace(old, f"for t in SP500 + RUSSELL_1000_ADDITIONS + {listname}:", 1)
    p.write_text(src)
    try: py_compile.compile(str(p), doraise=True, cfile="/tmp/_ut2.pyc")
    except Exception as e:
        shutil.copy2(str(p)+".bak", p); print(f"\n  compile FAILED, rolled back: {e}"); return 1
    print(f"\n{'='*74}\n  ADDED {len(accept)} validated tickers as {listname}")
    print(f"  get_all_tickers() union updated: {wired}")
    if not wired: print(f"  !! add {listname} to the union in get_all_tickers() by hand")
    print(f"  backup: universe_tickers.py.bak")
    print(f"\n  next:  python3 regen_sp500_companies.py\n         python3 ticker_audit.py\n{'='*74}\n")
    return 0
sys.exit(main())
