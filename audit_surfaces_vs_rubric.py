#!/usr/bin/env python3
"""The public surfaces against the new RUBRIC. Read-only. From the repo root:

    cd ~/Desktop/repo && python3 audit_surfaces_vs_rubric.py

WHY THIS COMES BEFORE A PATCH

RUBRIC.md is now current with the October audit. README, METHODOLOGY and the docs pages
are not, and they are what a POSE reviewer, a data-engineer candidate and every visitor to
thehibalance.org actually read. The RUBRIC is the internal document; these are the claims.

The temptation is to write a patch from memory. That is exactly the mistake avoided on the
RUBRIC itself: several patches have edited these files since anyone last read them in full,
so anchoring on remembered prose is guessing. This reports what they say. The patch comes
after, written against what is actually there.

WHAT IT CHECKS

  1. Which surface files exist — discovered, not assumed.
  2. Every spec-version string in each, against the engine's.
  3. Every sub-signal count claim ("18 active", "19 sub-signals", "21 sources").
  4. Mentions of RETIRED sub-signals, which should appear only as history.
  5. Status words attached to a sub-signal ID that disagree with the RUBRIC's status.
  6. **The eight debunked source claims.** The RUBRIC now carries a correction for each.
     If a surface still makes the original claim, the public statement is wrong while the
     internal document is right — the worse of the two failure modes.
  7. Coverage language: a surface claiming a sub-signal is grounded, measured or verified
     where the RUBRIC's coverage line says it is mostly an industry constant.

WHAT IT CANNOT CHECK

Tone, or whether a sentence is misleading without being false. "Scores every company on 19
signals" is true of the schema and false of the measurement; only a human reading it against
the coverage lines can judge which reading a visitor will take.
"""
import json
import re
from pathlib import Path

ENG = Path("pipeline/scoring_engine.py")
RUB = Path("RUBRIC.md")
if not RUB.exists() or not ENG.exists():
    raise SystemExit("  run from the repo root (~/Desktop/repo) — needs RUBRIC.md and "
                     "pipeline/scoring_engine.py")

rub, eng = RUB.read_text(), ENG.read_text()
em = re.search(r'"spec_version":\s*"([\d.]+)"', eng)
eng_spec = em.group(1) if em else "?"

# ── The RUBRIC's own claims, parsed from it rather than remembered ────────
heads = [(m.group(1), m.start(), m.end())
         for m in re.finditer(r"^### ([A-Z]\.\d)\s*[—-].*$", rub, re.M)]
status, coverage = {}, {}
for i, (ss, s, e) in enumerate(heads):
    nxt = heads[i + 1][1] if i + 1 < len(heads) else len(rub)
    body = rub[e:nxt]
    sm = re.search(r"\*\*Status:\*\*\s*\**\s*(GROUNDED|PARTIAL|UNGROUNDED)", body)
    if sm:
        status[ss] = sm.group(1)
    cm = re.search(r"\*\*Coverage \(Oct 2026\):\*\*\s*(.+)", body)
    if cm:
        coverage[ss] = cm.group(1).strip()

assigned = set(re.findall(r'scores\["([A-Z]\.\d)"\]\s*=', eng))
documented = set(status)
# N.5 is named explicitly because it is no longer documented, so `documented - assigned`
# cannot find it. M.3 is NOT retired — v1.11.0 made it absence-derived where litigation
# is zero, which is a different thing and a distinction three earlier scripts got wrong.
RETIRED = sorted({"N.5"} | (documented - assigned))

# Sub-signals whose coverage line says the constant carries them.
mostly_const = sorted(k for k, c in coverage.items()
                      if re.search(r"industry constant|constant for the remaining|"
                                   r"zero measured|wholly constant", c, re.I))

# ── The eight debunked claims: (label, required terms, what is true) ──────
DEBUNKED = [
    ("QCEW as a revenue source",
     [r"\bQCEW\b"], [r"revenue", r"\bRPE\b", r"revenue.per.employee"],
     "QCEW contains no revenue field. It cannot produce revenue-per-employee."),
    ("SAB 99 as a 5% materiality threshold",
     [r"SAB\s*99"], [r"\b5\s*%", r"five percent", r"materiality threshold"],
     "SAB 99 explicitly REJECTS a bright-line 5% threshold."),
    ("CCPA/GDPR record-count thresholds",
     [r"\bCCPA\b", r"\bGDPR\b"], [r"record count", r"records?\s+threshold",
                                  r"number of records", r"\bthreshold"],
     "Neither defines a record-count threshold."),
    ("CPSC Class I/II/III",
     [r"\bCPSC\b"], [r"Class\s*I\b", r"Class\s*II\b", r"Class\s*III\b"],
     "Class I/II/III is the FDA's scheme. CPSC's Class A/B/C is an internal staff tool, "
     "never published per recall — likely why the CPSC collector yields nothing."),
    ("AlgorithmWatch as a harm-tier dataset",
     [r"AlgorithmWatch"], [r"tier", r"dataset", r"score", r"harm level"],
     "AlgorithmWatch publishes no harm-tier dataset."),
    ("GRI as a disclosure-quality source",
     [r"\bGRI\b"], [r"quality", r"database", r"\bscore"],
     "GRI does not judge disclosure quality, and its database is decommissioned."),
    ("A central EU EPR register",
     [r"\bEPR\b"], [r"registe?r", r"\bEU\b", r"central"],
     "There is no central EU EPR register. Registration is per member state."),
    ("CDP without the licence caveat",
     [r"\bCDP\b"], [r"commercial", r"licen[cs]e", r"terms"],
     "CDP's licence forbids commercial use. Any surface naming CDP as an input should "
     "say so, because it caps A.1, A.2 and N.2 together."),
]

# ── Sources the project cannot use, advertised anyway ─────────────────────
#
# WHY THIS IS A CHECK OF ITS OWN
#
# Bounding the proximity match to one record (see `bounds`) removed six flags. One was a
# true false positive — CDP named in the acknowledgements, where the nearby "licence" was
# the Apache 2.0 heading. The other five were real findings the DEBUNKED check had been
# catching by coincidence:
#
#   METHODOLOGY:353   "Public datasets (HRC, CDP, GRI, etc.) — refreshed quarterly"
#   README:232        "Grounding ... against external frameworks (BLS, SBTi, GRI, B Corp)"
#   docs/index.html:2272  a JS label map, live code ready to render "GRI" to a visitor
#
# None of those claims GRI judges disclosure quality, so the DEBUNKED check was right to
# let them go. What they do is ADVERTISE A SOURCE THAT CANNOT BE USED — a different claim,
# and one that does not depend on two words landing near each other. Relying on proximity
# to find it was luck, and tightening the window spent the luck.
UNUSABLE = {
    "GRI": (r"\bGRI\b",
            "its database is DECOMMISSIONED — nothing can refresh and nothing can be read "
            "from it. A surface listing GRI as an input or a refresh target is promising "
            "data that no longer exists."),
    "CDP": (r"\bCDP\b",
            "its licence FORBIDS COMMERCIAL USE. Naming it as a scoring input is a "
            "liability, not just an inaccuracy, and it caps A.1, A.2 and N.2 together."),
    "B Corp": (r"B\s*Corp\b",
               "B Lab is ELIMINATING the numerical score under V2 standards from 2027, "
               "moving to pass/fail. U.3 and M.5 both read that score today."),
}
# Language that turns a mention into a forward commitment rather than a description.
#
# `target` and `next` were in this list and had to come out. Three of the first six
# PROMISE flags were "SBTi targets" and "SBTi-validated targets" — descriptions of a
# current input, not commitments about a future one. They now fall through to `unusable`,
# which is the correct bin: naming CDP and B Corp as live scoring inputs is the problem,
# not promising them.
#
# A word that appears in the vocabulary of the thing being described cannot be the test
# for whether a sentence is a promise about it.
PROMISE = (r"grounding\b|will\s+be|planned|roadmap|path forward|queued|"
           r"intend|upcoming|in a future|once we")
# ── Report all, exclude only the known-benign. The gate is inverted on purpose. ──
#
# The first version required INPUT VOCABULARY nearby (source|dataset|input|refresh|feed…)
# before flagging an unusable source, on the theory that a bare mention is not a claim.
# It dropped the two sharpest findings in the whole audit:
#
#   README:171            "GRI reporting (34)"  — a per-source company COUNT
#   docs/index.html:848   "product lifecycle (iFixit, B Corp Environment, Fair Trade
#                          traceability) … High scorers: CDP A/A- climate grades"
#
# Both are plainly input claims. Neither uses a word from the list. An allowlist of ways
# to phrase a claim will always miss a phrasing, and the phrasings it misses are not a
# random sample — they are the specific, concrete ones, because a sentence carrying a real
# number says "GRI reporting (34)" and not "GRI is one of our data sources".
#
# Second time in two edits that tightening a classification silently cost findings. So:
# there are only three names here. Flag EVERY mention outside a comment, and exclude only
# the one context that is genuinely not a claim — crediting someone's intellectual work.
# Suppression is then a short, fixed list rather than an open-ended guess, and the counts
# are printed so it is visible rather than inferred.
CREDIT = (r"acknowledg|thanks|thank you|credit|predates ours|informs ours|"
          r"built on methodology|inspired by|with gratitude")

# ── Discover the surfaces ─────────────────────────────────────────────────
cands = []
for pat in ("README*", "METHODOLOGY*", "SOURCES*", "docs/*.md", "docs/*.html",
            "docs/**/*.html", "*.md"):
    cands += [p for p in Path(".").glob(pat) if p.is_file()]
SKIP = {"RUBRIC.md"}
# Backups are copies of the files being audited. Scanning them produced 64 of 204 flags
# on the first run, all duplicates of findings already reported against the live file.
# A backup before a risky edit is good practice, not a stale claim — but it does not
# belong in an audit of what the public reads.
BAK = re.compile(r"\.bak$|\.pre_|\.orig$|~$|\.save$")
seen, surfaces, skipped = set(), [], []
for p in sorted(cands):
    s = str(p)
    if s in seen or p.name in SKIP or p.stat().st_size > 2_000_000:
        continue
    seen.add(s)
    (skipped if BAK.search(p.name) else surfaces).append(p)

print(f"engine spec {eng_spec} · RUBRIC documents {len(status)} sub-signals, "
      f"{len(coverage)} with a coverage line")

# A TOOL THAT CANNOT MEASURE MUST REFUSE TO REPORT.
#
# The second run of this script printed "coverage line says the constant carries it: none"
# while having parsed ZERO coverage lines. That line reads as a finding — no sub-signal is
# carried by a constant, excellent news — and meant the opposite: the ground truth was
# unreadable, so the `overclaim` check silently did not run. Reporting nothing was
# indistinguishable from reporting no problems.
#
# That is the project's oldest bug class: no evidence rendered as favourable evidence. It
# produced the fossil rows and the split identities, and this is its second appearance
# inside the audit tooling. The fix is not a better regex. It is this.
if not status:
    raise SystemExit(
        "  !! parsed 0 sub-signal sections from RUBRIC.md. The audit has no ground truth\n"
        "     and will not run on one it cannot read.\n"
        "       grep -c '^### ' RUBRIC.md        # expect 18\n"
        "       git branch --show-current ; wc -c RUBRIC.md")
if len(coverage) < len(status):
    raise SystemExit(
        f"  !! {len(status)} sub-signal sections but only {len(coverage)} coverage lines.\n"
        f"     The overclaim check reads those lines, so running now would report a clean\n"
        f"     result from an unread document. Refusing.\n"
        f"       grep -c 'Coverage (Oct 2026)' RUBRIC.md   # expect {len(status)}\n"
        f"       git branch --show-current ; wc -c RUBRIC.md\n"
        f"     48,250 chars with 18 matches means this parse is the bug. 23,984 with 0\n"
        f"     means the patched RUBRIC is not the file on disk — check the branch.")

print(f"retired, should appear only as history: {', '.join(RETIRED) or 'none'}")
print(f"coverage line says the constant carries it: "
      f"{', '.join(mostly_const) if mostly_const else 'none of the 18 — all measured enough'}")
print(f"\n{len(surfaces)} surface files found\n")
for p in surfaces:
    print(f"   {str(p):44} {p.stat().st_size:>8,} bytes")
if skipped:
    print(f"\n   not audited — backups of the above: "
          f"{', '.join(p.name for p in skipped)}")
    print("   (git holds the history; these should not be in the tree at all)")

findings = []
tally = {}          # file -> [(source, mentions, flagged, in credits)]


def comment_spans(text):
    """Character ranges of HTML comments and of `//` line comments.

    The first run flagged ~35 version strings that were deliberate history: the stack of
    `<!-- v1.10.4-api-enhance: applied … -->` patch markers at the top of docs/index.html,
    and code comments like `// v1.4.0: actual field is moat_level` that record when a line
    changed. Both are the project documenting itself correctly. An audit that cannot tell
    a historical record from an uncorrected claim will keep recommending the deletion of
    the project's own memory.
    """
    spans = [(m.start(), m.end()) for m in re.finditer(r"<!--.*?-->", text, re.S)]
    spans += [(m.start(), m.end()) for m in re.finditer(r"^[ \t]*//.*$", text, re.M)]
    spans += [(m.start(), m.end()) for m in re.finditer(r"/\*.*?\*/", text, re.S)]
    return spans


def in_span(pos, spans):
    return any(a <= pos < b for a, b in spans)


def bounds(text, s, e, before, after):
    """The region around a match, stopped at the enclosing table row or line.

    THE BUG THIS EXISTS TO KILL, which it took three attempts to get right.

    Run 1 flagged A.4 as an overclaim because a fixed 200-character window ran backwards
    past `</tr>` and picked up the PREVIOUS row's UNGROUNDED.

    Run 2 "fixed" it by clipping the DISPLAYED context — so the printed line looked
    correct while the MATCH was still made against the unbounded window. A.4 was flagged
    again, now with tidy-looking evidence. The symptom was prettier and the defect intact.
    Reading the real row settled it: `A.4 | Product Lifecycle | Repairability scores;
    certifications, CDP Forests or industry default otherwise | PARTIAL` is honest.

    Three mis-flags of one sub-signal, all the same error: treating a character count as
    if it respected structure. A table row is a record. Evidence from the row above it is
    not evidence about this one.

    So matching and display now share these bounds. There is one window, and it ends where
    the record ends.
    """
    lo, hi = max(0, s - before), min(len(text), e + after)
    cut = text.rfind("<tr", lo, s)
    if cut == -1:
        cut = text.rfind("\n", lo, s)
    if cut != -1:
        lo = cut + 1
    cut = text.find("</tr>", e, hi)
    if cut == -1:
        cut = text.find("\n", e, hi)
    if cut != -1:
        hi = cut
    return lo, hi


def clip(text, s, e, before=90, after=110):
    lo, hi = bounds(text, s, e, before, after)
    return text[lo:hi].replace("\n", " ").strip()


def near(text, a_pats, b_pats, window=400, spans=()):
    """Hits where a term from a_pats appears near one from b_pats, within one record."""
    out = []
    for ap in a_pats:
        for m in re.finditer(ap, text, re.I):
            if in_span(m.start(), spans):
                continue
            lo, hi = bounds(text, m.start(), m.end(), window, window)
            if any(re.search(bp, text[lo:hi], re.I) for bp in b_pats):
                out.append((text[:m.start()].count("\n") + 1, clip(text, m.start(), m.end())))
    return out


for p in surfaces:
    t = p.read_text(errors="replace")
    spans = comment_spans(t)
    hits, muted = [], 0

    # 2. spec versions. Skipped inside comments: a patch-marker stack and a code comment
    #    naming the version that changed a line are records, not claims.
    for m in re.finditer(r"v?(\d+\.\d+\.\d+)", t):
        v = m.group(1)
        if v == eng_spec or not re.match(r"1\.\d+\.\d+", v):
            continue
        if in_span(m.start(), spans):
            muted += 1
            continue
        hits.append(("spec", t[:m.start()].count("\n") + 1,
                     f"v{v} (engine is {eng_spec}) — {clip(t, m.start(), m.end(), 70, 70)}"))

    # 3. count claims. The (?<![\d.]) stops "1.78 sub-signals per company" being read as
    #    a claim of 78 sub-signals, which the first run did.
    for m in re.finditer(r"(?<![\d.])(\d{1,2})\s+(active\s+)?(sub-?signals?|signals?|"
                         r"sources?|dimensions?)\b", t, re.I):
        if in_span(m.start(), spans):
            muted += 1
            continue
        hits.append(("count", t[:m.start()].count("\n") + 1,
                     m.group(0).strip() + "  —  " + clip(t, m.start(), m.end(), 60, 80)))

    # 4. retired sub-signals, outside a historical context
    for ss in RETIRED:
        for m in re.finditer(re.escape(ss), t):
            ctx = clip(t, m.start(), m.end(), 80, 110)
            if re.search(r"retire|removed|withdrew|withdrawn|dropped|history|"
                         r"v1\.1[01]|defect", ctx, re.I):
                muted += 1
                continue
            hits.append(("retired", t[:m.start()].count("\n") + 1, f"{ss} — {ctx}"))

    # 5. status words disagreeing with the RUBRIC. Clipped at the row so a table cannot
    #    lend one sub-signal its neighbour's status.
    for ss, st in status.items():
        for m in re.finditer(re.escape(ss), t):
            seg = clip(t, m.start(), m.end(), 0, 160)
            other = [w for w in ("GROUNDED", "PARTIAL", "UNGROUNDED")
                     if re.search(r"\b" + w + r"\b", seg) and w != st]
            if other:
                hits.append(("status", t[:m.start()].count("\n") + 1,
                             f"{ss} called {other[0]}, RUBRIC says {st}\n"
                             f"           …{seg[:150]}…"))

    # 6. the eight debunked claims
    claim_lines = set()
    for label, a, b, truth in DEBUNKED:
        for ln, ctx in near(t, a, b, spans=spans):
            if (ln, label) in claim_lines:      # the same spot matched by two patterns
                continue
            claim_lines.add((ln, label))
            hits.append(("CLAIM", ln, f"{label}\n           …{ctx}…\n"
                                      f"           TRUE: {truth}"))

    # 6b. unusable sources: every mention outside a comment, minus credits only
    for name, (pat, why) in UNUSABLE.items():
        seen_lines = set()
        n_all = n_credit = 0
        for m in re.finditer(pat, t, re.I):
            n_all += 1
            if in_span(m.start(), spans):
                muted += 1
                continue
            ln = t[:m.start()].count("\n") + 1
            if ln in seen_lines or any(k == "CLAIM" and l == ln for k, l, _ in hits):
                continue                        # already reported against this line
            ctx = clip(t, m.start(), m.end(), 110, 140)
            if re.search(CREDIT, ctx, re.I):
                n_credit += 1
                continue                        # crediting the work, not claiming the data
            seen_lines.add(ln)
            promise = re.search(PROMISE, ctx, re.I)
            kind = "PROMISE" if promise else "unusable"
            lead = (f"{name} promised as a future grounding source"
                    if promise else f"{name} named as an input")
            hits.append((kind, ln, f"{lead}\n           …{ctx}…\n"
                                   f"           TRUE: {why}"))
        if n_all:
            tally.setdefault(str(p), []).append(
                (name, n_all, len(seen_lines), n_credit))

    # 7. grounded language on a sub-signal the coverage line calls a constant
    for ss in mostly_const:
        for ln, ctx in near(t, [re.escape(ss)],
                            [r"grounded", r"measured", r"verified", r"authoritative",
                             r"from (BLS|O\*NET|EPA|OSHA|SEC)"], window=200, spans=spans):
            hits.append(("overclaim", ln,
                         f"{ss} described as grounded/measured — RUBRIC coverage: "
                         f"{coverage[ss][:110]}\n           …{ctx}…"))

    if hits or muted:
        findings.append((p, hits, muted))

ORDER = {"CLAIM": 0, "PROMISE": 1, "unusable": 2, "overclaim": 3, "retired": 4,
         "status": 5, "spec": 6, "count": 7}
print("\n" + "=" * 92)
tot_hits = tot_muted = 0
for p, hits, muted in findings:
    tot_hits += len(hits)
    tot_muted += muted
    note = f"  ({muted} muted as deliberate history)" if muted else ""
    print(f"\n{p}  —  {len(hits)} to look at{note}")
    print("-" * 92)
    for kind, ln, msg in sorted(hits, key=lambda h: (ORDER.get(h[0], 9), h[1])):
        print(f"  {kind:10} :{ln:<5} {msg}")

print(f"\n{'=' * 92}\n{tot_hits} to look at · {tot_muted} muted as deliberate history "
      f"· {len(skipped)} backup files not scanned")

if tally:
    print("\nUNUSABLE SOURCES — every mention accounted for, so suppression is visible")
    print(f"  {'file':26} {'source':8} {'mentions':>8} {'flagged':>8} {'credits':>8}")
    print("  " + "─" * 64)
    for f, rows in tally.items():
        for name, n_all, n_flag, n_cr in rows:
            print(f"  {f[:26]:26} {name:8} {n_all:>8} {n_flag:>8} {n_cr:>8}")
    print("  mentions - flagged - credits = the ones inside comments, counted in 'muted'.")
    print("  If flagged is 0 while mentions is not, read the lines before believing it.")

if not findings:
    print("\n  Nothing flagged. Unlikely on a first run — check that the globs above")
    print("  actually found README.md and METHODOLOGY.md.")

print("\n" + "=" * 92)
print("\nHOW TO READ THIS")
print("  CLAIM     — the surface repeats a source claim the RUBRIC now corrects. Highest")
print("              priority: the public statement is wrong while the internal one is right.")
print("  PROMISE   — a source the project CANNOT use, named as a future grounding target.")
print("              A commitment that cannot be kept is worse than a stale fact: the")
print("              first is a plan a reviewer will ask about, the second is a typo.")
print("  unusable  — a source the project cannot use, advertised as a current input.")
print("              GRI (database decommissioned), CDP (licence forbids commercial use),")
print("              B Corp (score eliminated under V2 standards from 2027).")
print("  overclaim — grounded/measured language on a sub-signal its own coverage line says")
print("              is carried by a constant.")
print("  retired   — a retired sub-signal named outside a historical context.")
print("  status    — a status word disagreeing with the RUBRIC's.")
print("  spec      — a version string that is not the engine's. Some are legitimately")
print("              historical ('changed in v1.10.0'); the context line says which.")
print("  count     — every count claim, for reading. Not all are wrong: 18 sub-signals")
print("              exist in the schema. The question is whether the sentence implies")
print("              they are all measured.")
print("\n  A count can be true of the schema and false of the measurement. That is the")
print("  distinction the RUBRIC's coverage lines now carry and these surfaces do not.")
print("\nWHAT 'MUTED' MEANS, AND WHY IT IS NOT A SUPPRESSION")
print("  A version string inside an HTML comment, a code comment naming the release that")
print("  changed a line, and a retired sub-signal named beside the word 'retired' are the")
print("  project documenting itself correctly. The first run of this script printed ~35 of")
print("  them as staleness, alongside 64 flags from four .bak files — about half the output")
print("  was noise, and a tool that prints twice what it should trains the reader to skim.")
print("  Muted counts are shown per file so nothing is hidden, only ranked.")
print("\nNothing changed. Read-only.")
