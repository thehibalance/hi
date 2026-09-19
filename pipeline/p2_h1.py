import shutil, sys, tempfile, py_compile
from pathlib import Path
P = Path("scoring_engine.py"); src = P.read_text()
if "# HI-PATCH:industry-calibration:v130" not in src:
    print("run p1_medians.py --apply first"); sys.exit(1)
if "def _rpe_score(" in src: print("already applied"); sys.exit(0)

HELPER = '''def _rpe_score(industry_median, rpe):
    """H.1 revenue-per-employee.  v1.3.0

    Each doubling of employees per dollar of revenue, relative to the industry
    median, is worth +15 points. The median company scores 65.

    Replaces (median/rpe)*65, which clamped at 100 for anything below 0.65x the
    median and so pinned 168 companies (15%) at the ceiling, unable to tell a
    company at half its industry median from one at a tenth.
    """
    if not rpe or rpe <= 0 or not industry_median:
        return 50
    return round(clamp(65 + 15 * math.log2(industry_median / rpe)), 1)


def clamp(v, lo=0, hi=100):'''

LOOKUP = ('    industry_median = INDUSTRY_RPE_MEDIANS.get(industry)\n'
          '    _med_ok = industry_median is not None\n'
          '    if not _med_ok:\n'
          '        industry_median = 350000  # legacy value, retained only for rpe_ratio below')

HW_OLD = ('    industry_rpe_median = INDUSTRY_RPE_MEDIANS.get(industry, INDUSTRY_RPE_MEDIANS["default"])\n'
          '    if rpe and rpe > industry_rpe_median * 4:')
HW_NEW = ('    industry_rpe_median = INDUSTRY_RPE_MEDIANS.get(industry)\n'
          '    # v1.3.0: no baseline -> no accusation. Never flag on a guessed median.\n'
          '    if rpe and industry_rpe_median and rpe > industry_rpe_median * 4:')

E = [("H.1 helper", "def clamp(v, lo=0, hi=100):", HELPER),
     ("median lookup",
      '    industry_median = INDUSTRY_RPE_MEDIANS.get(industry, INDUSTRY_RPE_MEDIANS["default"])',
      LOOKUP),
     ("H.1 blended path",
      '        rpe_score = clamp((industry_median / rpe) * 65) if rpe > 0 else 50',
      '        rpe_score = _rpe_score(industry_median, rpe) if _med_ok else 50'),
     ("H.1 sole path",
      '        scores["H.1"] = clamp((industry_median / rpe) * 65) if rpe > 0 else 50',
      '        scores["H.1"] = _rpe_score(industry_median, rpe) if _med_ok else 50'),
     ("HW.1 guard", HW_OLD, HW_NEW)]

out, bad = src, []
for lbl, o, n in E:
    if out.count(o) != 1: bad.append(f"  {lbl}: found {out.count(o)}x, expected 1")
    else: out = out.replace(o, n, 1); print(f"  ok  {lbl}")
if bad: print("ABORTED - source does not match:\n" + "\n".join(bad)); sys.exit(1)
if "--apply" not in sys.argv: print("\nDRY RUN - 5 edits. Re-run with --apply"); sys.exit(0)
shutil.copy2(P, str(P) + ".bak1"); P.write_text(out)
try: py_compile.compile(str(P), doraise=True, cfile=tempfile.mktemp(suffix=".pyc"))
except Exception as e:
    shutil.copy2(str(P) + ".bak1", P); print(f"compile FAILED, rolled back: {e}"); sys.exit(1)
print("\nAPPLIED 2/3. backup: scoring_engine.py.bak1")
