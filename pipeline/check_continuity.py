#!/usr/bin/env python3
"""Fail the build when a published surface disagrees with the engine.

Five spec versions shipped in one day and the README badge, the RUBRIC footer, METHODOLOGY, the
Chrome extension and the iOS app all ended up claiming different ones -- RUBRIC contradicted
itself inside a single file. Numbers a reader can check are the whole product here, so drift in
them is a correctness bug, not a tidiness one.

Run from the repo root:  python3 pipeline/check_continuity.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def engine_spec():
    m = re.search(r'"spec_version":\s*"([0-9.]+)"', (ROOT / "pipeline/scoring_engine.py").read_text())
    return m.group(1) if m else None


# (path, regex capturing a version, human description)
SURFACES = [
    ("README.md", r"badge/spec-v([0-9.]+)-", "README spec badge"),
    ("RUBRIC.md", r"Spec version: \*\*v([0-9.]+)\*\*", "RUBRIC header"),
    ("RUBRIC.md", r"Last updated:[^.]*\. Spec v([0-9.]+)", "RUBRIC footer"),
    ("docs/index.html", r"c\.spec_version \|\| '([0-9.]+)'", "site spec fallback"),
    ("human-edge/content.js", r"Spec v([0-9.]+) &middot; 18 active", "extension badge"),
    ("ios/HI/HI/AboutView.swift", r"Heartbeat\)\. Spec v([0-9.]+)\.", "iOS about screen"),
    ("METHODOLOGY.md", r"\*\*Document version ([0-9.]+) ", "METHODOLOGY version line"),
    ("METHODOLOGY.md", r"\*\*HI Grade Methodology v([0-9.]+)\*\*", "METHODOLOGY footer"),
    # The extension ships its own implementation of the Gold gates. Its banner claimed
    # spec v1.2.0 for six releases because nothing checked this file.
    ("human-edge/lib/engine.js", r"Filter Engine — v([0-9.]+)", "extension engine banner"),
    ("human-edge/lib/engine.js", r"SPECIFICATION REFERENCE: HUMAN Methodology Spec v([0-9.]+)", "extension engine spec ref"),
    # v1.15.0: three claims about the CURRENT engine that no pattern above reached. The
    # v1.14.0 bump landed on all ten surfaces and a scan for leftover "1.13.0" then found
    # these, each asserting it described the current spec. Four other leftovers in RUBRIC.md
    # and scoring_engine.py are correct history and deliberately not covered here — a gate
    # that fails on an accurate historical reference gets switched off.
    ("METHODOLOGY.md", r"corrected to the current engine, spec v([0-9]+[.][0-9]+[.][0-9]+)", "METHODOLOGY correction note"),
    ("METHODOLOGY.md", r"The current engine \(spec v([0-9.]+)\)", "METHODOLOGY engine note"),
    ("README.md", r"\*\*Current state \(v([0-9.]+)\)", "README current state"),
]


# v1.13.1: this used to be a four-member copy of api_server._NOT_SOURCES, which has seven.
# The copy went stale when PRs #40/#42/#43 added names to the original, so this check reported
# README's stale 21 as correct for eight hours. One definition now, imported — the copy is
# deleted rather than corrected, because correcting it would leave the same failure available.
# See claude/FINDING-the-gate-copies-the-rule-it-claims-to-mirror.md
sys.path.insert(0, str(ROOT / "pipeline"))
from source_rules import NOT_SOURCES, normalize_source  # noqa: E402


def contributing_sources():
    """Count sources the same way api_server.get_contributing_sources does, so the README's
    claim is checked against the same rule the live /stats endpoint applies."""
    import json
    p = ROOT / "pipeline/data/scores/all_scores.json"
    if not p.exists():
        return None
    try:
        companies = json.load(open(p))
    except (OSError, ValueError):
        return None
    seen = set()
    for c in companies:
        for src in (c.get("data_sources") or []):
            src = normalize_source(src)
            if src is None:
                continue
            seen.add(src)
    return len(seen)


def median_coverage():
    """The median number of sub-signals with real data, computed from the scores rather than
    taken from anyone's memory. This is the figure that moved 7 -> 5 -> 4 in three days while
    four documents each claimed a different one."""
    import json
    import statistics
    p = ROOT / "pipeline/data/scores/all_scores.json"
    if not p.exists():
        return None
    try:
        companies = json.load(open(p))
    except (OSError, ValueError):
        return None
    counts, denoms = [], set()
    for c in companies:
        m = re.match(r"(\d+)/(\d+)", str(c.get("signal_coverage") or ""))
        if m:
            counts.append(int(m.group(1)))
            denoms.add(m.group(2))
    if not counts:
        return None
    return int(statistics.median(counts)), "/".join(sorted(denoms))


# Each claim is anchored on the word "median" so the correction trail — "used to say 7 of 19"
# — is not mistaken for a live claim.
COVERAGE_CLAIMS = [
    ("README.md", r"median company has real data behind \*\*(\d+) of 18\*\*"),
    ("RUBRIC.md", r"[Mm]edian coverage is now a truthful \*\*(\d+)/18\*\*"),
    ("docs/index.html", r"median company has real data behind <strong>(\d+) of its 18</strong>"),
    ("METHODOLOGY.md", r"median company, only \*\*(\d+) of those 18\*\*"),
]


def check_coverage():
    """Warn, do not fail: like the source count, this runs before the nightly regenerates
    scores, so a change published tonight shows up here tomorrow."""
    got = median_coverage()
    if got is None:
        return
    actual, denom = got
    for rel, pattern in COVERAGE_CLAIMS:
        p = ROOT / rel
        if not p.exists():
            continue
        found = set(re.findall(pattern, p.read_text(errors="ignore")))
        if not found:
            print(f"  ?  {rel:20} makes no median-coverage claim in the expected form")
            continue
        for v in sorted(found):
            mark = "OK" if int(v) == actual else "!!"
            print(f"  {mark} median coverage        {rel} claims {v}, "
                  f"scores show {actual}/{denom}")


def check_source_count():
    """Returns findings. Over-claiming fails the build; under-claiming warns.

    v1.13.1: this used to warn only, on the same reasoning as median coverage — "runs before the
    nightly regenerates scores, so a change published tonight shows up here tomorrow." That is
    right for a figure the nightly moves and wrong for this one. `contributing_sources()` applies
    TODAY's rule to last night's rows, so a count that changed because of a CODE change is
    already checkable: README's 18 was true the moment PR #43 merged, not the next morning.

    What the nightly can still do is bring a new source online, raising the measured count above
    the README's claim for one morning. Failing the build for that would punish honesty. So the
    asymmetry: claiming MORE sources than are measured is the defect this project exists to
    remove and fails; claiming fewer resolves itself overnight and warns.
    """
    actual = contributing_sources()
    if actual is None:
        print("  XX README source count      cannot be checked: no all_scores.json")
        return ["contributing-source count unreadable — pipeline/data/scores/all_scores.json "
                "missing, so the README's claim was not checked at all"]
    readme = (ROOT / "README.md").read_text(errors="ignore")
    claims = set(int(m) for m in re.findall(r"\*\*?(\d+) sources feed today's scores", readme))
    claims |= set(int(m) for m in re.findall(r"(\d+) sources feed today's scores", readme))
    if not claims:
        print("  XX README makes no 'N sources feed today's scores' claim")
        return ["README makes no 'N sources feed today's scores' claim — the sentence was "
                "reworded and this check silently stopped covering it"]
    bad = []
    for c in sorted(claims):
        mark = "OK" if c == actual else ("XX" if c > actual else "!!")
        print(f"  {mark} README source count      claims {c}, scores show {actual}")
        if c > actual:
            bad.append(f"README claims {c} sources feed today's scores; {actual} do. "
                       f"Over-claiming — the live figure is "
                       f"curl https://api.thehibalance.org/api/v1/stats | jq .data_sources")
        elif c < actual:
            print(f"  !! README under-claims ({c} < {actual}). Not a failure: a source that "
                  f"came online overnight shows up here before the README catches up.")
    return bad


def registry_total():
    """How many sources source_audit.py actually registers. The docs quoted 42 in seven
    places and nothing checked any of them, so removing one retired collector would have
    left every one of those claims wrong and the build green."""
    p = ROOT / "pipeline/source_audit.py"
    if not p.exists():
        return None
    return len(re.findall(r'\{"id":\s*\d+,', p.read_text(errors="ignore"))) or None


# Anchored on wording specific to the source count. The composite floor rule also uses the
# number 42; these patterns must never match it.
REGISTRY_CLAIMS = [
    ("README.md", r"sources feed today's scores, out of (\d+) registered"),
    ("README.md", r"sources feed today's scores; (\d+) are registered"),
    ("README.md", r"\(\d+ producing, (\d+) wired\)"),
    ("METHODOLOGY.md", r"pipelines pull data from (\d+) public sources"),
    ("METHODOLOGY.md", r"The data sources — (\d+) integrated"),
    ("METHODOLOGY.md", r"(\d+) public data sources are integrated"),
    # 2026-10-30: two patterns removed. Both were anchored to the body of a spotlight card,
    # and both cards were deleted — one re-published the source count beside "Zero ESG
    # ratings", the other inside an "Edge-to-cloud" line. A check whose anchor is editorial
    # copy is deleted by a copy edit, which is how this was found. The source count on
    # docs/index.html is still reconciled by the two patterns below, and by the two
    # METHODOLOGY.md patterns above, so this removes two anchors and no coverage.
    # See claude/FINDING-the-gates-source-count-check-is-anchored-to-marketing-copy.md
    ("docs/index.html", r"reconstructable from (\d+) public sources"),
    ("docs/index.html", r"ZERO AI in scoring\.</strong> (\d+) public data sources"),
]


def check_registry_total():
    """Fails the build, unlike the source count and coverage median: this figure comes from
    the registry in the repo, not from last night's data, so it can be checked exactly."""
    actual = registry_total()
    if actual is None:
        return []
    bad = []
    for rel, pattern in REGISTRY_CLAIMS:
        p = ROOT / rel
        if not p.exists():
            continue
        found = set(re.findall(pattern, p.read_text(errors="ignore")))
        if not found:
            # v1.13.1: fail rather than shrug. A declared claim that cannot be found is either a
            # surface that drifted or a pattern that went stale. Passing silently meant an
            # honest rewording removed a surface from the gate without anyone noticing, so the
            # only edit that kept the build green was the one that kept the wrong number.
            print(f"  XX {rel:20} makes no registered-source claim matching {pattern!r}")
            bad.append(f"{rel}: no registered-source claim matches {pattern!r} — "
                       f"surface reworded, or pattern stale")
            continue
        for v in sorted(found):
            ok = int(v) == actual
            print(f"  {'OK' if ok else 'XX'} registered sources      {rel} claims {v}, "
                  f"source_audit registers {actual}")
            if not ok:
                bad.append(f"{rel} claims {v} integrated sources, "
                           f"source_audit.py registers {actual}")
    return bad


def main():
    spec = engine_spec()
    if not spec:
        print("could not read spec_version from scoring_engine.py")
        return 1
    print(f"  engine spec_version: {spec}")
    bad = []
    for rel, pattern, label in SURFACES:
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(errors="ignore").replace("\u00b7", "&middot;").replace(chr(183), "&middot;")
        found = re.findall(pattern, text)
        if not found:
            # v1.13.1: same reasoning as the registry claims — a spec surface that stops
            # matching its pattern has either moved or been reworded, and both deserve red.
            print(f"  XX {label:24} pattern not found in {rel}")
            bad.append(f"{label} ({rel}): spec pattern no longer matches — surface moved, "
                       f"or pattern stale")
            continue
        for v in set(found):
            ok = (v == spec)
            print(f"  {'OK' if ok else 'XX'} {label:24} {rel} -> v{v}")
            if not ok:
                bad.append(f"{label} ({rel}) says v{v}, engine says v{spec}")
    bad += check_source_count()
    check_coverage()
    bad += check_registry_total()

    if bad:
        print("\n  Continuity check FAILED:")
        for b in bad:
            print("    - " + b)
        print("\n  Update the surface, or the engine, so every published number agrees.")
        return 1
    print("\n  Continuity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
