#!/usr/bin/env python3
"""
v1.2.0 Version Drift Sweep — eliminates stale v1.1.0 / "v1.2 target" / "v1.1.7"
references across all non-iOS surfaces. iOS handled separately via patch_ios_v120.py.

Scope:
  README.md          — 8 stale references
  RUBRIC.md          — 4 stale references
  docs/index.html    — 2 stale references in deep-dive cards
  human-edge/lib/engine.js — 8 docstring/comment references
  pipeline/api_server.py  — 1 fallback default ('1.0.2' → '1.2.0')

What this does NOT touch:
  - Historical version comments in scoring_engine.py / api_server.py that
    describe what changed in past versions (those are correct, keep)
  - iOS Swift files (separate patcher — different validation path)
  - The forward-looking 'deferred to v1.3' references already added by Patcher 11/13
  - Any AUDIT_*/CHANGELOG-style historical record files

Strategy:
  Each file gets its own list of (old_string, new_string) tuples. All anchors
  must match for that file's edits to apply. If any single anchor in a file is
  missing, abort that file but continue others.

Usage (from repo root):
  python3 patch_version_sweep_v120.py
"""

import sys
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if not (REPO_ROOT / "README.md").exists():
    REPO_ROOT = Path.cwd()


# ════════════════════════════════════════════════════════════════════
# README.md edits
# ════════════════════════════════════════════════════════════════════

README_EDITS = [
    # Edit 1: Current state header
    (
        "**Current state (v1.1.0):**",
        "**Current state (v1.2.0):**",
    ),
    # Edit 2: 7 sub-signals deferred line
    (
        "- 7 sub-signals are spec'd but not yet scored (v1.2 target).",
        "- 5 sub-signals are spec'd but not yet scored (v1.3 target).",
    ),
    # Edit 3: v1.2 sub-signals roadmap line
    (
        "- v1.2 sub-signals (H.4, H.5, U.5, A.5, N.1, N.3, N.4)",
        "- v1.3 sub-signals (H.4, U.5, N.1, N.3, N.4)",
    ),
    # Edit 4: Chrome Extension version row → just "Shipped"
    (
        "| Chrome Extension v1.1.7 | ✅ Shipped |",
        "| Chrome Extension | ✅ Shipped |",
    ),
    # Edit 5: iOS App version row → just "Shipped"
    (
        "| iOS App v1.1.0 | In Apple review |",
        "| iOS App | ✅ Shipped |",
    ),
    # Edit 6: Sub-signals roadmap target
    (
        "| Sub-signals H.4, H.5, U.5, A.5, N.1, N.3, N.4 | v1.2 target |",
        "| Sub-signals H.4, U.5, N.1, N.3, N.4 | v1.3 target |",
    ),
    # Edit 7: Subsidiary Transparency Rule target
    (
        "| Subsidiary Transparency Rule (SEC Exhibit 21) | v1.2 target |",
        "| Subsidiary Transparency Rule (SEC Exhibit 21) | v1.3 target |",
    ),
    # Edit 8: Whitepaper version
    (
        "| HUMAN Grade Spec v1.1.0 whitepaper | Copyright registered |",
        "| HUMAN Grade Spec v1.2.0 whitepaper | Copyright registered |",
    ),
]


# ════════════════════════════════════════════════════════════════════
# RUBRIC.md edits
# ════════════════════════════════════════════════════════════════════

RUBRIC_EDITS = [
    # Edit 1: Notes line about only fully grounded sub-signal
    (
        "**Notes:** Currently the only fully grounded sub-signal in v1.1.0.",
        "**Notes:** Currently the only fully grounded sub-signal in v1.2.0.",
    ),
    # Edit 2: Deferred section header
    (
        "## Deferred to v1.2",
        "## Deferred to v1.3",
    ),
    # Edit 3: Deferred section explanation paragraph
    (
        "These 5 sub-signals are spec'd in HUMAN Grade Spec v1.1.0 but not yet scored. They will be added in v1.2. Until then, they receive no contribution to dimension scores.",
        "These 5 sub-signals are spec'd in HUMAN Grade Spec v1.2.0 but not yet scored. They will be added in v1.3. Until then, they receive no contribution to dimension scores.",
    ),
    # Edit 4: Last updated footer
    (
        "*Last updated: April 2026. Spec v1.1.0. Maintained by Morf Innovations LLC. Apache 2.0 licensed.*",
        "*Last updated: April 2026. Spec v1.2.0. Maintained by Morf Innovations LLC. Apache 2.0 licensed.*",
    ),
]


# ════════════════════════════════════════════════════════════════════
# docs/index.html edits — only the two deep-dive cards still saying v1.1.0/v1.2
# (Other v1.1.0 refs were already updated by Patcher 12 — methodology page subhead
# and Balanced Board section header.)
# ════════════════════════════════════════════════════════════════════

INDEX_HTML_EDITS = [
    # Edit 1: "dominant pattern is v1.1.0" deep-dive card text
    (
        "<p>This is the dominant pattern in v1.1.0. Most scoring uses authoritative data",
        "<p>This is the dominant pattern in v1.2.0. Most scoring uses authoritative data",
    ),
    # Edit 2: "deferred to v1.2... v1.2 roadmap" line (D_N weights note)
    (
        "Sub-signals N.1, N.3, N.4 are deferred to v1.2. Additional grounded signals (DSA transparency, 12b-25 late-filings) are on the v1.2 roadmap.",
        "Sub-signals N.1, N.3, N.4 are deferred to v1.3. Additional grounded signals (DSA transparency, 12b-25 late-filings) are on the v1.3 roadmap.",
    ),
    # Edit 3: "Technical work planned for v1.2" line in industry medians card
    (
        "<strong>Path forward:</strong> dynamic industry median computation from the live company universe. Technical work planned for v1.2.",
        "<strong>Path forward:</strong> dynamic industry median computation from the live company universe. Technical work planned for v1.3.",
    ),
]


# ════════════════════════════════════════════════════════════════════
# human-edge/lib/engine.js edits — block-level docstring + scattered comments
# ════════════════════════════════════════════════════════════════════

ENGINE_JS_EDITS = [
    # Edit 1: File header
    (
        " * HI. Grade Filter Engine — v1.1.0",
        " * HI. Grade Filter Engine — v1.2.0",
    ),
    # Edit 2: Spec reference line
    (
        " * SPECIFICATION REFERENCE: HUMAN Methodology Spec v1.1.0",
        " * SPECIFICATION REFERENCE: HUMAN Methodology Spec v1.2.0",
    ),
    # Edit 3: Gate changes header (historical — describes the v1.1 transition,
    # so we keep "v1.1.0 GATE CHANGES from v1.0" as historical accuracy)
    # → no change to that line; it correctly describes what v1.1 did
    # Edit 4: Constants comment
    (
        "  // ═══ CONSTANTS (from Methodology Spec v1.1.0) ═══",
        "  // ═══ CONSTANTS (from Methodology Spec v1.2.0) ═══",
    ),
    # Edit 5: Gold HI Grade check fn comment
    (
        "   * Check if a company earns Gold HI Grade (v1.1.0 spec).",
        "   * Check if a company earns Gold HI Grade (v1.2.0 spec).",
    ),
    # Edit 6: Threshold backward-compat comment
    (
        "    // Threshold returned for backward compat — in v1.1.0 it's the per-dim threshold (60), not composite",
        "    // Threshold returned for backward compat — in v1.2.0 it's the per-dim threshold (60), not composite",
    ),
    # Edit 7: Humanwashing display comment
    (
        "  // These are kept for display purposes — but NO LONGER affect Gold gates in v1.1.0.",
        "  // These are kept for display purposes — but NO LONGER affect Gold gates in v1.2.0.",
    ),
    # Edit 8: Score color comment
    (
        "   * v1.1.0: Green ≥ 60 (Dimensions gate threshold), Amber ≥ 42, Red < 42.",
        "   * v1.2.0: Green ≥ 60 (Dimensions gate threshold), Amber ≥ 42, Red < 42.",
    ),
]


# ════════════════════════════════════════════════════════════════════
# pipeline/api_server.py — fallback default for spec_version
# ════════════════════════════════════════════════════════════════════

API_SERVER_EDITS = [
    (
        'record.setdefault("spec_version", "1.0.2")',
        'record.setdefault("spec_version", "1.2.0")',
    ),
]


# ════════════════════════════════════════════════════════════════════
# Apply
# ════════════════════════════════════════════════════════════════════

def apply_edits(target_path, edits, label):
    if not target_path.exists():
        return False, f"NOT FOUND: {target_path}"

    src = target_path.read_text()
    missing = [old for old, _ in edits if old not in src]
    if missing:
        sample = "\n    ".join(repr(m[:80]) for m in missing[:3])
        return False, f"{label}: {len(missing)} anchor(s) missing. First missing:\n    {sample}"

    # Re-run guard: if any new value is already in the file, skip
    already_done = sum(1 for _, new in edits if new in src and new != old_for_new(edits, new))
    # Simpler heuristic: just check if first edit has been applied
    if edits[0][1] in src and edits[0][0] not in src:
        return False, f"{label}: already patched (first anchor not present, replacement is)"

    new_src = src
    for old, new in edits:
        new_src = new_src.replace(old, new, 1)

    if new_src == src:
        return False, f"{label}: no changes after replacement (anchors matched but content unchanged?)"

    tmp = target_path.with_suffix(target_path.suffix + ".tmp")
    backup = target_path.with_suffix(target_path.suffix + ".bak")
    tmp.write_text(new_src)
    shutil.copy2(target_path, backup)
    tmp.replace(target_path)
    return True, f"{label}: {len(edits)} edits applied (backup: {backup.name})"


def old_for_new(edits, new):
    """Helper: lookup old text for a given new text."""
    for o, n in edits:
        if n == new:
            return o
    return None


def main():
    targets = [
        (REPO_ROOT / "README.md", README_EDITS, "README.md"),
        (REPO_ROOT / "RUBRIC.md", RUBRIC_EDITS, "RUBRIC.md"),
        (REPO_ROOT / "docs" / "index.html", INDEX_HTML_EDITS, "docs/index.html"),
        (REPO_ROOT / "human-edge" / "lib" / "engine.js", ENGINE_JS_EDITS, "human-edge/lib/engine.js"),
        (REPO_ROOT / "pipeline" / "api_server.py", API_SERVER_EDITS, "pipeline/api_server.py"),
    ]

    results = []
    for path, edits, label in targets:
        ok, msg = apply_edits(path, edits, label)
        marker = "✓" if ok else "✗"
        results.append((ok, f"  {marker} {msg}"))

    print("v1.2.0 Version Drift Sweep")
    print("=" * 60)
    for _, line in results:
        print(line)
    print("=" * 60)

    n_ok = sum(1 for ok, _ in results if ok)
    print(f"  {n_ok}/{len(results)} files patched")

    if n_ok < len(results):
        print()
        print("  Failed files left unchanged. Review messages above.")
        sys.exit(1 if n_ok == 0 else 0)


if __name__ == "__main__":
    main()
