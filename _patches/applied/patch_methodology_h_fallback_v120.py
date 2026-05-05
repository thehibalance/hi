#!/usr/bin/env python3
"""
v1.2.0 Methodology Page H-Fallback Disclosure — docs/index.html

Adds explicit disclosure that industry RPE medians fire as a FALLBACK
when per-company SEC workforce data is unavailable, and that this can
produce identical H sub-signals across companies in the same industry
(e.g., KO and SBUX both showing H.1=80, H.2=65, H.3=55, H.5=80 because
both fall to consumer-goods medians).

Existing card at line ~962-963 explains medians ARE hardcoded but not
that they're being SUBSTITUTED IN for ~30-40% of the universe. This
patch adds one sentence to make that explicit.

Anchor: exact-string match on the existing card body text.

Usage (from repo root):
  python3 patch_methodology_h_fallback_v120.py
"""

import sys
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "docs" / "index.html"


# ── Anchor: existing card body (line 963 approximate) ──
OLD_TEXT = ('<p>Many sub-signals normalize by industry. Medians were derived from aggregated '
            'SEC data but are currently hardcoded constants. Last refresh Q1 2026; '
            'next scheduled Q3 2026.</p>')

NEW_TEXT = ('<p>Many sub-signals normalize by industry. Medians were derived from aggregated '
            'SEC data but are currently hardcoded constants. Last refresh Q1 2026; '
            'next scheduled Q3 2026.</p>'
            '<p>When per-company SEC workforce data is unavailable, sub-signals fall back '
            'to these industry medians. This affects roughly 30-40% of the S&amp;P 500 universe '
            'today and means companies in the same industry can show identical H sub-signals '
            '— e.g., Coca-Cola and Starbucks both default to consumer-goods medians until '
            'broader workforce data sources are integrated. We disclose rather than mask the '
            'fallback; expanding per-company H signal coverage is on the v1.2.1 roadmap.</p>')


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    if OLD_TEXT not in src:
        sys.exit(
            "ABORT — anchor text not found verbatim.\n"
            "The methodology card at line ~963 may have been edited.\n"
            "Look for the 'Industry Revenue-Per-Employee medians are hardcoded' card."
        )

    if NEW_TEXT in src:
        sys.exit("ABORT — file already contains v1.2.0 fallback disclosure. No-op.")

    # Defensive: confirm the OLD_TEXT appears exactly once (avoid clobbering other text)
    if src.count(OLD_TEXT) != 1:
        sys.exit(
            f"ABORT — anchor text appears {src.count(OLD_TEXT)} times, expected exactly 1.\n"
            "Refusing to patch ambiguously."
        )

    new_src = src.replace(OLD_TEXT, NEW_TEXT, 1)
    if new_src == src:
        sys.exit("ABORT — replacement had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".h_fallback_bak")
    tmp.write_text(new_src)

    # Sanity: byte count diff is small (positive, not negative)
    src_len = len(src)
    new_len = len(new_src)
    if not (0 < new_len - src_len < 2000):
        tmp.unlink()
        sys.exit(f"ABORT — unexpected size change: {src_len} → {new_len} bytes")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print(f"✓ Patched: {TARGET}")
    print(f"  Backup: {backup.name}")
    print(f"  Bytes added: {new_len - src_len}")
    print()
    print("  Methodology page now explicitly discloses the H industry-default fallback")
    print("  and acknowledges KO/SBUX as a visible example.")
    print()
    print("  Next:")
    print("    git add docs/index.html")
    print("    git commit + push (GitHub Pages auto-deploys ~30-60s)")


if __name__ == "__main__":
    main()
