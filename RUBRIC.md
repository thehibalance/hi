# RUBRIC: Sub-Signal Audit

**Honest inventory of which sub-signal scoring ladders are grounded against external authorities, partially grounded, or editorial.**

This file accompanies the [Limitations](https://thehibalance.org/limitations) page on thehibalance.org. It is the technical backbone of the disclosure — for every sub-signal we ship, we declare:

- **GROUNDED** — both the data input AND the scoring ladder come from a published external authority (regulatory framework, peer-reviewed research, industry standard). We've reproduced their methodology.
- **PARTIAL** — the data input is authoritative (regulator, certified third party) but the tier cutoffs that map data to score bands were chosen by the engine authors.
- **UNGROUNDED** — both the data input AND the scoring ladder are editorial. May be defensible, but does not reproduce a published methodology.

Spec version: **v1.1.0** · Active sub-signals: **18** · Deferred to v1.2: **7**

---

## Summary

| Status | Count | Meaning |
|---|---|---|
| GROUNDED | 3 | Data + ladder both authoritative |
| PARTIAL | 13 | Authoritative data, editorial ladder |
| UNGROUNDED | 2 | Editorial data + editorial ladder |
| **TOTAL ACTIVE** | **18** | |
| DEFERRED | 7 | Spec'd but not yet scored (v1.2 target) |
| **TOTAL SPEC** | **25** | |

The dominant pattern is **PARTIAL**: we use authoritative inputs (SEC EDGAR, CFPB, OSHA, EPA, BLS) but draw the score-band cutoffs ourselves. Grounding these against published industry distributions (B Corp quintiles, BLS percentiles, CFPB published baselines) is the priority for v1.2.

---

## H — Human Consciousness

### H.1 — Workforce Investment
**Status:** PARTIAL  
**Inputs:** SEC 10-K headcount, IRS 990 compensation tables, BLS Industry Wages, Glassdoor pay ratings  
**Ladder:** Editorial. Tier cutoffs chosen by engine authors based on observed distribution of scored companies.  
**Path forward:** BLS publishes industry-specific wage percentiles. Mapping ladder cutoffs to BLS quartiles would ground the ladder.

### H.2 — Headcount Stability
**Status:** PARTIAL  
**Inputs:** SEC 10-K year-over-year headcount, WARN Act notices, layoffs.fyi  
**Ladder:** Editorial. -5% YoY change is "significant reduction"; +5% is "growing." These cutoffs are not derived from labor economics literature.  
**Path forward:** Reference BLS JOLTS turnover rates by industry to set "normal" vs. "abnormal" reduction bands.

### H.3 — Revenue Per Employee
**Status:** PARTIAL  
**Inputs:** SEC 10-K revenue / headcount; industry RPE medians (currently hardcoded constants)  
**Ladder:** Editorial. RPE > $2M flagged as "very high — suggests heavy automation" is an editorial threshold.  
**Path forward:** Industry-relative RPE percentiles from live universe (currently snapshot Q1 2025).

---

## U — Understanding & Empathy

### U.1 — Customer Empathy
**Status:** PARTIAL  
**Inputs:** CFPB complaints (financial services only), BBB complaints, FTC enforcement actions, NHTSA recalls  
**Ladder:** Editorial. <100 complaints/$B = 85, <500 = 70, <2000 = 55. Not derived from CFPB published distributions.  
**Coverage gap:** ~80% of scored companies are not in financial services. They fall back to BBB/FTC inputs only. Path forward: per-sector complaint regulators (CFPB for finance, FCC for telecom, FDA for pharma, NHTSA for auto).

### U.2 — Worker Empathy
**Status:** PARTIAL  
**Inputs:** Glassdoor employee ratings, Disability:IN DEI Index, HRC Corporate Equality Index  
**Ladder:** Editorial blend across three sources. Glassdoor 4.0+ = "employees feel valued"; HRC 80+ = "strong inclusion."  
**Path forward:** HRC and Disability:IN both publish their own scoring rubrics. Reproducing their score → tier mapping would ground this.

### U.3 — Customer Satisfaction Stability
**Status:** UNGROUNDED  
**Inputs:** Editorial — composite of complaint trend + Glassdoor trend  
**Ladder:** Editorial. Both data and ladder are internally constructed.  
**Path forward:** This sub-signal is a candidate for replacement with a published satisfaction stability metric (J.D. Power, ACSI).

### U.4 — Algorithmic Harm Index Impact
**Status:** PARTIAL  
**Inputs:** Internal AHI computation from incident database (ACLU, AlgorithmWatch, Brookings, FTC settlements)  
**Ladder:** Editorial. AHI 0-25 = no impact; 25-50 = moderate; 50+ = severe. Blast radius weighting (millions affected vs. thousands) editorial.  
**Path forward:** AlgorithmWatch publishes harm tier classifications that could replace internal cutoffs.

---

## M — Moral & Ethical Conduct

### M.1 — Pricing Ethics
**Status:** PARTIAL  
**Inputs:** CFPB pricing complaints, FTC pricing actions, state AG settlements, predatory pricing dictionary  
**Ladder:** Editorial. Settlement >$10M flagged as "material"; >$100M as "major."  
**Path forward:** SEC materiality thresholds (typically 5% of revenue) could ground "material" vs "incidental."

### M.2 — Data Ethics
**Status:** PARTIAL  
**Inputs:** Have I Been Pwned breach records, FTC privacy enforcement, state AG breach notifications  
**Ladder:** Editorial. <100K records breached = 80; <1M = 60; <10M = 40; >10M = 20.  
**Path forward:** California CCPA + EU GDPR define "material" breach thresholds. Mapping to those would ground.

### M.3 — Market Ethics
**Status:** PARTIAL  
**Inputs:** SEC enforcement actions, DOJ antitrust cases, FEC/OpenSecrets political donations, FTC market actions, FCC enforcement  
**Ladder:** Editorial. Sherman Act violations weighted heavier than minor SEC enforcement; political donation concentration > $10M flagged.  
**Path forward:** DOJ/FTC publish their own severity classifications for enforcement actions.

### M.4 — Product Ethics
**Status:** PARTIAL  
**Inputs:** CPSC SaferProducts recalls, NHTSA recalls, FDA recalls, Product Harm Index dictionary  
**Ladder:** Editorial. Recall classification (Class I/II/III) is authoritative; mapping to score bands is editorial.  
**Path forward:** CPSC publishes recall severity tiers. Reproducing their classification = grounded.

### M.5 — Stakeholder Ethics & Harm Documentation
**Status:** GROUNDED *(for documented harm events)*  
**Inputs:** Major Harm Events dictionary (court settlements, attributed deaths, knowing concealment, weapons), DOJ/SEC/state AG records  
**Ladder:** Penalties applied directly proportional to documented attribution (deaths attributed by court findings). Magnitude grounded in legal records.  
**Path forward:** Pre-2020 historical harm coverage is incomplete; backfilling from EPA Superfund + state AG databases planned.

---

## A — Alive & Environmental

### A.1 — Energy Use & Climate
**Status:** GROUNDED  
**Inputs:** CDP Climate Disclosures (audited reporting), Science Based Targets initiative (SBTi) validations, EPA emissions data  
**Ladder:** Reproduces SBTi tier classification (1.5°C aligned / well below 2°C / committed / not committed).  
**Notes:** This is one of two fully grounded sub-signals.

### A.2 — Water & Pollution
**Status:** PARTIAL  
**Inputs:** EPA ECHO violations, CDP Water Disclosures, Clean Water Act enforcement  
**Ladder:** Editorial penalty severity. EPA classifies violations (significant noncompliance, etc.) but our ladder doesn't fully reproduce their classification.  
**Path forward:** Map directly to EPA's HPV (High Priority Violation) classification.

### A.3 — Land Use & Deforestation
**Status:** PARTIAL  
**Inputs:** CDP Forests Disclosures, industry deforestation risk dictionary, USDA Organic certification  
**Ladder:** Editorial. Forest commitment score from CDP combined with sector risk weights.  
**Path forward:** Forest 500 publishes a methodology that could ground the ladder.

### A.4 — Product Lifecycle
**Status:** PARTIAL *(for 15 covered companies)*  
**Inputs:** iFixit repairability scores (consumer electronics, ~15 companies)  
**Ladder:** Reproduces iFixit's 1-10 repairability tiers, scaled to 0-100.  
**Coverage gap:** ~426+ companies fall back to industry default (varies by sector). Path forward: EU Extended Producer Responsibility datasets.

---

## N — Natural Transparency

### N.2 — Disclosure Volume
**Status:** GROUNDED  
**Inputs:** SEC EDGAR filing count by type (10-K, 8-K, DEF 14A, Form 4) over trailing 12 months  
**Ladder:** Reproduces SEC's own materiality framework — companies with consistent on-time material disclosure rank highest.  
**Notes:** Second of two fully grounded sub-signals.

### N.5 — Audit Trail Depth
**Status:** UNGROUNDED  
**Inputs:** Editorial — composite of voluntary GRI/SASB reporting + 10-K depth  
**Ladder:** Editorial. Both inputs and ladder are internally constructed.  
**Path forward:** GRI publishes its own quality scoring framework. Reproducing it would ground this.

---

## Deferred to v1.2

These 7 sub-signals are spec'd in HUMAN Grade Spec v1.1.0 but **not yet scored**. They will be added in v1.2. Until then, they receive no contribution to dimension scores.

| ID | Name | Why deferred |
|---|---|---|
| H.4 | Decision Authority | No reliable proxy for "human-in-the-loop" rate yet |
| H.5 | Craft Retention | Need apprenticeship/skills-pipeline data source |
| U.5 | Relational Integrity | Multi-year customer retention data not standardized |
| A.5 | Lifecycle Accountability | EU EPR data ingestion planned for v1.2 |
| N.1 | Reporting Quality | Awaiting GRI quality score grounding |
| N.3 | Subsidiary Transparency | SEC Exhibit 21 parsing in development |
| N.4 | Supply Chain Attestation | Modern Slavery Act + Conflict Minerals data ingestion planned |

---

## What this document is NOT

- It is **not** a defense of the editorial choices. Where the ladder is editorial, we say so.
- It is **not** a roadmap commitment. Path-forward notes are research directions, not promises.
- It is **not** a substitute for the methodology. Read [thehibalance.org/methodology](https://thehibalance.org/#methodology) for how the dimensions and composite score are computed.
- It is **not** an implication that PARTIAL sub-signals are wrong. The data inputs are authoritative; the cutoffs are reasonable. They are simply not yet reproduced from a published authority.

---

## How to challenge a ladder

If you believe a specific sub-signal ladder is mis-calibrated:

1. Open an issue: [github.com/thehibalance/hi/issues/new](https://github.com/thehibalance/hi/issues/new) with label `ladder-grounding`
2. Cite the published authority you believe should ground the cutoffs
3. Propose the mapping (e.g., "B Corp publishes 80-quintile cutoffs; our ladder should reproduce them")

We respond to ladder-grounding issues within 5 business days.

---

*Last updated: April 2026. Spec v1.1.0. Maintained by Morf Innovations LLC. Apache 2.0 licensed.*
