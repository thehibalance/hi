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
    ("human-edge/content.js", r"Spec v([0-9.]+) &middot; 19 active", "extension badge"),
    ("ios/HI/HI/AboutView.swift", r"Heartbeat\)\. Spec v([0-9.]+)\.", "iOS about screen"),
    ("METHODOLOGY.md", r"\*\*Document version ([0-9.]+) ", "METHODOLOGY version line"),
    ("METHODOLOGY.md", r"\*\*HI Grade Methodology v([0-9.]+)\*\*", "METHODOLOGY footer"),
    # The extension ships its own implementation of the Gold gates. Its banner claimed
    # spec v1.2.0 for six releases because nothing checked this file.
    ("human-edge/lib/engine.js", r"Filter Engine — v([0-9.]+)", "extension engine banner"),
    ("human-edge/lib/engine.js", r"SPECIFICATION REFERENCE: HUMAN Methodology Spec v([0-9.]+)", "extension engine spec ref"),
]


NOT_SOURCES = {"Industry", "Manual Scoring", "Defaults", "Seed Estimate"}


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
            if src in NOT_SOURCES:
                continue
            if src.startswith("SEC"):
                src = "SEC"
            elif src == "Industry+EPA":
                src = "EPA"
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
    counts = []
    for c in companies:
        m = re.match(r"(\d+)/(\d+)", str(c.get("signal_coverage") or ""))
        if m:
            counts.append(int(m.group(1)))
    return int(statistics.median(counts)) if counts else None


# Each claim is anchored on the word "median" so the correction trail — "used to say 7 of 19"
# — is not mistaken for a live claim.
COVERAGE_CLAIMS = [
    ("README.md", r"median company has real data behind \*\*(\d+) of 19\*\*"),
    ("RUBRIC.md", r"[Mm]edian coverage is now a truthful \*\*(\d+)/19\*\*"),
    ("docs/index.html", r"median company has real data behind <strong>(\d+) of its 19</strong>"),
    ("METHODOLOGY.md", r"median company, only \*\*(\d+) of those 19\*\*"),
]


def check_coverage():
    """Warn, do not fail: like the source count, this runs before the nightly regenerates
    scores, so a change published tonight shows up here tomorrow."""
    actual = median_coverage()
    if actual is None:
        return
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
            print(f"  {mark} median coverage        {rel} claims {v}/19, scores show {actual}/19")


def check_source_count():
    """Warn, do not fail: this runs before the nightly pipeline regenerates scores, so a change
    published tonight shows up here tomorrow."""
    actual = contributing_sources()
    if actual is None:
        return
    readme = (ROOT / "README.md").read_text(errors="ignore")
    claims = set(int(m) for m in re.findall(r"\*\*?(\d+) sources feed today's scores", readme))
    claims |= set(int(m) for m in re.findall(r"(\d+) sources feed today's scores", readme))
    if not claims:
        print("  ?  README makes no 'N sources feed today's scores' claim")
        return
    for c in sorted(claims):
        mark = "OK" if c == actual else "!!"
        print(f"  {mark} README source count      claims {c}, scores show {actual}")
    if claims != {actual}:
        print(f"  !! README's source count is stale. Live figure: "
              f"curl https://api.thehibalance.org/api/v1/stats | jq .data_sources")


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
    ("README.md", r"sources feed today's scores, out of (\d+) integrated"),
    ("README.md", r"sources feed today's scores; (\d+) are integrated"),
    ("README.md", r"\(\d+ producing, (\d+) wired\)"),
    ("METHODOLOGY.md", r"pipelines pull data from (\d+) public sources"),
    ("METHODOLOGY.md", r"The data sources — (\d+) integrated"),
    ("METHODOLOGY.md", r"(\d+) public data sources are integrated"),
    ("docs/index.html", r"(\d+) public sources\. Zero ESG ratings"),
    ("docs/index.html", r"Edge-to-cloud\. (\d+) public data sources"),
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
            print(f"  ?  {rel:20} makes no registered-source claim matching {pattern!r}")
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
            print(f"  ?  {label:24} pattern not found in {rel}")
            continue
        for v in set(found):
            ok = (v == spec)
            print(f"  {'OK' if ok else 'XX'} {label:24} {rel} -> v{v}")
            if not ok:
                bad.append(f"{label} ({rel}) says v{v}, engine says v{spec}")
    check_source_count()
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
