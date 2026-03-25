# HUMAN Grade Methodology — Session 4 Updates
## Changes to incorporate into Methodology Spec v1.1 and Whitepaper Eighth Edition

**Date:** March 25, 2026
**Author:** Project Anakin Session 4
**Status:** Ready for incorporation

---

## 1. Gold HI Grade — 3-Gate System (replaces 10-gate system)

### Previous (v1.0)
10 gates across 3 categories: Score (1 gate), Balance (1 gate), 8 HUMAN Features (8 gates).

### Updated (v1.1)
3 gates. Three categories. The data decides.

**Gate 1 — SCORE:** Composite ≥ adaptive threshold (mean + 2σ of all scored companies, recalculated quarterly). Two failsafes: hard floor (never below 55) and ratchet (can only go up, never down). Threshold rounded to whole number.

**Gate 2 — BALANCE:** All 5 HUMAN dimensions ≥ 42. Any dimension below 42 = not balanced. No exceptions. 42 is the answer to life, the universe, and everything.

**Gate 3 — HONESTY:** Two checks, both must pass:
- No Humanwashing™ flags (HUMAN Watermark is clean)
- Algorithmic Harm Index™ score < 30 (company's algorithms are not dividing, addicting, or manipulating people)

### Rationale
The 7 removed gates (decay, shield, ESG washing, contagion, genome, pressure, alerts) remain as **features that inform the score** — they are data systems, not gatekeepers. A company in heavy decay will naturally lose Gold through the score dropping below threshold (Gate 1), not through a separate gate. This simplification makes Gold HI Grade explainable in one sentence: "Score, balance, and honesty."

### Spec Language
Replace Section 2.3 (Tier Classification) with:

> **2.3 Score-Only Classification**
>
> Every company receives a composite score from 0 to 100. There are no letter grades and no tier labels. The score is color-coded: green (≥ Gold threshold), amber (≥ 42), red (< 42).
>
> **2.3.1 Gold HI Grade**
>
> Gold HI Grade is earned by passing all 3 gates:
>
> Gate 1 (Score): composite ≥ adaptive_threshold
> Gate 2 (Balance): min(D_H, D_U, D_M, D_A, D_N) ≥ 42
> Gate 3 (Honesty): humanwashing_flags = 0 AND algorithmic_harm_score < 30
>
> Gold HI Grade is not purchased. It is not applied for. The data proves it.

---

## 2. Algorithmic Harm Index™ — Incorporated into Gate 3

### Previous
The Algorithmic Harm Index was a cross-cutting penalty applied to H, U, M, and N dimensions. It was informational and not connected to Gold HI Grade status.

### Updated
The AHI now serves dual purpose:
1. Cross-cutting penalty on dimensions (unchanged)
2. Gate 3 component: AHI score ≥ 30 blocks Gold HI Grade

### AHI Scoring (unchanged from whitepaper)
Five factors, each 0–100:
- **Division** — Does the algorithm amplify outrage, tribalism, or polarization?
- **Addiction** — Does the product use dopamine loops, infinite scroll, dark patterns?
- **Manipulation** — Does the algorithm exploit vulnerable users?
- **Transparency** — Does the company disclose how its algorithms work?
- **Human Override** — Can users opt out, adjust, or control the algorithm?

Composite AHI = weighted average of five factors. Penalties applied to H, U, M, N when AHI > 30. Maximum penalty per dimension: -15 points at AHI = 100.

### Gate 3 Integration
```
honesty_gate = (humanwashing_flags == 0) AND (algorithmic_harm_score < 30)
```

### Seed Data
41 companies now carry `algorithmic_harm_score` in the seed database. 11 companies fail Gate 3 on AHI alone: Meta (72), TikTok (68), X/Twitter (58), Palantir (55), Google (52), Snap (45), Amazon (45), UnitedHealth (42), Uber (40), Netflix (32), Spotify (30).

---

## 3. H.5 — AI Displacement & Augmentation Trajectory

### Previous
H.5 measured only displacement: `displacement_signal = ai_invest_delta - headcount_delta`. One-directional penalty — no reward for augmenting well.

### Updated
H.5 becomes bidirectional. Same weight (0.20), same sub-signal slot, backward compatible.

**Component A: Displacement Signal (unchanged)**
```
headcount_delta = (headcount_current - headcount_prior) / headcount_prior
ai_invest_delta = (ai_capex_current - ai_capex_prior) / ai_capex_prior
displacement_signal = ai_invest_delta - headcount_delta
base_score = clamp(100 - (displacement_signal × 100), 0, 100)
```

**Component B: Augmentation Signal (new)**
```
augmentation_signal = (
    0.30 × ai_training_investment_score +
    0.30 × copilot_deployment_ratio +
    0.20 × no_displacement_commitment +
    0.20 × redeployment_rate
)
augmentation_bonus = augmentation_signal × 0.20
```

**Combined:**
```
S_H5 = clamp(base_score + augmentation_bonus, 0, 100)
```

Maximum bonus: +20 points on H.5. Maximum composite impact: ~0.8 points. Companies without augmentation data score identically to today (bonus defaults to 0).

### Four Augmentation Indicators

| Indicator | Source | Measures |
|-----------|--------|----------|
| AI Training Investment | SEC 10-K, press releases, job postings | Proportion of AI budget for upskilling existing employees |
| Copilot Deployment Ratio | Job postings, product disclosures | Ratio of AI tools deployed as human-assistive vs. autonomous |
| No-Displacement Commitment | Public commitments, SEC filings | Public, verifiable commitment that AI won't cause net workforce reduction |
| Redeployment Rate | SEC 10-K, WARN Act cross-reference | Proportion of automated-role workers redeployed vs. terminated |

### Spec Language
Replace H.5 description in Section 3.3 sub-signal table:

> H.5 | AI Displacement & Augmentation | 0.20 | SEC filings, job postings, press releases | See Section 3.4

Replace Section 3.4 with expanded formula including both components.

---

## 4. Subsidiary Transparency Rule (STR)

### New Addition
Addresses Supply Chain Laundering (Section 8.4.7 of the whitepaper). Companies cannot earn high scores by moving low-scoring operations into separate legal entities.

### Rule
```
subsidiary_delta = parent_composite - weighted_avg(subsidiary_composites)

IF subsidiary_delta > 20 AND subsidiaries_coverage >= 30%:
    penalty = min(subsidiary_delta × 0.25, 15)
    adjusted_composite = parent_composite - penalty
```

### Parameters
- Delta threshold: 20 points (prevents false positives from normal diversification)
- Coverage threshold: 30% of known subsidiaries/contractors must be scored
- Penalty rate: 0.25 (25% of delta above threshold)
- Maximum penalty: 15 points (aligned with MSSI from Data Integrity Firewall)

### Subsidiary Identification Sources
- SEC EDGAR Exhibit 21 (legally required list of subsidiaries)
- Corporate structure databases
- Press releases (outsourcing announcements)
- Job postings under subsidiary names

### Interaction with Existing Systems
- STR adjusts composite **before** Gate 1 is evaluated
- Applied **after** floor rule
- Complements CES (Contagion Effect Score) — CES measures full supply chain, STR targets majority-owned entities

### Implementation
Phase 1 (now): Add STR logic to scoring engine. Use SEC Exhibit 21 for public companies.
Phase 2 (Q3 2026): Expand to contractor relationships from job posting analysis.
Phase 3 (Q4 2026): Community-submitted subsidiary relationships with Data Integrity Firewall verification.

### Spec Language
Add new Section 10.5 (Subsidiary Transparency Rule) after Industry Normalization:

> **10.5 Subsidiary Transparency Rule**
>
> A company's composite score is adjusted downward when its known subsidiaries, contractors, or majority-owned entities score significantly lower than the parent. This prevents Supply Chain Laundering — the practice of moving low-scoring operations into separate legal entities to artificially inflate the parent's HUMAN Grade.
>
> [Include full formula and parameters]

---

## 5. 3-Layer Data Validation System

### New Addition
Pipeline now includes automated validation that blocks bad data from going live.

### Layer 1: Input Validation
Runs before scoring. Checks:
- Dimension scores 0–100 (rejects negative, >100)
- Headcount non-negative, < 3M
- Revenue per employee < $50M
- Glassdoor rating 1.0–5.0
- AI hiring ratio 0.0–1.0
- Composite matches dimensions (±2 tolerance)
- Subsignal files: no NaN, no Infinity, all 0–100

### Layer 2: Output Validation
Runs after scoring, before publishing. Checks:
- Minimum company count (≥ 100)
- Score distribution shape (standard deviation > 1.0)
- Gold company percentage (< 15%)
- Comparison with previous run (flag any company moving > 15 points)
- Individual dimension swings (flag > 25 point moves)
- Sanity checks (known ethical leaders > 30, known problematic < 85)
- Missing companies from previous run

### Layer 3: Source Cross-Referencing (MSSI)
Enforces Maximum Single-Source Impact rule from Data Integrity Firewall (Section 24.2):
- No single data source can move any sub-signal > 15 points
- Material changes require corroboration from ≥ 2 independent source categories
- Subsignal-level comparison against previous run
- Flags uncorroborated extreme scores (> 20 points from 50 with single source)

### Pipeline Integration
```python
from validate_pipeline import validate_all
report = validate_all(data_dir="data")
if report.critical:
    sys.exit(1)  # Scores NOT published
```

### Spec Language
Add new Section 24.9 (Automated Validation) to Data Integrity Firewall:

> **24.9 Automated Validation**
>
> Conforming implementations must run a 3-layer validation system before publishing any score update. Layer 1 validates inputs before scoring. Layer 2 validates outputs before publishing. Layer 3 enforces the MSSI rule at the sub-signal level. The pipeline blocks if any critical issue is detected. Validation reports are retained for a minimum of 7 years alongside the audit trail (Section 24.4).

---

## 6. Seed Database Updates

### Changes
- 41 companies now carry `algorithmic_harm_score` field
- 25 companies have `subsidiaries` arrays mapped
- 9 companies have `primary_contractors` arrays mapped
- 38 companies have improved `notes` with specific citations
- Header updated: "The Nahum Foundation" → "The HI Balance"

### New Fields in Company Record
```json
{
  "algorithmic_harm_score": 72,
  "subsidiaries": ["Instagram", "WhatsApp", "Reality Labs"],
  "primary_contractors": ["Accenture (content moderation)", "Cognizant (content moderation)"]
}
```

---

## 7. Movement Language

### Three Lines
1. We're not anti-AI. We're pro-balance.
2. Brands that empower humans score well. Brands that replace, divide, or addict them score poorly.
3. **We reward companies that use AI to empower their people.** (NEW)

### Where It Appears
- About page (website)
- Whitepaper (Part I: Origin)
- README
- Extension panel (implicit in augmentation bonus)

---

## 8. Foundation Name

### Change
All references to "The Nahum Foundation" and "The Deep Thought Foundation" → **The HI Balance**

Affects: Methodology Spec, Whitepaper, IP Filing Package, Provisional Patent (note: patent references are locked at filing date — this change applies to all post-filing documents only).

---

## 9. Trademark Updates

### All Three TMs Now Filed
| Mark | Status |
|------|--------|
| HI Grade™ | Filed |
| Humanwashing™ | Filed |
| Algorithmic Harm Index™ | Filed |

### Where TMs Appear
Gate 3 description, About page, Footer, README, all formal documents.

---

## 10. Score-Only Display System

### Previous
Letter grades: HI Certified, A, B, C, F with score ranges.

### Updated
Score only: every company gets a number 0–100. No letters. No tiers. Color-coded:
- Green (≥ Gold threshold): in Gold territory
- Amber (≥ 42): balanced but not Gold
- Red (< 42): out of balance

Gold HI Grade is the only named classification. It's earned through the 3 gates, not through a score range.

---

## Documents Requiring Update

| Document | Sections Affected |
|----------|------------------|
| **HUMAN Grade Methodology Spec v1.0** | §2.3 (tiers → score-only), §3.4 (H.5 augmentation), §9 (humanwashing → add AHI reference), §10 (add STR), §24 (add automated validation) |
| **Whitepaper (Seventh → Eighth Edition)** | Part II §2.3 (3 gates), Part III §3.1 (H.5), Part IV (AHI in Gate 3), Part V (Humanwashing™), Part VI (10 features → clarify features vs gates), Part VIII (score-only display) |
| **IP Filing Package** | Update claims language to reflect 3-gate system, add STR claim, add validation claim |
| **Provisional Patent** | Note: priority date locked. Changes for non-provisional filing (March 2027) |
| **README** | ✅ Done |
| **Website (index.html)** | ✅ Done |
| **Extension (engine.js, content.js)** | ✅ Done |
| **API Server (api_server.py)** | ✅ Done |
| **Seed Database (seed-data.js)** | ✅ Done |
| **Pipeline Validator (validate_pipeline.py)** | ✅ New |

---

*Patent Pending · Morf Innovations LLC · The HI Balance · thehibalance.org*
