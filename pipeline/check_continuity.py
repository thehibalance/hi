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
]


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
