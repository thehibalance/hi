#!/usr/bin/env python3
"""
v1.2.0 iOS Version Sweep — Swift files

Updates user-facing v1.1.0 references in iOS app source. Comments that
describe historical v1.0→v1.1 transitions are kept (correct historical record).

Files touched:
  ios/HI/HI/AboutView.swift           — 'Spec v1.1.0.' user-facing text
  ios/HI/HI/Models.swift              — 2 docstring comments
  ios/HI/HI/CompanyDetailView.swift   — 3 references including a fallback default

Validation:
  - Exact-string anchors
  - Atomic write per file with .bak backup
  - No Swift compilation step (would require Xcode); relies on string accuracy

Usage (from repo root):
  python3 patch_ios_v120.py

After this lands, you will need to:
  - Open ios/HI in Xcode
  - Build & test on a simulator (verify nothing visually broken)
  - Increment marketing version + build number in Xcode project settings
  - Submit to App Store Connect
"""

import sys
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if not (REPO_ROOT / "ios").exists():
    REPO_ROOT = Path.cwd()


# ════════════════════════════════════════════════════════════════════
# AboutView.swift — user-facing about copy
# ════════════════════════════════════════════════════════════════════

ABOUT_VIEW_EDITS = [
    (
        'Text("Gold HI Grade requires all 5 HUMAN dimensions ≥ 60, each verified by public data, and no critical decay (90-day Heartbeat). Spec v1.1.0. Scores are estimated from public data. Not financial or legal advice.")',
        'Text("Gold HI Grade requires all 5 HUMAN dimensions ≥ 60, each verified by public data, and no critical decay (90-day Heartbeat). Spec v1.2.0. Scores are estimated from public data. Not financial or legal advice.")',
    ),
]


# ════════════════════════════════════════════════════════════════════
# Models.swift — docstring comments referencing the spec
# ════════════════════════════════════════════════════════════════════

MODELS_EDITS = [
    (
        "// v1.1.0: gate booleans returned by /api/v1/score/* — Dimensions, Evidence, Momentum",
        "// v1.2.0: gate booleans returned by /api/v1/score/* — Dimensions, Evidence, Momentum",
    ),
    (
        "    // v1.1.0: cloud-provided gate booleans (dimensions/evidence/momentum)",
        "    // v1.2.0: cloud-provided gate booleans (dimensions/evidence/momentum)",
    ),
]


# ════════════════════════════════════════════════════════════════════
# CompanyDetailView.swift — comments + fallback default
# ════════════════════════════════════════════════════════════════════

COMPANY_DETAIL_EDITS = [
    (
        "        // v1.1.0 spec: Dimensions / Evidence / Momentum.",
        "        // v1.2.0 spec: Dimensions / Evidence / Momentum.",
    ),
    (
        "        // v1.1.0: 19 active sub-signals; 6 marked (v1.2) are spec'd but not yet scored.",
        "        // v1.2.0: 19 active sub-signals; 5 marked (v1.3) are spec'd but not yet scored.",
    ),
    (
        '                metaTag("Spec", c.spec_version ?? "1.1.0")',
        '                metaTag("Spec", c.spec_version ?? "1.2.0")',
    ),
]


def apply_edits(target_path, edits, label):
    if not target_path.exists():
        return False, f"NOT FOUND: {target_path}"

    src = target_path.read_text()
    missing = [old for old, _ in edits if old not in src]
    if missing:
        sample = "\n    ".join(repr(m[:80]) for m in missing[:2])
        return False, f"{label}: {len(missing)}/{len(edits)} anchor(s) missing. Sample:\n    {sample}"

    new_src = src
    for old, new in edits:
        new_src = new_src.replace(old, new, 1)

    if new_src == src:
        return False, f"{label}: no changes after replacement"

    tmp = target_path.with_suffix(target_path.suffix + ".tmp")
    backup = target_path.with_suffix(target_path.suffix + ".bak")
    tmp.write_text(new_src)
    shutil.copy2(target_path, backup)
    tmp.replace(target_path)
    return True, f"{label}: {len(edits)} edits applied (backup: {backup.name})"


def main():
    targets = [
        (REPO_ROOT / "ios" / "HI" / "HI" / "AboutView.swift", ABOUT_VIEW_EDITS, "ios/HI/HI/AboutView.swift"),
        (REPO_ROOT / "ios" / "HI" / "HI" / "Models.swift", MODELS_EDITS, "ios/HI/HI/Models.swift"),
        (REPO_ROOT / "ios" / "HI" / "HI" / "CompanyDetailView.swift", COMPANY_DETAIL_EDITS, "ios/HI/HI/CompanyDetailView.swift"),
    ]

    results = []
    for path, edits, label in targets:
        ok, msg = apply_edits(path, edits, label)
        marker = "✓" if ok else "✗"
        results.append((ok, f"  {marker} {msg}"))

    print("v1.2.0 iOS Version Sweep")
    print("=" * 60)
    for _, line in results:
        print(line)
    print("=" * 60)

    n_ok = sum(1 for ok, _ in results if ok)
    print(f"  {n_ok}/{len(results)} files patched")
    print()
    print("  Next steps:")
    print("    1. Open ios/HI in Xcode")
    print("    2. Build → make sure no compile errors (string accuracy check)")
    print("    3. Run on simulator → verify About screen shows 'Spec v1.2.0'")
    print("    4. Bump marketing version in Xcode project settings (Target → General → Identity)")
    print("    5. Archive → distribute → App Store Connect")

    if n_ok < len(results):
        print()
        print("  Failed files left unchanged. Review messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
