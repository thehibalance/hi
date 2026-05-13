# RUBRIC: Sub-Signal Audit

**Honest inventory of which sub-signal scoring ladders are grounded against external authorities, partially grounded, or editorial.**

This file accompanies the [Limitations](https://thehibalance.org/#limitations) page on thehibalance.org. For every sub-signal we ship, we declare:

- **GROUNDED** — both the data input AND the scoring ladder come from a published external authority (regulatory framework, academic standard, industry-published threshold). Our engine reproduces their methodology.
- **PARTIAL** — the data input is authoritative (regulator, certified third party) but the tier cutoffs that map data to score bands were chosen by the engine authors.
- **UNGROUNDED** — both the data input source AND the scoring ladder are editorial choices. May be defensible, but does not reproduce a published methodology.

Spec version: **v1.2.1** · Active sub-signals: **19** · Deferred: **5**

---

## Summary

| Status | Count | Meaning |
|---|---|---|
| GROUNDED | 1 | Data + ladder both authoritative |
| PARTIAL | 10 | Authoritative data, editorial ladder |
| UNGROUNDED | 8 | Editorial data + editorial ladder |
| **TOTAL ACTIVE** | **19** | |
| DEFERRED (v1.3 target) | 5 | Spec'd but not yet scored |

The dominant pattern is **UNGROUNDED**. We don't hide this — most sub-signal ladders were authored by intuition during the engine build, not by reproducing a published authority. **Grounding these ladders is the active research priority for v1.3 and beyond.**

---

## Composite Floor Rule (v1.2.1)

The composite score is the simple mean of the five HUMAN dimensions, with **one floor rule**:

> **If any HUMAN dimension scores below 42, the composite is capped at 50.**

This protects against severe single-dimension failure being averaged away by strong scores in other dimensions. A company cannot earn a composite above 50 if even one HUMAN dimension is in critical failure (< 42), regardless of how the other four perform.

When the floor fires:
- `composite` is capped at 50 (or kept at the natural mean if already ≤ 50)
- `floor_triggered: true` in the API response
- `triggering_dimension` indicates which dimension caused the cap (H/U/M/A/N)

This rule replaces a multi-tier floor system used in earlier specs (any dim < 10 → 40 / 1 dim < 42 → 49 / 2+ dims < 42 → 41), simplified to one clear, defensible threshold.

**Examples:**
- J&J: `D_M = 0` (Harm Documentation penalty) → composite capped at 50
- Costco: `D_N = 27` (CDP grade D + thin SEC filings) → composite capped at 50
- Microsoft: `D_H = 35` (mass layoffs, AI-acceleration penalty) → composite capped at 50
- Apple: min dim `D_H = 50` → no cap, composite = mean (73)

**Sub-signal scores < 42 do NOT trigger the floor.** Only dimension-level scores (D_H, D_U, D_M, D_A, D_N) count. Sub-signals are component inputs to the dimension score; the dimension is what matters for floor evaluation.

---

## H — Human Consciousness

### H.1 — Workforce Valuation
**Status:** UNGROUNDED  
**Inputs:** SEC EDGAR `revenue_per_employee`, hardcoded `INDUSTRY_RPE_MEDIANS` dict, job-board AI-vs-human hiring ratio  
**Ladder:** Editorial. The 12-entry industry RPE median dict ($500k tech, $200k retail, $1.5M energy) was chosen in-house. The `·65` anchor and the 50/50 RPE-vs-job-board blend have no cited source.  
**Path forward:** BLS QCEW × Compustat for cited RPE benchmarks by GICS sub-industry; Damodaran NYU datasets; distributional anchors (P50/P75) instead of editorial multipliers.

### H.2 — Craft
**Status:** PARTIAL  
**Inputs:** BLS industry wage data (cited), `craft_defaults` lookup table (in-house)  
**Ladder:** BLS wage-vs-national adjustment is grounded. The `craft_defaults` base table that adjusts for industry craft intensity is intuition-based.  
**Path forward:** DOL registered-apprenticeship density as additional craft signal; replace base table with cited industry-craft framework.

### H.3 — Human Decision Depth
**Status:** UNGROUNDED  
**Inputs:** SEC EDGAR `revenue_per_employee`, headcount tier (>200k/>50k/>10k), industry bias dict, displacement signal  
**Ladder:** Every component editorial: the `40 + (median/rpe)·30` anchor, headcount tier cutoffs, industry bias values (healthcare +10, defense +8, retail −5, tech −8, etc.), displacement coefficient.  
**Path forward:** O*NET work-context variables ("Decision Making", "Responsibility for Outcomes") aggregated to industry; OECD PIAAC non-routine task intensity; distributional headcount thresholds.

### H.5 — Human Augmentation Index
**Status:** PARTIAL  
**Inputs:** SEC `displacement_signal` (R&D-spend growth vs headcount change), job-board `ai_hiring_trend` (surging/growing/stable), USPTO patent AI ratio  
**Ladder:** Spec (`h5-augmentation-draft.md`) is rubric-grade. Engine implements only the displacement half. Augmentation half (reskilling, internal mobility, tool-building) not yet ingested.  
**Path forward:** LinkedIn Workforce Reports for internal mobility signals; Burning Glass / Lightcast skills-pipeline data.

---

## U — Understanding & Empathy

### U.1 — Customer Empathy
**Status:** PARTIAL  
**Inputs:** CFPB consumer complaints (financial services), BBB complaints, FTC enforcement actions  
**Ladder:** CFPB is an authoritative source. The complaints-per-$B-revenue tier cutoffs (<100 = 85 pts, <500 = 70 pts, <2000 = 55 pts) are editorial.  
**Coverage gap:** CFPB regulates financial services. ~80% of scored companies fall back to BBB/FTC inputs only.  
**Path forward:** CFPB published complaint distribution percentiles; per-sector regulators (FCC for telecom, FDA for pharma, NHTSA for auto).

### U.2 — Worker Empathy
**Status:** UNGROUNDED  
**Inputs:** Glassdoor employee ratings, Disability:IN DEI Index, HRC Corporate Equality Index  
**Ladder:** Glassdoor is a commercial reporter, not an authoritative threshold system. The 50/50 blend across the three sources is arbitrary.  
**Path forward:** HRC and Disability:IN both publish their own scoring rubrics — reproducing their score-to-tier mappings would ground this. Glassdoor needs distributional anchoring (industry quartiles).

### U.3 — Relational Integrity
**Status:** UNGROUNDED  
**Inputs:** Raw Glassdoor culture sub-score, passed through  
**Ladder:** No cited rationale for choosing the culture sub-score over other Glassdoor dimensions; no industry adjustment.  
**Path forward:** Candidate for replacement with a published satisfaction-stability metric (J.D. Power, ACSI). Or grounding in a defined "relational integrity" framework from organizational research.

### U.4 — Simulated Empathy Detection
**Status:** PARTIAL  
**Inputs:** Algorithmic Harm Index (AHI) computation from incident database (ACLU, AlgorithmWatch, Brookings, FTC settlements)  
**Ladder:** Editorial. AHI 0-25 = no impact, 25-50 = moderate, 50+ = severe. Blast-radius weighting (millions vs thousands affected) is editorial.  
**Path forward:** AlgorithmWatch publishes harm tier classifications that could replace internal cutoffs.

---

## M — Moral & Ethical Conduct

### M.1 — Pricing Ethics
**Status:** PARTIAL  
**Inputs:** CFPB pricing complaints, FTC pricing actions, state AG settlements, predatory pricing dictionary  
**Ladder:** Editorial. Settlement >$10M flagged "material"; >$100M = "major." These are not derived from SEC materiality framework.  
**Path forward:** SEC materiality thresholds (typically 5% of revenue) could ground "material" vs "incidental."

### M.2 — Data Ethics
**Status:** PARTIAL  
**Inputs:** Have I Been Pwned breach records, FTC privacy enforcement, state AG breach notifications  
**Ladder:** Editorial. <100K records = 80 pts; <1M = 60; <10M = 40; >10M = 20.  
**Path forward:** California CCPA + EU GDPR define "material" breach thresholds. Mapping to those would ground.

### M.3 — Market Ethics
**Status:** PARTIAL  
**Inputs:** SEC enforcement actions, DOJ antitrust cases, FEC/OpenSecrets political donations, FTC market actions  
**Ladder:** Editorial. Sherman Act violations weighted heavier than minor SEC enforcement; political donation concentration > $10M flagged.  
**Path forward:** DOJ/FTC publish their own severity classifications for enforcement actions.

### M.4 — Product Ethics
**Status:** PARTIAL  
**Inputs:** CPSC SaferProducts recalls, NHTSA recalls, FDA recalls, Product Harm Index dictionary  
**Ladder:** Recall classification (Class I/II/III) is authoritative; mapping to score bands is editorial.  
**Path forward:** Reproduce CPSC recall severity tiers exactly.

### M.5 — Stakeholder Governance
**Status:** PARTIAL  
**Inputs:** Major Harm Events dictionary (court settlements, attributed deaths, knowing concealment, weapons), DOJ/SEC/state AG records  
**Ladder:** Penalty magnitudes calibrated against documented attribution (court findings, settlement amounts). Direction grounded; magnitudes editorial.  
**Path forward:** Pre-2020 historical harm coverage is incomplete — backfilling from EPA Superfund + state AG databases planned.

---

## A — Alive & Environmental

### A.1 — Energy & Emissions
**Status:** UNGROUNDED  
**Inputs:** CDP Climate disclosures (when available), industry-default emissions intensity table  
**Ladder:** CDP disclosure letter grades exist but engine doesn't reproduce them. Industry defaults are in-house.  
**Path forward:** SBTi alignment status (1.5°C / well below 2°C / committed / not committed); reproduce CDP tier scoring.

### A.2 — Water
**Status:** UNGROUNDED  
**Inputs:** EPA ECHO violations, CDP Water disclosures (when available)  
**Ladder:** EPA classifies violations (HPV — High Priority Violation) but engine ladder doesn't reproduce that classification.  
**Path forward:** Map directly to EPA's HPV tier classification.

### A.3 — Land & Habitat
**Status:** UNGROUNDED  
**Inputs:** CDP Forests disclosures (when available), industry deforestation risk dictionary  
**Ladder:** Forest commitment composite from CDP + sector risk weights, both editorial.  
**Path forward:** Forest 500 publishes a methodology that could ground the ladder.

### A.4 — Product Lifecycle
**Status:** PARTIAL *(for 15 covered companies)*  
**Inputs:** iFixit repairability scores (consumer electronics, ~15 companies)  
**Ladder:** Reproduces iFixit's 1-10 repairability tiers, scaled to 0-100. Grounded for covered companies.  
**Coverage gap:** ~426+ companies fall back to industry default. Path forward: EU Extended Producer Responsibility datasets.

---

## N — Natural Transparency

### N.2 — Reporting Quality
**Status:** UNGROUNDED  
**Inputs:** SEC EDGAR filing count (10-K, 8-K, DEF 14A, Form 4) over trailing 12 months  
**Ladder:** Filing volume is authoritative input but editorial mapping to "high quality" vs "low quality" reporting.  
**Path forward:** GRI publishes its own reporting quality scoring framework. Reproducing it would ground this.

### N.5 — Filing Volume
**Status:** GROUNDED  
**Inputs:** SEC EDGAR filing counts and timeliness (on-time material disclosure)  
**Ladder:** Reproduces SEC's own materiality + timeliness framework. Companies with consistent on-time material disclosure rank highest.  
**Notes:** Currently the only fully grounded sub-signal in v1.2.0.

---

## Deferred to v1.3

These 5 sub-signals are spec'd in HUMAN Grade Spec v1.2.0 but not yet scored. They will be added in v1.3. Until then, they receive no contribution to dimension scores.

| ID | Why deferred |
|---|---|
| H.4 | Removed in v1.0.2; pay-ratio adjustment moved to M.3. Re-introduction awaits cited "human contribution to value" framework. |
| U.5 | Removed in v1.0.2; charity-pipeline data was unreliable. Re-introduction awaits multi-year customer/community engagement data. |
| N.1 | Narrative Integrity — removed in v1.0.2. Re-introduction awaits cited reporting-narrative framework. |
| N.3 | Stakeholder Engagement — removed in v1.0.2. Re-introduction awaits structured stakeholder dataset. |
| N.4 | Narrative Courage — removed in v1.0.2. Deceptive-practices signal deferred to Pass 3 rubric authoring. |

---

## What this document is NOT

- It is **not** a defense of the editorial choices. Where the ladder is editorial, we say so.
- It is **not** a roadmap commitment. Path-forward notes are research directions, not promises.
- It is **not** a substitute for the methodology. Read [thehibalance.org methodology](https://thehibalance.org/#methodology) for how dimensions and the composite score are computed.
- It is **not** an implication that PARTIAL or UNGROUNDED sub-signals are wrong. They reflect public data inputs interpreted with reasonable cutoffs. They are simply not yet reproduced from a published authority.

---

## How to challenge a ladder

If you believe a specific sub-signal ladder is mis-calibrated:

1. Open an issue: [github.com/thehibalance/hi/issues/new](https://github.com/thehibalance/hi/issues/new) with label `ladder-grounding`
2. Cite the published authority you believe should ground the cutoffs
3. Propose the mapping (e.g., "B Corp publishes 80-quintile cutoffs; our ladder should reproduce them")

We respond to ladder-grounding issues within 5 business days.

---

*Last updated: April 2026. Spec v1.2.0. Maintained by Morf Innovations LLC. Apache 2.0 licensed.*
