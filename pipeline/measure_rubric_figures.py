#!/usr/bin/env python3
"""Every coverage and correlation figure RUBRIC.md publishes, re-measured against today's
scores. Read-only. From pipeline/:

    python3 measure_rubric_figures.py

WHY

RUBRIC.md carries a "Coverage (Oct 2026)" line under each sub-signal. Three of them are
provably stale, and one of the three describes a defect that was fixed five days ago:

    H.3: "**16% sit at exactly 100** — the linear form saturates."

v1.13.0 recentred H.3 on a log2 ratio. The form is not linear any more and the saturation
that sentence reports is gone. A reader who checks the rubric against the data finds the
rubric wrong about its own engine — which is worse than a rubric that says nothing, because
it was written to be checked.

The figures were last measured by hand, by pasting one-off `python3 -c` lines into a shell
and reading the numbers off. That is how they went stale: nothing re-runs. This is the
instrument, so the next release re-measures instead of re-deriving.

WHAT IT DOES

Three passes, each independently checkable:

  1. DISCOVER   — reads the score rows and reports what fields actually carry the
                  derived/withheld markers and the published coverage, rather than
                  assuming field names. A figure computed from a guessed field is a
                  figure nobody can defend.
  2. MEASURE    — per sub-signal: n measured, withheld, mean, median, max, share at
                  exactly 100. Then every pairwise correlation among the H sub-signals,
                  Spearman and Pearson, with the n each was computed over. Then the
                  coverage distribution, its median, the zero-coverage count, and the
                  composition of the modal coverage bucket.
  3. COMPARE    — greps RUBRIC.md for its own "Coverage" lines, extracts the numbers it
                  claims, and prints claim against measurement with a verdict. An anchor
                  that does not match prints **PATTERN DID NOT MATCH** rather than
                  passing silently: the gate's own lesson from v1.13.1, where an
                  unmatched pattern returned a clean `?`.

The claim lines are printed verbatim, with line numbers, so the text patch that follows
can anchor on them exactly instead of on a remembered paraphrase.

Spearman is computed here rather than imported: scipy is not a pipeline dependency and
adding one for three numbers would make the rubric's figures depend on an install.

Changes nothing.
"""
import json
import re
import statistics as st
from collections import Counter
from pathlib import Path

SCORES = Path("data/scores/all_scores.json")
if not SCORES.exists():
    raise SystemExit(f"  missing {SCORES} — run from pipeline/")

RUBRIC = next((p for p in (Path("RUBRIC.md"), Path("../RUBRIC.md")) if p.exists()), None)

rows = json.load(open(SCORES))
engine = [r for r in rows if r.get("spec_version")]
seed = [r for r in rows if not r.get("spec_version")]

print(f"{len(rows)} rows · {len(engine)} engine-scored · {len(seed)} seed")
print(f"spec_version: {dict(Counter(r.get('spec_version') for r in rows))}\n")


# ── 1. DISCOVER ───────────────────────────────────────────────────────────────
def walk(obj, path="", depth=0, out=None):
    """Every key whose name mentions 'derived', 'coverage' or 'count', with its path."""
    if out is None:
        out = {}
    if depth > 4 or not isinstance(obj, dict):
        return out
    for k, v in obj.items():
        p = f"{path}/{k}".lstrip("/")
        if re.search(r"derived|coverage|real_count|count", k, re.I):
            out[p] = v
        if isinstance(v, dict):
            walk(v, p, depth + 1, out)
    return out


print("1. DISCOVER — what the rows actually carry\n")
probe = engine[0] if engine else {}
found = walk(probe)
if not found:
    print("   !! no field matching derived/coverage/count found on the first engine row.")
    print(f"      top-level keys: {sorted(probe)[:20]}")
else:
    for p, v in sorted(found.items()):
        s = json.dumps(v)
        print(f"   {p:46} {type(v).__name__:6} {s[:60]}")
print(f"\n   row keys: {', '.join(sorted(probe))}")

GEN = probe.get("genome") or {}
DIMS = sorted(GEN)
print(f"   genome dimensions: {DIMS}")
if DIMS:
    print(f"   genome['{DIMS[0]}'] keys: {sorted(GEN[DIMS[0]])}")


def sub_scores(r):
    """{code: value} across every dimension of one row."""
    out = {}
    for dim in (r.get("genome") or {}).values():
        if isinstance(dim, dict):
            for code, val in (dim.get("scores") or {}).items():
                if isinstance(val, (int, float)):
                    out[code] = float(val)
    return out


def derived_codes(r):
    """Every sub-signal code this row marks as derived or absence-derived, from whatever
    field holds it. Union, so a code marked in either place counts as not-measured."""
    marks = set()
    for p, v in walk(r).items():
        # ONLY fields whose name says "derived". `signal_coverage` can be a map of
        # code -> has-data, which means the opposite, and reading it as a derived mark
        # would invert every count in section 2 while still printing plausibly.
        if "derived" not in p.lower():
            continue
        if isinstance(v, list):
            marks |= {x for x in v if isinstance(x, str) and re.fullmatch(r"[A-Z]\.\d", x)}
        elif isinstance(v, dict):
            marks |= {k for k, flag in v.items()
                      if re.fullmatch(r"[A-Z]\.\d", k or "") and flag}
    return marks


CODES = sorted({c for r in engine for c in sub_scores(r)},
               key=lambda c: (c[0], int(c.split(".")[1])))
print(f"\n   sub-signal codes present ({len(CODES)}): {', '.join(CODES)}")

n_marked = sum(1 for r in engine if derived_codes(r))
print(f"   engine rows with at least one derived mark: {n_marked} of {len(engine)}")
if n_marked == 0:
    print("   !! nothing marks a sub-signal as withheld, so 'measured' below collapses to")
    print("      'has a number', which counts every neutral 50 as evidence. Read the field")
    print("      list above before trusting any coverage figure in section 2.")


# ── 2. MEASURE ────────────────────────────────────────────────────────────────
def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def pearson(a, b):
    n = len(a)
    if n < 3:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va <= 0 or vb <= 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (va ** 0.5 * vb ** 0.5)


def spearman(a, b):
    return pearson(ranks(a), ranks(b))


PROXY = n_marked == 0
MEASURED = {}          # code -> {company: value}, measured only
for r in engine:
    name = r.get("company") or r.get("ticker") or ""
    dv = derived_codes(r)
    for code, val in sub_scores(r).items():
        if code in dv:
            continue
        if PROXY and val == 50:
            continue      # the engine's own `v != 50` term, minus the sets we cannot see
        MEASURED.setdefault(code, {})[name] = val

print("\n\n2. MEASURE\n")
if PROXY:
    print("   ARM = NON-NEUTRAL PROXY. No row carries a derived mark, so 'measured' here is")
    print("   `v != 50` — the first half of the engine's own real_count term at")
    print("   scoring_engine.py:1906, WITHOUT the INDUSTRY_DERIVED / ABSENCE_DERIVED")
    print("   exclusions it cannot see. Every count below is therefore an UPPER BOUND on")
    print("   coverage, and a genuinely measured value of exactly 50.0 is counted as")
    print("   withheld. Row-level truth is the published `signal_coverage` string; this")
    print("   table is the only per-sub-signal view the file permits.\n")
else:
    print("   ARM = DERIVED MARKS. The rows carry provenance; these counts are exact.\n")
print(f"   {'code':6} {'measured':>9} {'withheld':>9} {'mean':>7} {'median':>7} "
      f"{'max':>6} {'at 100':>8}")
print("   " + "─" * 62)
for code in CODES:
    vals = list(MEASURED.get(code, {}).values())
    held = len(engine) - len(vals)
    if not vals:
        print(f"   {code:6} {0:>9} {held:>9}       —       —      —        —")
        continue
    at100 = sum(1 for v in vals if v >= 99.95)
    print(f"   {code:6} {len(vals):>9} {held:>9} {st.mean(vals):>7.1f} "
          f"{st.median(vals):>7.1f} {max(vals):>6.1f} "
          f"{100.0 * at100 / len(vals):>7.1f}%")

H_CODES = [c for c in CODES if c.startswith("H.")]
print("\n   CORRELATIONS among the H sub-signals — computed over companies measured on BOTH\n")
print(f"   {'pair':13} {'n':>5} {'Spearman':>9} {'Pearson':>9}")
print("   " + "─" * 40)
for i, a in enumerate(H_CODES):
    for b in H_CODES[i + 1:]:
        shared = sorted(set(MEASURED.get(a, {})) & set(MEASURED.get(b, {})))
        if len(shared) < 3:
            print(f"   {a}×{b:8} {len(shared):>5}         —         —")
            continue
        xa = [MEASURED[a][c] for c in shared]
        xb = [MEASURED[b][c] for c in shared]
        rs, rp = spearman(xa, xb), pearson(xa, xb)
        if rs is None or rp is None:
            # one arm is constant, so no correlation is defined. Say which, rather than
            # printing a dash: a sub-signal with zero variance is itself a finding.
            flat = [c for c, x in ((a, xa), (b, xb)) if len(set(x)) == 1]
            print(f"   {a}×{b:8} {len(shared):>5}   undefined — "
                  f"{' and '.join(flat) or 'degenerate'} is constant")
            continue
        flag = "  <-- one datum counted twice" if rs > 0.9 else ""
        print(f"   {a}×{b:8} {len(shared):>5} {rs:>9.3f} {rp:>9.3f}{flag}")

PUB = re.compile(r"^\s*(\d+)\s*/\s*(\d+)")
cov = Counter()
pairs = Counter()
zero = []
gap = Counter()
for r in engine:
    dv = derived_codes(r)
    have = tuple(sorted(c for c, v in sub_scores(r).items()
                        if c not in dv and not (PROXY and v == 50)))
    cov[len(have)] += 1
    if len(have) == 2:
        pairs[have] += 1
    if not have:
        zero.append(r.get("company") or r.get("ticker") or "?")
    m = PUB.match(str(r.get("signal_coverage") or ""))
    if m:
        gap[len(have) - int(m.group(1))] += 1

print(f"\n   COVERAGE out of {len(CODES)} sub-signals, over {len(engine)} engine rows\n")
print("   " + " ".join(f"{k}:{cov[k]}" for k in sorted(cov)))
per_row = [k for k, n in cov.items() for _ in range(n)]
print(f"\n   median {int(st.median(per_row))}/{len(CODES)} · "
      f"mean {st.mean(per_row):.2f} · max {max(cov)}")
print(f"   zero coverage : {len(zero)} companies "
      f"({100.0 * len(zero) / len(engine):.1f}%)")
le2 = sum(n for k, n in cov.items() if k <= 2)
print(f"   at most 2     : {le2} ({100.0 * le2 / len(engine):.1f}%)")

if gap:
    print("\n   CROSS-CHECK against the engine's published `signal_coverage` per row\n")
    print("   this table's count MINUS the engine's own count, per company:")
    for d in sorted(gap):
        tag = ("agree" if d == 0 else
               f"this table counts {d:+d} — untracked constants off 50" if d > 0 else
               f"this table counts {d:+d} — real measurements landing on exactly 50")
        print(f"      {d:+3d}  {gap[d]:>5} companies   {tag}")
    if set(gap) == {0}:
        print("\n   Exact agreement on every row. The proxy reproduces real_count, so the")
        print("   derived sets currently exclude nothing the `v != 50` term does not already")
        print("   exclude — which is a statement about today's data, not a licence to delete")
        print("   the sets.")
    else:
        off = sum(n for d, n in gap.items() if d != 0)
        print(f"\n   {off} companies disagree. Each one is a sub-signal this table calls")
        print("   evidence and the engine does not, or the reverse. The per-sub-signal")
        print("   counts above are wrong by that much, in the direction shown.")

if pairs:
    print(f"\n   COMPOSITION of the {cov[2]} companies at coverage 2 — WHICH two\n")
    for pair, n in pairs.most_common(8):
        print(f"      {n:>5}  {' + '.join(pair)}")
    top, topn = pairs.most_common(1)[0]
    print(f"\n   {topn} of {len(engine)} companies "
          f"({100.0 * topn / len(engine):.1f}% of the index) have exactly "
          f"{' and '.join(top)}")
    if len(top) == 2 and all(t.startswith("H.") for t in top):
        sh = sorted(set(MEASURED.get(top[0], {})) & set(MEASURED.get(top[1], {})))
        if len(sh) > 2:
            rs = spearman([MEASURED[top[0]][c] for c in sh],
                          [MEASURED[top[1]][c] for c in sh])
            if rs is None:
                print("   and no correlation between those two is defined — one of them has")
                print("   no variance across the companies that carry both.")
            else:
                print(f"   and those two correlate at Spearman {rs:.3f}. For that share of")
                print("   the index the whole evidentiary base is one measurement, twice.")


# ── 3. COMPARE ────────────────────────────────────────────────────────────────
print("\n\n3. COMPARE — what RUBRIC.md claims\n")
if RUBRIC is None:
    print("   !! RUBRIC.md not found from here (tried ./ and ../). Section 2 stands on its")
    print("      own; nothing was compared. Run from pipeline/ inside the repo.")
    raise SystemExit(0)

print(f"   reading {RUBRIC.resolve()}\n")
lines = RUBRIC.read_text().splitlines()

CODE_RE = re.compile(r"\b([A-Z]\.\d)\b")
claims = []
for i, line in enumerate(lines, 1):
    if "overage" not in line or "of" not in line:
        continue
    # nearest preceding heading that names a sub-signal
    owner = None
    for j in range(i - 2, max(i - 40, 0) - 1, -1):
        m = CODE_RE.search(lines[j])
        if m and (lines[j].lstrip().startswith("#") or "**" in lines[j]):
            owner = m.group(1)
            break
    claims.append((i, owner, line))

if not claims:
    print("   !! PATTERN DID NOT MATCH — no line containing 'overage' and 'of' in RUBRIC.md.")
    print("      The coverage lines moved or were reworded. Do not patch on a stale anchor;")
    print("      grep the file and fix this script's pattern first.")
    raise SystemExit(0)

NUM = re.compile(r"\*\*([\d,]+) of ([\d,]+)\*\*")
PCT = re.compile(r"\*\*(\d+)% sit at exactly 100\*\*")
COR = re.compile(r"\*\*(?:Spearman\s+)?(0\.\d+)\*\*(?:\s*\(([\d,]+) companies\))?")
HELD = re.compile(r"\*\*([\d,]+)\*\* recorded as no-measurement")


def num(s):
    return int(s.replace(",", ""))


for ln, owner, line in claims:
    print(f"   line {ln:>4}  [{owner or 'unattributed'}]")
    print(f"      {line.strip()}")
    vals = list(MEASURED.get(owner, {}).values()) if owner else []

    m = NUM.search(line)
    if not m:
        print("      !! PATTERN DID NOT MATCH the 'N of M' anchor on this line.")
    elif not owner:
        print("      !! no sub-signal code found above this line — cannot compare.")
    else:
        c_n, c_d = num(m.group(1)), num(m.group(2))
        verdict = "OK" if c_n == len(vals) else f"STALE  -> {len(vals)}"
        print(f"      coverage  claims {c_n} of {c_d}   measures "
              f"{len(vals)} of {len(engine)}   {verdict}")
        if c_d != len(engine):
            print(f"      denominator claims {c_d}, engine rows are {len(engine)}")

    h = HELD.search(line)
    if h and owner:
        got = len(engine) - len(vals)
        c_h = num(h.group(1))
        print(f"      withheld  claims {c_h}            measures {got}"
              f"   {'OK' if c_h == got else 'STALE'}")

    p = PCT.search(line)
    if p and owner and vals:
        got = 100.0 * sum(1 for v in vals if v >= 99.95) / len(vals)
        print(f"      at 100    claims {p.group(1)}%          measures {got:.1f}%"
              f"   {'OK' if abs(got - int(p.group(1))) < 1 else 'STALE'}")

    for cm in COR.finditer(line):
        claimed = float(cm.group(1))
        cn = num(cm.group(2)) if cm.group(2) else None
        best = None
        for other in H_CODES:
            if other == owner:
                continue
            sh = sorted(set(MEASURED.get(owner, {})) & set(MEASURED.get(other, {})))
            if len(sh) < 3:
                continue
            rs = spearman([MEASURED[owner][c] for c in sh],
                          [MEASURED[other][c] for c in sh])
            if rs is not None and (best is None or abs(rs - claimed) < abs(best[1] - claimed)):
                best = (other, rs, len(sh))
        if best is None:
            print(f"      correlation claims {claimed} — no comparable pair measurable.")
        else:
            o, rs, n_ = best
            tail = f" over {cn}" if cn else ""
            v = "OK" if abs(rs - claimed) < 0.005 and (not cn or cn == n_) else "STALE"
            print(f"      corr      claims {claimed}{tail}    measures {rs:.3f} vs {o} "
                  f"over {n_}   {v}")
    print()

print("""   A STALE verdict above is a sentence in the published rubric that the data
   contradicts today. Each one needs the measurement written in, not the claim
   softened: the figure is the point of the line.

Nothing changed. Read-only.
""")
