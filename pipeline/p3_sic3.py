import shutil, sys, tempfile, py_compile
from pathlib import Path
P = Path("scoring_engine.py"); src = P.read_text()
if "SIC3_TO_INDUSTRY" in src: print("already applied"); sys.exit(0)
if "HI-PATCH:industry-calibration:v130" not in src:
    print("v1.3.0 not applied - wrong file?"); sys.exit(1)

SIC3 = '''# HI-PATCH:sic3:v131
# Two-digit SIC is too coarse in two places, and both were costing real accuracy.
#
# SIC 28 is chemicals AND pharma AND consumer products. Mapped whole to
# "healthcare", it scored 16 industrial-chemical companies (DOW, DD, CF, MOS,
# IFF) against a pharma baseline 2-4x too low. Measured: 283 pharma 348,774 /
# 284 soap+cosmetics 373,397 / industrial chemicals 955,571.
#
# SIC 67 lumped 53 REITs in with banks. REITs run ~2.8x the bank median
# revenue-per-employee, and 28 of the 53 were floor-capped at composite 50
# as a direct result. Near-zero headcount is the REIT business model, not a
# humanity signal.
SIC3_TO_INDUSTRY = {
    "283": "healthcare",   # pharmaceutical preparations
    "284": "consumer",     # soap, detergents, cosmetics
    "280": "chemicals", "281": "chemicals", "282": "chemicals",
    "285": "chemicals", "286": "chemicals", "287": "chemicals", "289": "chemicals",
    "679": "reit",         # real estate investment trusts
}

SIC_TO_INDUSTRY = {'''

E = [("SIC3 table", "SIC_TO_INDUSTRY = {", SIC3),
     ("3-digit lookup first",
      '    # v1.3.0: None, not "default" - an unmapped SIC is unknown, not a category.\n'
      '    return SIC_TO_INDUSTRY.get(str(sic_code)[:2])',
      '    # v1.3.1: 3-digit first, then 2-digit. None if neither - an unmapped SIC\n'
      '    # is unknown, not a category.\n'
      '    s = str(sic_code)\n'
      '    return SIC3_TO_INDUSTRY.get(s[:3]) or SIC_TO_INDUSTRY.get(s[:2])')]

out, bad = src, []
for lbl, o, n in E:
    if out.count(o) != 1: bad.append(f"  {lbl}: found {out.count(o)}x, expected 1")
    else: out = out.replace(o, n, 1); print(f"  ok  {lbl}")
if bad: print("ABORTED:\n" + "\n".join(bad)); sys.exit(1)
if "--apply" not in sys.argv: print("\nDRY RUN - 2 edits. Re-run with --apply"); sys.exit(0)
shutil.copy2(P, str(P) + ".bak3"); P.write_text(out)
try: py_compile.compile(str(P), doraise=True, cfile=tempfile.mktemp(suffix=".pyc"))
except Exception as e:
    shutil.copy2(str(P) + ".bak3", P); print(f"compile FAILED, rolled back: {e}"); sys.exit(1)
print("\nAPPLIED. backup: scoring_engine.py.bak3")
print("next: recalibrate medians - chemicals/consumer/reit have no entry yet")
