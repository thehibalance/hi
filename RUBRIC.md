# RUBRIC: Sub-Signal Audit

**Honest inventory of which sub-signal scoring ladders are grounded against external authorities, partially grounded, or editorial.**

This file accompanies the [Limitations](https://thehibalance.org/#limitations) page on thehibalance.org. For every sub-signal we ship, we declare:

- **GROUNDED** — both the data input AND the scoring ladder come from a published external authority (regulatory framework, academic standard, industry-published threshold). Our engine reproduces their methodology.
- **PARTIAL** — the data input is authoritative (regulator, certified third party) but the tier cutoffs that map data to score bands were chosen by the engine authors.
- **UNGROUNDED** — both the data input source AND the scoring ladder are editorial choices. May be defensible, but does not reproduce a published methodology.

### Curated tables, and how far they reach

Seven inputs are **hand-compiled lookup tables in the source, not live feeds**. They are accurate
for the companies they name and silent for everyone else — a company that is missing from one
receives a neutral adjustment of zero and the source is not credited in its `data_sources`. They
are listed here so nobody mistakes them for an agency pull:

| Input | Companies covered | Where it lives |
|---|---|---|
| CEO pay ratio | 44 | `PAY_RATIOS` |
| GRI reporting | 34 | `GRI_REPORTERS` |
| SBTi targets | 28 | `SBTI_STATUS` |
| BBB ratings | 27 | `BBB_RATINGS` |
| IRS 990 charity | 16 | `CHARITY_LEVELS` |
| FTC actions | 15 | `FTC_ACTIONS` |
| EEOC actions | 13 | `EEOC_DATA` |
| Insider-sale flags | 4 | `INSIDER_FLAGS` |

Spec version: **v1.6.0** · Active sub-signals: **19** · Not yet scored: **5**

**Industry constants are not evidence (v1.6.0).** Where a sub-signal's value comes from an
industry lookup table rather than from anything about the company, it no longer counts toward that
company's coverage or confidence. It still contributes to the score as a prior, and the company's
`data_sources` says `Industry`. This applies the rule `aggregate_collected.py` has enforced since
v1.4.0 to the engine's own internal defaults: H.2 craft baselines, and the A.1 and A.4 fallbacks.
The effect was 1.78 sub-signals per company, which moved published median coverage from 7/19 to a
truthful **5/19**. No score changed.

Every entry below was checked against `pipeline/scoring_engine.py` in September 2026. Where this file and the code disagree, the code is right and this file is a bug.

---

## Summary

| Status | Count | Meaning |
|---|---|---|
| GROUNDED | 0 | Data + ladder both authoritative |
| PARTIAL | 12 | Authoritative data, editorial ladder |
| UNGROUNDED | 7 | Editorial data + editorial ladder, or mostly industry defaults |
| **TOTAL ACTIVE** | **19** | |
| NOT YET SCORED | 5 | Defined in the spec, contributes nothing |

The dominant pattern is **PARTIAL**: authoritative data read through cutoffs we chose ourselves. Seven sub-signals are UNGROUNDED, and none is fully GROUNDED yet. We don't hide this — most ladders were authored by judgment during the engine build, not by reproducing a published authority. **Grounding them is the active research priority.**

**Status changes in September 2026** (from checking this file against the engine): H.1 UNGROUNDED → PARTIAL (industry medians now measured), H.2 PARTIAL → UNGROUNDED (its BLS adjustment isn't firing), U.3 UNGROUNDED → PARTIAL (now built on HRC and Disability:IN, not just Glassdoor), N.2 UNGROUNDED → PARTIAL (CDP is an authoritative input), N.5 GROUNDED → PARTIAL (its tier cutoffs were set by us, not by the SEC). **v1.5.0:** U.1 and M.1 UNGROUNDED → PARTIAL, after CFPB matching was rebuilt against the regulator's own registered-entity names and verified company by company. **v1.5.1:** M.4 PARTIAL → UNGROUNDED, after an audit found the FDA collector was scoring failed lookups as clean records.

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

**Examples** (live values, September 2026 — `curl https://api.thehibalance.org/api/v1/score/ticker/JNJ` for today's):
- J&J: `D_M = 0` (Harm Documentation penalty) → composite capped at 50
- Microsoft: `D_H = 29` (mass layoffs, AI-acceleration penalty) → composite capped at 50
- Costco: lowest dimension `D_A = 46` → no cap, composite = mean (63)
- Apple: no dimension below 42 → no cap, composite = mean (72)

**Known limitation:** this is a hard threshold. A weakest dimension of 42.1 keeps the full composite; 41.9 caps it at 50, so a fraction of a point can move the published score by ten or more. Measuring a graduated penalty is on the research list.

**Sub-signal scores < 42 do NOT trigger the floor.** Only dimension-level scores (D_H, D_U, D_M, D_A, D_N) count. Sub-signals are component inputs to the dimension score; the dimension is what matters for floor evaluation.

---

## H — Human Consciousness

### H.1 — Workforce Valuation
**Status:** PARTIAL *(was UNGROUNDED; changed in v1.3.0)*  
**Inputs:** SEC EDGAR / FMP `revenue_per_employee`, industry medians computed from the scored universe, job-board AI-vs-human hiring ratio  
**Formula:** `65 + 15·log2(industry_median / rpe)`, clamped 0–100; blended 50/50 with the job-board score when that data exists  
**Ladder:** The medians are now measured, not chosen: each is the median revenue per employee of the companies we score in that industry (`recalibrate_medians.py`), so the median company scores 65 by construction. The 65 anchor and the 15-points-per-doubling slope are editorial; the slope was chosen by testing five candidate formulas against the real distribution. Industries with fewer than 10 companies are marked provisional.  
**Path forward:** BLS QCEW × Compustat for externally cited benchmarks by sub-industry; ground the 50/50 job-board blend.

### H.2 — Craft
**Status:** UNGROUNDED *(was PARTIAL; changed September 2026)*  
**Inputs:** `craft_defaults` lookup table (in-house); BLS industry wage-vs-national adjustment (designed, not currently firing)  
**Ladder:** The BLS adjustment would be grounded, but no company's H sources include BLS today, so in practice H.2 is the in-house base table.  
**Path forward:** connect BLS wage data so the adjustment fires; DOL registered-apprenticeship density as an additional craft signal; replace the base table with a cited industry-craft framework.

### H.3 — Human Decision Depth
**Status:** UNGROUNDED  
**Inputs:** SEC EDGAR `revenue_per_employee`, headcount tier (>200k/>50k/>10k), industry bias dict, displacement signal  
**Ladder:** Editorial apart from the industry median, which is measured since v1.3.0: the `40 + (median/rpe)·30` anchor, headcount tier cutoffs, industry bias values (healthcare +10, defense +8, retail −5, tech −8, etc.), displacement coefficient.  
**Path forward:** O*NET work-context variables ("Decision Making", "Responsibility for Outcomes") aggregated to industry; OECD PIAAC non-routine task intensity; distributional headcount thresholds.

### H.5 — Human Augmentation Index
**Status:** PARTIAL  
**Inputs:** SEC `displacement_signal` (R&D-spend growth vs headcount change), job-board `ai_hiring_trend` (surging/growing/stable), USPTO patent AI ratio  
**Ladder:** Spec (`h5-augmentation-draft.md`) is rubric-grade. Engine implements only the displacement half. Augmentation half (reskilling, internal mobility, tool-building) not yet ingested.  
**Path forward:** LinkedIn Workforce Reports for internal mobility signals; Burning Glass / Lightcast skills-pipeline data.

---

## U — Understanding & Empathy

### U.1 — Customer Empathy
**Status:** PARTIAL *(was UNGROUNDED; restored in v1.5.0)*  
**Inputs:** CFPB consumer complaints over three years, normalized per 10,000 employees, for the 37 companies whose name resolves to a CFPB-registered entity; BBB complaints (10% blend); Glassdoor overall and culture ratings as fallback; neutral 50 when none exists.  
**Ladder:** Editorial, but now on a stated scale: 30 complaints per 10,000 employees scores 85, and every tenfold increase costs 15 points, clamped to [25, 85]. The constants were frozen from a dated snapshot of the 37 scoreable companies (35 to 2,643,987 per 10k) rather than computed live, so one company's score never moves because another company's data changed.  
**Path forward:** ground the scale against CFPB's own published complaint distributions instead of our snapshot; extend matching to wholly-owned subsidiaries (see the captive-finance limitation) so Ford Motor Credit can be attributed to Ford.

### U.2 — Worker Empathy
**Status:** UNGROUNDED  
**Inputs:** Glassdoor employee ratings, weighted by review count; OSHA (15% blend) and DOL (10% blend) — neither OSHA nor DOL is producing data today  
**Ladder:** Glassdoor is a commercial reporter, not an authoritative threshold system. The blend weights are editorial.  
**Path forward:** bring OSHA and DOL online; distributional anchoring for Glassdoor (industry quartiles).

### U.3 — Relational Integrity
**Status:** PARTIAL *(was UNGROUNDED; changed September 2026)*  
**Inputs:** HRC Corporate Equality Index, Disability:IN DEI Index, B Corp status, blended with the Glassdoor culture score  
**Ladder:** HRC and Disability:IN are authoritative inclusion ratings; the blend weights are editorial.  
**Path forward:** reproduce HRC's and Disability:IN's own score-to-tier mappings; ground the blend.

### U.4 — Simulated Empathy Detection
**Status:** PARTIAL  
**Inputs:** Algorithmic Harm Index (AHI™) computation from incident database (ACLU, AlgorithmWatch, Brookings, FTC settlements)  
**Ladder:** Editorial. AHI 0-25 = no impact, 25-50 = moderate, 50+ = severe. Blast-radius weighting (millions vs thousands affected) is editorial.  
**Path forward:** AlgorithmWatch publishes harm tier classifications that could replace internal cutoffs.

---

## M — Moral & Ethical Conduct

### M.1 — Pricing Ethics
**Status:** PARTIAL *(was UNGROUNDED; restored in v1.5.0)*  
**Inputs:** CFPB complaint volume (see U.1), capped so the same evidence never scores higher here than on U.1; FTC pricing actions, state AG settlements, predatory pricing dictionary. Companies with no CFPB record score a neutral 50  
**Ladder:** Editorial. Settlement >$10M flagged "material"; >$100M = "major." These are not derived from SEC materiality framework.  
**Path forward:** SEC materiality thresholds (typically 5% of revenue) could ground "material" vs "incidental."

### M.2 — Data Ethics
**Status:** PARTIAL  
**Inputs:** Have I Been Pwned breach records **matched by exact domain since v1.4.0** (the old name-fragment matching attributed other sites' breaches to the wrong company and was withdrawn), FTC privacy enforcement, state AG breach notifications. No known breach is not scored as good practice; it earns no credit. Companies with no domain on file can't be checked  
**Ladder:** Editorial. <100K records = 80 pts; <1M = 60; <10M = 40; >10M = 20.  
**Path forward:** California CCPA + EU GDPR define "material" breach thresholds. Mapping to those would ground.

### M.3 — Market Ethics
**Status:** PARTIAL  
**Inputs:** SEC litigation and EPA penalties (legal score), blended with certification signals when present (60% certifications, 40% legal); EEOC, pay-ratio (DEF 14A) and insider-trading (Form 4) adjustments  
**Ladder:** Editorial. The legal-penalty dollar tiers ($1B / $100M / $10M / $1M) and the certification blend weights are in-house.  
**Path forward:** DOJ/FTC publish their own severity classifications for enforcement actions.

### M.4 — Product Ethics
**Status:** UNGROUNDED *(was PARTIAL; changed in v1.5.1 when FDA was withdrawn)*  
**Inputs:** CPSC SaferProducts recalls (integrated, not yet producing data); Glassdoor management and compensation ratings as fallback. **FDA is withdrawn** — an audit found 1,041 of 1,422 collected rows scoring 85 because openFDA returns 404 when nothing matches and the collector recorded that as "no recalls", and 228 more scoring 25 because an empty company name searches as a wildcard.  
**Ladder:** Editorial while FDA is out: the score rests on employee ratings, which are not a measure of product safety.  
**Path forward:** rebuild the FDA collector on the v1.5.0 pattern — refuse an empty name or ticker, never convert a miss into evidence, read the true count from `meta.results.total`, verify the returned `recalling_firm` against the company, and query food and device enforcement as well as drug. Then bring CPSC online and add NHTSA.

### M.5 — Stakeholder Governance
**Status:** PARTIAL  
**Inputs:** stakeholder-centric legal structure (B Corp and similar signals); FEC political spending when available; Glassdoor CEO rating as a last fallback  
**Ladder:** B Corp status is authoritative; the FEC spending tiers and the Glassdoor fallback are editorial. Since v1.4.0 FEC counts only when committees are actually found for that company — "none found" used to be scored as clean political conduct. Harm Documentation (settlements, attributed deaths, concealment) penalizes M.3 and M.4 directly; it is not an M.5 input.  
**Path forward:** political-spending thresholds per $B of revenue; retire the Glassdoor fallback.

---

## A — Alive & Environmental

### A.1 — Energy & Emissions
**Status:** UNGROUNDED  
**Inputs:** CDP Climate disclosures (when available), industry-default emissions intensity table  
**Ladder:** CDP disclosure letter grades exist but engine doesn't reproduce them. Industry defaults are in-house.  
**Path forward:** SBTi alignment status (1.5°C / well below 2°C / committed / not committed); reproduce CDP tier scoring.

### A.2 — Water
**Status:** UNGROUNDED  
**Inputs:** CDP Water disclosures (when available); neutral 50 otherwise  
**Ladder:** CDP water scores are mapped by an in-house translation. EPA violations feed A.3, not A.2.  
**Path forward:** reproduce CDP's water tiers; add a water source that covers companies outside CDP.

### A.3 — Land & Habitat
**Status:** UNGROUNDED  
**Inputs:** USDA Organic certification (70%) with sector land-use risk (30%); EPA violation counts when neither is available  
**Ladder:** Sector risk weights and the EPA violation tiers (0 / 3 / 10 / 20) are editorial.  
**Path forward:** Forest 500 publishes a methodology that could ground the ladder.

### A.4 — Product Lifecycle
**Status:** PARTIAL *(for 15 covered companies)*  
**Inputs:** iFixit repairability scores (consumer electronics, ~15 companies)  
**Ladder:** Reproduces iFixit's 1-10 repairability tiers, scaled to 0-100. Grounded for covered companies.  
**Coverage gap:** every other company falls back to certifications, then CDP Forests, then an industry default. Path forward: EU Extended Producer Responsibility datasets.

---

## N — Natural Transparency

### N.2 — Reporting Quality
**Status:** PARTIAL *(was UNGROUNDED; changed September 2026)*  
**Inputs:** reporting-quality level (excellent / good / partial) from CDP disclosure; CDP non-responders receive a mild penalty; neutral 50 otherwise  
**Ladder:** The mapping from reporting level to score (90 / 70 / 45 / 25) is editorial.  
**Path forward:** GRI publishes its own reporting quality scoring framework. Reproducing it would ground this.

### N.5 — Filing Volume
**Status:** PARTIAL *(was GROUNDED; changed September 2026)*  
**Inputs:** SEC EDGAR filing counts and timeliness (on-time material disclosure)  
**Ladder:** The filing data is SEC's own, but the tier cutoffs (8 / 5 / 3 / 1 filings → 90 / 75 / 60 / 40 / 20) are editorial.  
**Path forward:** Derive the tiers from the distribution of filing counts across all SEC registrants, or from SEC's timeliness rules directly.

---

## Not yet scored

These 5 sub-signals are defined in the spec but not yet scored. They contribute nothing to any score.

| ID | Name | Why not yet |
|---|---|---|
| H.4 | CEO Accountability | Removed in v1.0.2; the pay-ratio adjustment moved to M.3. Re-introduction awaits a cited "human contribution to value" framework. |
| U.5 | Moral Courage | Removed in v1.0.2; charity-pipeline data was unreliable. Re-introduction awaits multi-year customer and community engagement data. |
| N.1 | AI Disclosure | Defined in the spec; data source and scoring ladder not yet built. |
| N.3 | Labor Auditability | Defined in the spec; data source and scoring ladder not yet built. |
| N.4 | Humanwashing Detection | Humanwashing is detected and flagged today; making it a scored sub-signal awaits a rubric. |
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

*Last updated: September 2026. Spec v1.6.0 (industry constants no longer count as evidence; median coverage 5/19). Maintained by Morf Innovations LLC. Apache 2.0 licensed.*
