#!/usr/bin/env python3
"""Is every source endpoint still an API? From pipeline/:

    python3 probe_source_health.py                  # probe, compare to baseline, report
    python3 probe_source_health.py --baseline       # accept the current state as the baseline
    python3 probe_source_health.py --json           # machine-readable only

WHY

Measured 2026-11-16, from the Nov 15 nightly's own log:

    1080 USPTO error        Expecting value: line 1 column 1 (char 0)
    1080 OSHA error         Expecting value: line 1 column 1 (char 0)
    1080 DOL error          Expecting value: line 1 column 1 (char 0)
       0 FDA error

Three sources failed for **every company processed**, for an unknown number of nights, and the
pipeline exited green each time. Probing the endpoints directly:

    200  text/html   9,768 B   enforcedata.dol.gov/api/osha_inspection    <- a Drupal page
    200  text/html   9,768 B   enforcedata.dol.gov/api/whd_whisard        <- the SAME page
    200  text/html  12,258 B   developer.uspto.gov/ibd-api/v1/...         <- an Angular shell
    200  application/json      api.fda.gov/drug/enforcement.json          <- the control

**All three are retired, and all three answer 200.** So `if r.status_code != 200` — the only
check the collectors make — passes. A failure recorded as a favourable fact, at the HTTP layer.

It went unnoticed because `osha`, `dol` and `patents` are all inert downstream: two have no
entry in the `ext` loader and the third's adjustment defaults to the additive identity. *A
source can die completely and nothing notices, because its output was never used.*

WHY CONTENT TYPE AND NOT STATUS CODE

This probe sends a bare request with no query parameters, which a healthy API may well reject.
That is fine, because the classification is on what it speaks, not whether it liked the
question:

    400 + application/json   alive. It parsed the request and complained in its own language.
    200 + text/html          dead. The path is gone and a web server is answering instead.

So the probe needs to know nothing about any API's parameters, and it keeps working when they
change.

WHY IT COMPARES TO A BASELINE

Three sources are already dead. A probe that failed the build on any dead source would fail
every night from now until they are rewritten, and a check that is always red is a check nobody
reads. So:

    a source that was healthy and is now HTML   -> FAIL, exit 1   (a regression)
    a source that was already dead              -> WARN, exit 0   (a known debt, counted)
    a source that was dead and now speaks JSON  -> reported as RECOVERED, update the baseline

**Assert the regression, not the invariant.** A check that fires on a pre-existing condition
blames the change in front of it.

WHERE THE URL LIST COMES FROM

Not from this file. It is read out of `extended_pipelines.py` by `ast` at run time —
module-level constants plus any URL literal passed to a request call. *Ask at run time, never
record the answer*: a hardcoded list here would be a second place for the truth to live, and
the one that goes stale silently.

It writes `data/audit/source_health_<date>.json` unconditionally, so a night in which nothing
changed is distinguishable from a night in which nothing worked.

Changes nothing but that manifest. Makes one request per endpoint, never per company.
"""
import argparse
import ast
import datetime as dt
import json
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("  requests is not installed")

ap = argparse.ArgumentParser()
ap.add_argument("--baseline", action="store_true", help="accept current state as the baseline")
ap.add_argument("--json", action="store_true", help="print only the manifest")
ap.add_argument("--timeout", type=float, default=20.0)
ap.add_argument("--force", action="store_true",
                help="with --baseline: accept a baseline even if endpoints are unreachable")
ap.add_argument("--source", default="extended_pipelines.py")
args = ap.parse_args()

SRC = Path(args.source)
AUDIT = Path("data/audit")
BASELINE = AUDIT / "source_health_baseline.json"
if not SRC.exists():
    raise SystemExit(f"  {SRC} not found — run from pipeline/")


# ── harvest the URLs from the code, not from a list in here ──────────────────────────
def harvest(path):
    """Every http(s) URL literal in the module, with the name or function it belongs to."""
    src = path.read_text()
    tree = ast.parse(src)
    found = {}                                   # url -> label

    def add(url, label):
        url = url.split("?")[0].rstrip("/")
        if url.startswith("http") and url not in found:
            found[url] = label

    # module-level constants: NAME = "https://..."
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    add(node.value.value, t.id)

    # URL literals inside functions, attributed to the enclosing function
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                add(node.value, fn.name)
            # f-strings: take the literal prefix, which is enough to reach the host
            if isinstance(node, ast.JoinedStr):
                lead = ""
                for v in node.values:
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        lead += v.value
                    else:
                        break
                if lead.startswith("http") and lead.count("/") >= 3:
                    add(lead, fn.name)
    return found


urls = harvest(SRC)
if not urls:
    raise SystemExit(f"  no URLs found in {SRC} — has it moved?")


# ── probe ────────────────────────────────────────────────────────────────────────────
def classify(r):
    ct = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
    body = r.content or b""
    looks_json = False
    try:
        json.loads(body.decode("utf-8", "replace"))
        looks_json = True
    except Exception:                                           # noqa: BLE001
        pass
    if looks_json or "json" in ct:
        # Alive, whatever it thinks of a bare request. A 400 in JSON is a conversation.
        return ("ok_json", ct)
    if r.status_code == 200 and ("html" in ct or body[:120].lstrip().lower()
                                 .startswith((b"<!doctype", b"<html"))):
        # THE SILENT KILLER: every status check the collectors make passes on this.
        return ("html_200", ct)
    if r.status_code >= 400:
        return (f"http_{r.status_code}", ct)
    return ("not_json", ct)


rows = []
for url, label in sorted(urls.items(), key=lambda kv: kv[1]):
    rec = {"source": label, "url": url}
    try:
        r = requests.get(url, timeout=args.timeout,
                         headers={"User-Agent": "hi-grade source-health-probe"})
        state, ct = classify(r)
        rec.update(state=state, http=r.status_code, content_type=ct,
                   bytes=len(r.content or b""))
    except Exception as e:                                      # noqa: BLE001
        rec.update(state="transport_error", http=None,
                   content_type=None, bytes=0, error=f"{type(e).__name__}: {e}"[:160])
    rows.append(rec)

HEALTHY = {"ok_json"}
manifest = {
    "probed_at": dt.datetime.now().isoformat(),
    "source_file": str(SRC),
    "counts": {},
    "endpoints": rows,
}
for rec in rows:
    manifest["counts"][rec["state"]] = manifest["counts"].get(rec["state"], 0) + 1

# ── compare to the baseline: report the regression, not the state ────────────────────
base = {}
if BASELINE.exists():
    try:
        base = {e["url"]: e["state"] for e in json.load(open(BASELINE)).get("endpoints", [])}
    except Exception:                                           # noqa: BLE001
        base = {}

regressed, recovered, known_bad, new = [], [], [], []
for rec in rows:
    was, now = base.get(rec["url"]), rec["state"]
    if was is None:
        new.append(rec)
    elif was in HEALTHY and now not in HEALTHY:
        regressed.append((rec, was))
    elif was not in HEALTHY and now in HEALTHY:
        recovered.append((rec, was))
    elif now not in HEALTHY:
        known_bad.append(rec)
manifest["regressed"] = [r["url"] for r, _ in regressed]
manifest["recovered"] = [r["url"] for r, _ in recovered]
manifest["known_bad"] = [r["url"] for r in known_bad]
manifest["baseline"] = str(BASELINE) if base else None

AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / f"source_health_{dt.date.today()}.json"
out.write_text(json.dumps(manifest, indent=2))

if args.json:
    print(json.dumps(manifest, indent=2))
    sys.exit(1 if regressed else 0)

# ── report ───────────────────────────────────────────────────────────────────────────
print(f"SOURCE HEALTH — {len(rows)} endpoints harvested from {SRC}\n")
print(f"   {'state':16} {'http':>5} {'bytes':>8}  {'content-type':26} source")
print("   " + "-" * 92)
for rec in rows:
    mark = " " if rec["state"] in HEALTHY else "!"
    print(f" {mark} {rec['state']:16} {str(rec['http'] or '-'):>5} {rec['bytes']:>8}  "
          f"{(rec['content_type'] or '-'):26} {rec['source']}")
    if rec["state"] == "html_200":
        print(f"      ^ 200 with HTML. `if r.status_code != 200` PASSES on this.")
    if rec.get("error"):
        print(f"      {rec['error']}")
print()
for state, n in sorted(manifest["counts"].items(), key=lambda kv: -kv[1]):
    print(f"   {n:>3}  {state}")

if args.baseline:
    # A baseline is the floor every future run is judged against, so a baseline captured
    # while the network is down records "everything is broken" as acceptable and the probe
    # can never fail again. A guard that disables itself is worse than no guard: refuse.
    down = [r for r in rows if r["state"] == "transport_error"]
    if down and not args.force:
        print(f"\n\nNO BASELINE WRITTEN — {len(down)} endpoint(s) are unreachable.\n")
        for r in down[:8]:
            print(f"   {r['source']:18} {r.get('error', '')[:70]}")
        print("\n   A transport error is this machine's problem, not the source's. Baselining")
        print("   it would accept 'broken' as the floor and silence every future regression.")
        print("   Fix the connection and re-run, or pass --force if these really are gone.")
        sys.exit(1)
    _dead = sum(n for st, n in manifest["counts"].items() if st not in HEALTHY)
    BASELINE.write_text(json.dumps(manifest, indent=2))
    print(f"\n\nBASELINE WRITTEN — {BASELINE}\n")
    print("   The current state is now the accepted state. From here the probe reports")
    print("   CHANGE, not condition: a source that was speaking JSON and now serves HTML")
    print(f"   fails the run. The {_dead}"
          f" known-dead endpoint(s) are recorded as debt, not as a nightly failure.")
    print(f"\n   manifest {out}")
    sys.exit(0)

print("\n\nCHANGE SINCE THE BASELINE\n")
if not base:
    print("   No baseline exists yet. Nothing can be called a regression, because there is")
    print("   no prior state to regress from — which is the honest answer, not a pass.")
    print("   Re-run with --baseline to accept today's state, then this section becomes a test.")
    print(f"\n   manifest {out}")
    sys.exit(0)

for rec, was in regressed:
    print(f"   FAIL  {rec['source']}: {was} -> {rec['state']}")
    print(f"         {rec['url']}")
for rec, was in recovered:
    print(f"   ok    RECOVERED  {rec['source']}: {was} -> {rec['state']}")
    print(f"         Update the baseline so this becomes the new floor.")
for rec in known_bad:
    print(f"   warn  known dead  {rec['source']:18} {rec['state']}   {rec['url']}")
for rec in new:
    print(f"   note  not in baseline  {rec['source']:14} {rec['state']}   {rec['url']}")
if not (regressed or recovered or known_bad or new):
    print("   Every endpoint matches the baseline.")

print(f"\n   manifest {out}")
print(f"""
   {len(regressed)} regression(s) · {len(recovered)} recovery(ies) · """
      f"""{len(known_bad)} known dead · {len(new)} unbaselined""")
if regressed:
    print("\n   A source stopped speaking JSON since the baseline. That is a live defect, not")
    print("   debt: whatever it feeds is now inheriting yesterday's values with no record,")
    print("   exactly as osha, dol and patents did for days without anyone noticing.")
sys.exit(1 if regressed else 0)
