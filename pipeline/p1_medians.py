import shutil, sys, tempfile, py_compile
from pathlib import Path
P = Path("scoring_engine.py"); src = P.read_text()
M = "# HI-PATCH:industry-calibration:v130"
if M in src: print("already applied"); sys.exit(0)

OLDTAB = '''INDUSTRY_RPE_MEDIANS = {
    "tech": 500000, "retail": 200000, "finance": 600000,
    "healthcare": 250000, "energy": 1500000, "manufacturing": 300000,
    "food": 150000, "media": 400000, "telecom": 500000,
    "defense": 350000, "auto": 300000, "default": 350000,
}'''

NEWTAB = M + '''
# Calibrated from the scored universe (n=633 with RPE), Sept 2026. The median
# company in each industry scores 65 by construction. Previous values were
# invented and off by up to 2.9x, which flagged 39 companies as humanwashing in
# error (KO, CPB, SYY, BMY...). See FINDING-industry-rpe-miscalibration.md
INDUSTRY_RPE_MEDIANS = {
    "tech": 380265, "finance": 1125674, "energy": 1174206,
    "healthcare": 405636, "retail": 342863, "manufacturing": 374602,
    "food": 429906, "hospitality": 251909, "transportation": 213536,
    "materials": 463524, "apparel": 447389,
    # n < 10 - provisional, revisit as coverage grows
    "telecom": 920304, "auto": 298165, "mining": 609479,
    "construction": 672929, "media": 262376, "realestate": 206123,
    "services": 699491,
    # No "default" key on purpose: an unknown industry has no credible peer
    # baseline, so H.1 returns no-data rather than dividing by a fiction.
}'''

SIC = '''    # v1.3.0: heavy industry. 77 companies were falling through to "default"
    # and scored against a fictional 350,000 baseline. Mapped from SEC's own
    # sic_description, not from guessing at two-digit codes.
    "10": "mining", "14": "mining",
    "33": "materials", "26": "materials", "32": "materials", "24": "materials",
    "34": "manufacturing", "39": "manufacturing", "22": "manufacturing", "25": "manufacturing",
    "15": "construction", "16": "construction", "17": "construction",
    "65": "realestate", "75": "transportation", "46": "energy", "01": "food",
    # (end v1.7.1)'''

E = [("import math", "import json, os, sys", "import json, math, os, sys"),
     ("RPE medians", OLDTAB, NEWTAB),
     ("SIC map +77", "    # (end v1.7.1)", SIC),
     ("unknown -> None",
      '    return SIC_TO_INDUSTRY.get(str(sic_code)[:2], "default")',
      '    # v1.3.0: None, not "default" - an unmapped SIC is unknown, not a category.\n'
      '    return SIC_TO_INDUSTRY.get(str(sic_code)[:2])')]

out, bad = src, []
for lbl, o, n in E:
    if out.count(o) != 1: bad.append(f"  {lbl}: found {out.count(o)}x, expected 1")
    else: out = out.replace(o, n, 1); print(f"  ok  {lbl}")
if bad: print("ABORTED - source does not match:\n" + "\n".join(bad)); sys.exit(1)
if "--apply" not in sys.argv: print("\nDRY RUN - 4 edits. Re-run with --apply"); sys.exit(0)
shutil.copy2(P, str(P) + ".bak"); P.write_text(out)
try: py_compile.compile(str(P), doraise=True, cfile=tempfile.mktemp(suffix=".pyc"))
except Exception as e:
    shutil.copy2(str(P) + ".bak", P); print(f"compile FAILED, rolled back: {e}"); sys.exit(1)
print("\nAPPLIED 1/3. backup: scoring_engine.py.bak")
