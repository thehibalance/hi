#!/usr/bin/env python3
"""
Self-test for v1.2.0 compute_composite floor rule.
Run after applying patch_scoring_v120.py.
Exits 0 on success, 1 on any failure.

Usage (from repo root):
  python3 pipeline/patch_scoring_v120_test.py
"""
import sys
from pathlib import Path

# Make sibling import work whether run from repo root or pipeline/
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from scoring_engine import compute_composite  # noqa: E402


def case(label, dims, expect_composite, expect_floor, expect_dim):
    D_H, D_U, D_M, D_A, D_N = dims
    composite, floor, balance_unused, trig = compute_composite(D_H, D_U, D_M, D_A, D_N)
    ok = (
        composite == expect_composite
        and floor == expect_floor
        and trig == expect_dim
        and balance_unused is False  # always False in v1.2.0
    )
    status = "✓" if ok else "✗"
    print(f"  {status} {label}: composite={composite}, floor={floor}, trig={trig}")
    if not ok:
        print(f"      expected: composite={expect_composite}, floor={expect_floor}, trig={expect_dim}")
    return ok


def main():
    print("v1.2.0 compute_composite self-test")
    print("=" * 60)

    results = []

    # Real-world cases (matched to live API curl baseline)
    results.append(case(
        "J&J live   (D_M=0)        → cap 62→50, floor=M",
        dims=(65, 73, 0, 75, 95),  # H, U, M, A, N from live API
        expect_composite=50,
        expect_floor=True,
        expect_dim="M",
    ))
    results.append(case(
        "Apple live (min D_H=53)   → no cap, stays 74",
        dims=(53, 71, 77, 72, 95),
        expect_composite=74,
        expect_floor=False,
        expect_dim=None,
    ))

    # Boundary cases
    results.append(case(
        "Boundary: dim=30 exactly  → no trigger (rule is < 30)",
        dims=(30, 70, 70, 70, 70),
        expect_composite=62,  # (30+70+70+70+70)/5 = 62
        expect_floor=False,
        expect_dim=None,
    ))
    results.append(case(
        "Boundary: dim=29          → triggers, caps at 50",
        dims=(29, 70, 70, 70, 70),  # mean = 53.8 → 53
        expect_composite=50,
        expect_floor=True,
        expect_dim="H",
    ))

    # Multiple low dims — triggering_dim picks the lowest
    results.append(case(
        "Multi-low: M=5, U=10      → triggers, M is lowest",
        dims=(60, 10, 5, 60, 60),
        expect_composite=39,  # mean=39, already ≤ 50, stays 39 but floor flag fires
        expect_floor=True,
        expect_dim="M",
    ))

    # Below-cap-already case: floor signals severe dim even if mean was already low
    results.append(case(
        "Already-low: mean=45, H=20 → floor=True (signals severity)",
        dims=(20, 40, 50, 60, 55),
        expect_composite=45,  # mean=45, min(45,50)=45, no change but floor fires
        expect_floor=True,
        expect_dim="H",
    ))

    # All healthy
    results.append(case(
        "Healthy: all dims ≥ 60     → no floor",
        dims=(70, 75, 80, 65, 90),
        expect_composite=76,
        expect_floor=False,
        expect_dim=None,
    ))

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"  {passed}/{total} tests passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
