#!/usr/bin/env python3
"""v1.3.0 addendum — H.3 must not use a baseline H.1 refused.
   Run AFTER patch_v130_industry.py.   python3 patch_v130_h3.py [--apply]"""
import shutil, sys, tempfile, py_compile
from pathlib import Path

P = Path("scoring_engine.py"); src = P.read_text()
if "# HI-PATCH:industry-calibration:v130" not in src:
    print("run patch_v130_industry.py first"); sys.exit(1)
if "if rpe and _med_ok:" in src:
    print("already applied"); sys.exit(0)

OLD = ("    if rpe:\n"
       "        # Lower revenue-per-employee = more humans in the loop = more human decisions\n"
       "        rpe_ratio = industry_median / max(rpe, 1)")
NEW = ("    # v1.3.0: no credible industry baseline -> H.3 skips the RPE term entirely,\n"
       "    # rather than deriving a 'human decision depth' from a fictional peer group.\n"
       "    if rpe and _med_ok:\n"
       "        # Lower revenue-per-employee = more humans in the loop = more human decisions\n"
       "        rpe_ratio = industry_median / max(rpe, 1)")

if src.count(OLD) != 1:
    print(f"ABORTED — matched {src.count(OLD)}x, expected 1"); sys.exit(1)
out = src.replace(OLD, NEW, 1)

if "--apply" not in sys.argv:
    print("DRY RUN — 1 edit would apply. Re-run with --apply"); sys.exit(0)

shutil.copy2(P, str(P) + ".bak2"); P.write_text(out)
try:
    py_compile.compile(str(P), doraise=True, cfile=tempfile.mktemp(suffix=".pyc"))
except Exception as e:
    shutil.copy2(str(P) + ".bak2", P); print(f"compile FAILED, rolled back: {e}"); sys.exit(1)
print("APPLIED. backup: scoring_engine.py.bak2")
