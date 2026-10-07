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

Spec version: **v1.11.0** · Active sub-signals: **18** · Not yet scored: **5** · Retired: **1** (N.5, v1.11.0)

**Of those 18, nine carry real measurement for 40 or more companies** (H.1+H.3 counted once, A.3, U.3, M.5, A.4, U.1, H.5, N.2, M.3). Four are industry lookup tables for 90–100% of companies (H.2, U.4, A.4, A.1). Five reach under 4% of companies. See `claude/AUDIT-the-honest-baseline.md`.

**Industry constants are not evidence (v1.6.0).** Where a sub-signal's value comes from an
industry lookup table rather than from anything about the company, it no longer counts toward that
company's coverage or confidence. It still contributes to the score as a prior, and the company's
`data_sources` says `Industry`. This applies the rule `aggregate_collected.py` has enforced since
v1.4.0 to the engine's own internal defaults: H.2 craft baselines, and the A.1 and A.4 fallbacks.
The effect was 1.78 sub-signals per company, which moved published median coverage from 7/19 to
5/19. **v1.7.0 found one more:** U.4 reads like a Glassdoor blend, but only about 37 of 1,141
companies have a Glassdoor record, so for the other 692 affected companies it was the industry
table alone. Median coverage is now a truthful **2/18** — and under v1.11.0, **270 of 1,041 scored companies measure nothing at all**, stated rather than hidden behind a composite. No score changed in either release.

**One company, one score (v1.8.0).** The engine matched sources by a name normalizer that
stripped a fixed suffix list once. SEC spellings (`BANK OF AMERICA CORP /DE/`) and
sustainability-data spellings (`Bank of America Corporation`) therefore described two
different companies, each scored on half the evidence, with one copy dropped at the end of
the run — 94 of 1,140 companies. `canon_name()` now gives every source one spelling. Five
composites moved, all upward, all because the company now sees evidence it already had:
JPM 57→66, BAC 63→70, SBUX 65→70, MCD 66→69, JNJ 49→50. In the same release the nightly
score merge stopped preserving rows the engine no longer produces: four had been frozen at
spec 1.2.1 since March, and two of them were the last place FDA evidence — withdrawn in
v1.5.1 — still appeared. Published sources: 22 → 21.

**A measurement of the wrong thing is not grounding (v1.9.0).** H.2 had a BLS wage adjustment
waiting to be connected, and connecting it would have inverted the sub-signal — wage data ranks
tech above food service on "craft," which is the reverse of what the table asserts and of what the
signal is for. It was removed instead, and H.2 is now documented as an editorial prior that never
counts toward coverage. The rule this sets: a sub-signal is grounded when an authoritative source
measures *the construct we claim*, not when an authoritative number is available to multiply by.


Every entry below was checked against `pipeline/scoring_engine.py` in September 2026. Where this file and the code disagree, the code is right and this file is a bug.

---

## Summary

| Status | Count | Meaning |
|---|---|---|
| GROUNDED | 0 | Data + ladder both authoritative |
| PARTIAL | 10 | Authoritative data, editorial ladder |
| UNGROUNDED | 8 | Editorial data + editorial ladder, or mostly industry defaults |
| **TOTAL ACTIVE** | **18** | |
| NOT YET SCORED | 5 | Defined in the spec, contributes nothing |

The dominant pattern is **PARTIAL**: authoritative data read through cutoffs we chose ourselves. Eight sub-signals are UNGROUNDED, and none is fully GROUNDED yet. We don't hide this — most ladders were authored by judgment during the engine build, not by reproducing a published authority. **Grounding them is the active research priority.**

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
**Coverage (Oct 2026):** **649 of 1,045** companies measured. Correlates with H.3 at **Spearman 0.930** (632 companies) — the two are one measurement counted twice; see the note under H.3.  
**Inputs:** SEC EDGAR / FMP `revenue_per_employee`, industry medians computed from the scored universe, job-board AI-vs-human hiring ratio  
**Formula:** `65 + 15·log2(industry_median / rpe)`, clamped 0–100; blended 50/50 with the job-board score when that data exists  
**Ladder:** The medians are now measured, not chosen: each is the median revenue per employee of the companies we score in that industry (`recalibrate_medians.py`), so the median company scores 65 by construction. The 65 anchor and the 15-points-per-doubling slope are editorial; the slope was chosen by testing five candidate formulas against the real distribution. Industries with fewer than 10 companies are marked provisional.  
**Path forward:** **Census Economic Census** `RCPTOT` (total receipts) + `EMP` at 6-digit NAICS — free API and bulk files — gives a real receipts-per-employee denominator. **Correction, Oct 2026:** the previous note here said "BLS QCEW × Compustat." QCEW is built from state unemployment-insurance tax reports and contains establishment counts, employment and wages **only — no revenue, receipts, sales or output field of any kind**, so that path cannot produce this denominator and has been struck. Two caveats on the Census route: its denominator is all firms in the industry, overwhelmingly small ones, so public-company RPE sits far above the industry mean; and low revenue per employee is also what capital-light industries look like, so the construct measures capital intensity alongside workforce valuation. No authority publishes revenue-per-employee tiers, so the cutoffs remain editorial under every option.

### H.2 — Craft
**Status:** UNGROUNDED *(was PARTIAL; changed September 2026)*  
**Coverage (Oct 2026):** **0 of 1,045** companies measured. This sub-signal is the `craft_defaults` lookup table for **every company in the file** — the BLS adjustment has never fired for anyone. It is a constant, not a partially grounded measure.  
**Inputs:** a 12-entry `craft_defaults` industry table (in-house). Nothing else. **Always excluded from coverage and confidence.**  
**Ladder:** Editorial throughout. The table encodes a judgment — that hands-on human work still carries the output in food service (65), healthcare (70) and manufacturing (60), and carries less of it in tech (40), telecom (40) and retail (45).  
**Why the BLS adjustment was removed rather than connected (v1.9.0):** a wage-vs-national term sat here, inert since nothing wrote the field it read. Connecting it would have moved H.2 by only about ±8 points on a base of 40–70 while claiming full coverage credit for the sub-signal — re-admitting an industry constant as evidence, which is what v1.6.0 removed. Worse, it measures the opposite construct: Information earns roughly 1.44× the total-private average and Leisure/Hospitality about 0.64×, so a wage-derived H.2 would rank tech as high-craft and food service as low-craft. Wages are a real measurement of a different thing.  
**Path forward:** **O*NET Job Zones** weighted by **BLS OEWS** national industry-specific (SOC × NAICS) employment. Both are free bulk downloads, and O*NET publishes the tiers with numeric cutoffs: five named zones by Specific Vocational Preparation — Zone 1 "Little or No Preparation" (SVP < 4.0), Zone 2 "Some Preparation" (4.0–<6.0), Zone 3 "Medium" (6.0–<7.0), Zone 4 "Considerable" (7.0–<8.0), Zone 5 "Extensive" (8.0+). An employment-weighted mean Job Zone per industry replaces the entire hand-written table with a measured quantity on DOL's cutoffs. **This is the single highest-value grounding available in the index**, because H.2 currently has zero measured input. Cross-check with BLS Employment Projections education/training assignments, which classify every occupation independently. **Registered apprenticeship is not viable** — a few hundred thousand apprentices nationally, concentrated in construction and utilities, and RAPIDS records are programme sponsors rather than matchable employers.

### H.3 — Human Decision Depth
**Status:** UNGROUNDED  
**Coverage (Oct 2026):** **635 of 1,045** measured; **352** recorded as no-measurement since v1.12.0 (no credible industry RPE median). Of the measured arm, **16% sit at exactly 100** — the linear form saturates. Correlates with H.1 at **0.930**: both are functions of revenue per employee against the industry median, so D_H counts one datum twice.  
**Inputs:** SEC EDGAR `revenue_per_employee`, headcount tier (>200k/>50k/>10k), industry bias dict, displacement signal  
**Ladder:** Editorial apart from the industry median, which is measured since v1.3.0: the `40 + (median/rpe)·30` anchor, headcount tier cutoffs, industry bias values (healthcare +10, defense +8, retail −5, tech −8, etc.), displacement coefficient.  
**Path forward:** **O*NET Work Context** publishes exactly this construct on verbally anchored 5-point scales: *Frequency of Decision Making* (Never → Every day), *Freedom to Make Decisions* (No freedom → A lot of freedom), *Impact of Decisions on Co-workers or Company Results*, and *Responsibility for Outcomes and Results*. Free bulk download, 291,201 rows, aggregated to industry by the same OEWS crosswalk H.2 uses. **This is the fix for the 0.930 correlation with H.1**, because it is wholly independent of revenue per employee. A second free measure of organisational depth is computable from OEWS alone: management and first-line-supervisor employment share per industry is the inverse of span of control. Separately, the linear `40 + ratio·30` form should become a log form — measured candidates put `65 + 15·log2(ratio)` at 26 companies on the ceiling against 105 today, the same correction H.1 took in v1.3.0. Per-employer alternatives were assessed and rejected: H-1B/PERM covers only sponsors and scores non-sponsors null rather than low; WARN has no federal database; NLRB measures unionisation, a different construct.

### H.5 — Human Augmentation Index
**Status:** PARTIAL  
**Coverage (Oct 2026):** **50 of 1,045** companies measured. Correlates with H.1 at **0.829** (44 companies).  
**Inputs:** SEC `displacement_signal` (R&D-spend growth vs headcount change), job-board `ai_hiring_trend` (surging/growing/stable), USPTO patent AI ratio  
**Ladder:** Spec (`h5-augmentation-draft.md`) is rubric-grade. Engine implements only the displacement half. Augmentation half (reskilling, internal mobility, tool-building) not yet ingested.  
**Path forward:** **No free per-company source exists** and this sub-signal should be demoted to a disclosed diagnostic or dropped. Census **BTOS** asks precisely the right questions — whether AI increased or decreased employment, and whether staff were trained or hired for AI — but publishes **sector aggregates from a sample survey**, so it can set an industry prior and cannot distinguish two companies in a sector, which is the entire purpose. The one per-company option, the **American Opportunity Index** (395 large employers), is built on LinkedIn and proprietary Burning Glass data, so it is not reproducible, is scrape-only, publishes no thresholds, and is not AI-specific. Lightcast publishes no pricing and its free tier contains no employer data. At 50 of 1,045 companies, folding this into a composite is not defensible.

---

## U — Understanding & Empathy

### U.1 — Customer Empathy  
**Status:** PARTIAL — *anchor grounded, slope editorial* *(construct replaced in v1.10.0)*  
**Coverage (Oct 2026):** **65 of 1,045** companies measured — CFPB-regulated financial services only. This is the only sub-signal in the index anchored to a published federal distribution.  
**Inputs:** CFPB complaint outcomes by product, for the 27 companies with at least 100 complaints in a product CFPB publishes a rate for; BBB complaints (10% blend); Glassdoor overall and culture ratings as fallback; neutral 50 when none exists.  
**Ladder:** `50 + (company relief rate − CFPB's published relief rate for that product)`, volume-weighted across the company's products and across CY2023 and CY2024, clamped to [25, 85]. **The neutral point is CFPB's own published figure** (Consumer Response Annual Report, Table 1, p.18), not a constant we chose — the first anchor in this system taken from an outside authority. The slope of one score point per percentage point remains editorial, and is 1:1 because that is the least tunable choice available and a reader can check it by hand.  
**Role rule:** credit reporting and debt collection are scored only for SIC 732x (consumer credit reporting and collection agencies). For everyone else those benchmarks are set by a different kind of company: of 22 measured in credit reporting, 21 were furnishers answering disputes about data they reported and sat 20–52 points below, while the single actual bureau was the only one above. Verisk is gated out on SIC 7374 despite running consumer-reporting products — a close call, recorded rather than hidden.  
**Known limitations:** volume is disclosed, not scored, so a company that generates enormous complaint volume and resolves it well scores well; whether that is right is a judgment this project cannot settle alone. A relief rate also cannot distinguish a company that prevents problems upstream from one that refuses relief — CFPB's `company_public_response` field would separate them but is voluntary, with median coverage of 0% and 25 of 57 companies silent. Coverage fell from 39 companies to 27 when the evidence floor was applied; CFPB regulates financial services and nothing else, so ~1,100 companies need a source that does not exist.  
**Path forward:** **Leave this sub-signal sector-bounded and say so.** A search for a CFPB equivalent in other sectors found none. **FCC** publishes individual complaints with **no company name field at all** and no resolution field. **NHTSA ODI** complaints carry a manufacturer name but no remedy or outcome field. **DOT** moved in 2023 to monthly PDF counts with no disposition. **FTC Consumer Sentinel** is law-enforcement-only and its public Data Book names no companies. **FDA MAUDE** has a sparsely populated `remedial_action` field describing a product action rather than a complainant remedy, with no published benchmark. The one structurally correct analogue — **NHTSA Vehicle Safety Recall Completion Rates**, which publishes per-manufacturer completion rates *and* NHTSA's own 62.1% benchmark — covers 13 manufacturers in a PDF appendix. What makes CFPB work, a published per-company relief rate plus the regulator's own benchmark rate per product-year, is unique to CFPB.

### U.2 — Worker Empathy
**Status:** UNGROUNDED  
**Coverage (Oct 2026):** **39 of 1,045** companies measured. OSHA and DOL remain unconnected.  
**Inputs:** Glassdoor employee ratings, weighted by review count; OSHA (15% blend) and DOL (10% blend) — neither OSHA nor DOL is producing data today  
**Ladder:** Glassdoor is a commercial reporter, not an authoritative threshold system. The blend weights are editorial.  
**Path forward:** **OSHA Injury Tracking Application Form 300A establishment data** — free annual CSV, 2016 onward, carrying `company_name`, `ein_number`, `naics_code`, `annual_average_employees`, `total_hours_worked` and case counts — benchmarked against **BLS SOII Table 1** detailed-NAICS incidence rates. BLS also publishes its own **Incidence Rate Calculator and Comparison Tool**, whose stated purpose is this exact establishment-versus-industry comparison, so the rate formula, the industry comparand and the comparison method are all federal publications and nothing is hand-set. Two obligations come with it. The ITA file has **no parent identifier**, so the join is name plus EIN clustering. And finance, insurance, software publishing, data processing and professional services are **partially exempt from OSHA recordkeeping** under 29 CFR 1904 Subpart B Appendix A — so a large, identifiable part of this universe must return *no evidence*, never *safe*. Realistic reach is 350–500 companies. OSHA's own Site-Specific Targeting DART cutoffs are not public, so use BLS percentile position rather than an OSHA tier. Second free federal source: **DOL WHD compliance actions**, ~367,890 investigations with employer name, back wages, employees affected and penalties.

### U.3 — Relational Integrity
**Status:** PARTIAL *(was UNGROUNDED; changed September 2026)*  
**Coverage (Oct 2026):** **116 of 1,045** companies measured, of which **82% score in the top fifth** — but see the path forward: HRC rates 1,449 companies including non-participants and publishes zeros, so this is substantially a collection gap, not only a selection effect.  
**Inputs:** HRC Corporate Equality Index, Disability:IN DEI Index, B Corp status, blended with the Glassdoor culture score  
**Ladder:** HRC and Disability:IN are authoritative inclusion ratings; the blend weights are editorial.  
**Path forward:** **Scrape the full HRC Corporate Equality Index.** The important finding: **HRC rates non-participants and publishes zeros.** CEI 2025 covers **1,449 companies** and states it reflects "verified data submitted to the HRC Foundation as well as independent research on non-responding businesses… irrespective of their participation." So the top-heavy distribution here is substantially a **collection gap** — 116 companies used against an index that rates 1,449 including low scorers — rather than purely a selection effect. HRC publishes its 100-point structure (Workforce Protections 30, Inclusive Benefits 30, Inclusive Culture & CSR 40, and a **−25 Responsible Citizenship deduction**). **Disability:IN** publishes its methodology and an 80+ threshold but **discloses only honorees**, so it is one-tailed and cannot carry a ladder — demote it to a bonus flag. On covering non-participants from a non-voluntary source the answer is no: **EEO-1 Component 1 cannot be used**, because Title VII § 709(e) prohibits release of individually identifiable data, and OFCCP publishes audit *selection* lists, which are a selection artifact rather than a finding.

### U.4 — Simulated Empathy Detection
**Status:** UNGROUNDED *(was listed as PARTIAL; corrected in v1.7.0 — this entry described the AHI, which is a downstream penalty, not U.4's input)*  
**Coverage (Oct 2026):** **38 of 1,045** companies measured; **1,007** receive the `u4_industry` constant. PARTIAL describes the 38; the remaining 96.4% are an industry lookup table.  
**Inputs:** a 15-entry industry automation table (in-house), blended 40/30/30 with Glassdoor culture and overall ratings **where a Glassdoor record exists — it does for about 37 of 1,141 companies**. For everyone else U.4 is the industry constant alone.  
**Ladder:** Editorial in both halves: the industry values (hospitality 72, food 70, healthcare 65 … telecom 32, insurance 30) and the 40/30/30 blend were chosen by us.  
**Path forward:** **AI Incident Database** (Responsible AI Collaborative) — free weekly bulk exports in JSON, MongoDB and CSV, with entities modelled structurally by role (as Deployer, as Developer, Harmed By) — with severity tiers from the **MIT AI Risk Initiative tracker**, which applies **CSET's AI Harm Taxonomy**: ten harm types scored 1 "Negligible" to 5 "Catastrophic", CC BY 4.0. That is the only published severity ladder found in this field. **Correction, Oct 2026:** the previous note cited AlgorithmWatch harm tier classifications. **No such dataset exists** — AlgorithmWatch is an advocacy and journalism organisation — and the claim has been struck. Honest ceiling: AIID is editor-curated from media reports, so realistic coverage is **60–120 of 1,045 companies**, concentrated in large-cap technology. A company with no incident record is one no journalist wrote about, not one without algorithmic harm. Adopting it replaces a 96.4% lookup table with ~10% real coverage and ~90% declared no-evidence, which is the honest trade.

---

## M — Moral & Ethical Conduct

### M.1 — Pricing Ethics
**Status:** PARTIAL *(was UNGROUNDED; restored in v1.5.0)*  
**Coverage (Oct 2026):** **27 of 1,045** companies measured.  
**Inputs:** CFPB complaint volume (see U.1), capped so the same evidence never scores higher here than on U.1; FTC pricing actions, state AG settlements, predatory pricing dictionary. Companies with no CFPB record score a neutral 50  
**Ladder:** Editorial. Settlement >$10M flagged "material"; >$100M = "major." These are not derived from SEC materiality framework.  
**Path forward:** **CFPB's own statutory penalty tiers, 12 U.S.C. § 5565(c)** — three levels defined by culpability rather than size: first tier not exceeding $5,000 per day for any violation, second tier not exceeding $25,000 per day for reckless violations, third tier not exceeding $1,000,000 per day for knowing violations, with statutory mitigating factors. Bucket by **which tier the agency charged under**, which appears in the order document, rather than by settlement size. **Correction, Oct 2026:** the previous note cited "SEC materiality thresholds (typically 5% of revenue)." SAB 99 says the opposite in terms — "exclusive reliance on this or any percentage or numerical threshold has no basis in the accounting literature or the law" — permitting 5% only as a preliminary rule of thumb. Citing the SEC for a bright line would misrepresent the source, and the claim has been struck. Note also that CFPB stopped publishing complaint narratives on 17 Aug 2026; structured fields appear to remain but should be re-confirmed.

### M.2 — Data Ethics
**Status:** PARTIAL  
**Coverage (Oct 2026):** **31 of 1,045** companies measured.  
**Inputs:** Have I Been Pwned breach records **matched by exact domain since v1.4.0** (the old name-fragment matching attributed other sites' breaches to the wrong company and was withdrawn), FTC privacy enforcement, state AG breach notifications. No known breach is not scored as good practice; it earns no credit. Companies with no domain on file can't be checked  
**Ladder:** Editorial. <100K records = 80 pts; <1M = 60; <10M = 40; >10M = 20.  
**Path forward:** **HHS OCR breach portal** — free CSV, Excel and XML export, per covered entity, carrying the only authority-published record threshold in US privacy law: breaches **affecting 500 or more individuals**, under HITECH § 13402(e)(4). Healthcare only, so roughly 60–100 companies. For severity, the **HIPAA civil money penalty structure at 45 CFR 160.404** tiers by culpability in four levels (no knowledge; reasonable cause; willful neglect corrected; willful neglect uncorrected). **Correction, Oct 2026:** the previous note said CCPA and GDPR define material breach thresholds. Neither defines a **record-count** threshold — CCPA § 1798.150 sets $100–$750 per consumer per incident with discretionary factors, and GDPR Article 83 tiers by **revenue percentage** (2% / 4%), not records. The claim has been struck. The California AG breach list is free CSV but **publishes no affected-individual count**, so it supports incident counts only.

### M.3 — Market Ethics
**Status:** PARTIAL  
**Coverage (Oct 2026):** **40 of 1,045** companies measured; the rest are recorded as no-measurement (a litigation value of zero is an absence, not a clean record — v1.11.0).  
**Inputs:** SEC litigation and EPA penalties (legal score), blended with certification signals when present (60% certifications, 40% legal); EEOC, pay-ratio (DEF 14A) and insider-trading (Form 4) adjustments  
**Ladder:** Editorial. The legal-penalty dollar tiers ($1B / $100M / $10M / $1M) and the certification blend weights are in-house.  
**v1.11.0 correction:** the legal component scored **85 when no penalty record was found**, and no record has ever been found — zero of 1,048 SEC records carry a litigation value and the EPA records carry empty `m_signals`. M.3 therefore read 85 for 1,013 of 1,139 companies while claiming to measure legal conduct. It is now a neutral 50 marked not-evidence unless a certification or a real penalty record exists, which is true for 128 companies.  
**Path forward:** **EPA ECHO** publishes per-facility, per-statute compliance classifications that can replace the invented dollar ladder outright: **High Priority Violation** (Clean Air Act), **Significant or Category I Noncompliance** (Clean Water Act), **Significant Noncomplier** (RCRA), **Enforcement Priority** (SDWA), sitting above "Violation Identified" and "No Violation Identified" — plus **`Quarters with Noncompliance (of 12)`**, an ordinal severity measure requiring no invention. Free weekly bulk download, no key. **The blocker is attribution, and it is specific:** ECHO's Detailed Facility Report carries no owner, parent or DUNS field, and the FRS download is facility-level with no organisational structure. **TRI Basic Data Files are the only EPA dataset with a parent-company field** — `PARENT CO NAME`, `PARENT CO DB NUM`, and a maintained `STANDARDIZED PARENT COMPANY NAME` reflecting the current ultimate US parent. Any plan assuming EPA facility data can be rolled up to public companies is assuming a field that exists in exactly one programme. The antitrust half has no equivalent: DOJ and FTC publish aggregate fiscal-year counts classified by procedural type, with no severity field and no per-company records.

### M.4 — Product Ethics
**Status:** UNGROUNDED *(was PARTIAL; changed in v1.5.1 when FDA was withdrawn)*  
**Coverage (Oct 2026):** **38 of 1,045** companies measured. The CPSC path produces nothing; see the path forward for why.  
**Inputs:** CPSC SaferProducts recalls (integrated, not yet producing data); Glassdoor management and compensation ratings as fallback. **FDA is withdrawn** — an audit found 1,041 of 1,422 collected rows scoring 85 because openFDA returns 404 when nothing matches and the collector recorded that as "no recalls", and 228 more scoring 25 because an empty company name searches as a wildcard.  
**Ladder:** Editorial while FDA is out: the score rests on employee ratings, which are not a measure of product safety.  
**Path forward:** **openFDA enforcement endpoints** (food, drug, device) — free API and bulk JSON, 2004 onward, weekly, with `recalling_firm` per record and a severity classification **defined in binding regulation at 21 CFR 7.3(m)**: Class I "reasonable probability that use of, or exposure to, a violative product will cause serious adverse health consequences or death", Class II "temporary or medically reversible", Class III "not likely to cause adverse health consequences". The `classification` field is attached to every record, so the invented tiers can be deleted rather than recalibrated. **Correction, Oct 2026:** the previous note said CPSC publishes recall severity. **Class I/II/III is FDA's system.** CPSC does maintain a Class A/B/C hazard priority in its Recall Handbook, but it is an **internal staff tool and is not published per recall** — the SaferProducts API returns no severity field, which is almost certainly why this sub-signal's CPSC path produces nothing. NHTSA is worth adding for volume (free APIs and flat files, per manufacturer) but publishes no severity or hazard-class field; its one tiered publication is the NCAP 5-star rating, which measures product safety performance rather than recall severity.

### M.5 — Stakeholder Governance
**Status:** PARTIAL  
**Coverage (Oct 2026):** **104 of 1,045** companies measured — the best-covered sub-signal in M.  
**Inputs:** stakeholder-centric legal structure (B Corp and similar signals); FEC political spending when available; Glassdoor CEO rating as a last fallback  
**Ladder:** B Corp status is authoritative; the FEC spending tiers and the Glassdoor fallback are editorial. Since v1.4.0 FEC counts only when committees are actually found for that company — "none found" used to be scored as clean political conduct. Harm Documentation (settlements, attributed deaths, concealment) penalizes M.3 and M.4 directly; it is not an M.5 input.  
**Path forward:** **No authority publishes corporate political-spending benchmarks relative to size** — not the FEC, not the IRS, not any trade or academic body. FEC bulk data is free and complete at committee and contribution level but publishes no tiers and no issuer rollup, so a "per $B of revenue" ladder remains entirely editorial with a denominator attached. The **CPA-Zicklin Index** does publish real tiers at real thresholds over the Russell 1000 — Trendsetters at 90% or above, a first tier at 80–100% — but it scores *disclosure and governance policy* for political spending, not amounts spent, so adopting it substitutes a different construct and must be renamed if used. **Urgent, Oct 2026:** the B Corp leg of this sub-signal rests on a scale being eliminated. B Lab's **V2 standards, launched 8 April 2025, remove the scoring system entirely** — no 80-point threshold, no numeric B Impact Score, pass/fail against seven mandatory impact topics verified by third parties. Large companies recertify under V2 from January 2026 and all recertifications from 2027, so `_score_from_bcorp` will stop having a score to read. This affects U.3 as well.

---

## A — Alive & Environmental

### A.1 — Energy & Emissions
**Status:** UNGROUNDED  
**Coverage (Oct 2026):** roughly **32 of 1,045** companies measured; approximately **1,013** receive an industry default. The exact split cannot be determined from published data because one measured path writes `cdp_score` directly and CDP scores collide with the fallback values {30, 40, 45, 50, 55, 60, 65}.  
**Inputs:** CDP Climate disclosures (when available), industry-default emissions intensity table  
**Ladder:** CDP disclosure letter grades exist but engine doesn't reproduce them. Industry defaults are in-house.  
**Path forward:** **SBTi Target Dashboard** — free .xlsx export covering 14,245 companies (12,092 with validated targets, 2,310 with active commitments), **carrying an ISIN column**, so matching is a join rather than a fuzzy-name problem. SBTi publishes its own exhaustive ordinal: near-term status `Validated Targets` / `Commitment to Set Targets` / `Commitment Removed`, and temperature alignment `1.5°C` / `well-below 2°C` / `2°C`, plus separate net-zero status. The decisive property is that **absence is informative** — SBTi enumerates every company that has acted, so a company not in the register is genuinely "not committed" and earns a real bottom rung instead of an industry default. That single property takes this sub-signal from ~97% invented to 0% invented in one pass. **It measures target ambition, not energy use or emissions**, so adopting it is a construct substitution and the sub-signal must be renamed. Layer **EPA eGRID** (plant-level CO₂ output rates in lb/MWh, free, authoritative — electric power only) and **EPA GHGRP**, which publishes a "Reported Parent Companies" file with percent ownership, for a quantitative second tier; discount GHGRP for durability, since EPA proposed in September 2025 to remove reporting for 46 of 47 source categories. **Correction, Oct 2026:** reproducing CDP's letter tiers is blocked by licence, not by data — CDP scores "must not, without prior written consent from CDP, be used for anything other than internal, non-commercial use," and the free Action Tracker licence explicitly prohibits research in a corporate setting. **Watch item:** California SB 253's first Scope 1/2 reports were due 10 November 2026; if CARB publishes structured figures for thousands of filers, that becomes the best source for this sub-signal in existence. Re-check Q1 2027. The SEC climate rule will not help — formal rescission was proposed 3 June 2026.

### A.2 — Water
**Status:** UNGROUNDED  
**Coverage (Oct 2026):** **17 of 1,045** companies measured — the thinnest sub-signal in the index. The other 1,028 receive a neutral 50, which is a null that reads as a score.  
**Inputs:** CDP Water disclosures (when available); neutral 50 otherwise  
**Ladder:** CDP water scores are mapped by an in-house translation. EPA violations feed A.3, not A.2.  
**Path forward:** **Retire this sub-signal as written, or redefine and rename it.** Water *use* is not a publicly reported quantity for US public companies, and no free source will lift 17 companies. CDP Water is the only real per-company water data and its licence forbids this use. A buildable replacement exists but measures something else: **TRI water releases, parent-attributed** via TRI's `STANDARDIZED PARENT COMPANY NAME` — the only parent field anywhere in EPA's estate — joined to **WRI Aqueduct 4.0** baseline water stress at facility coordinates, which ships `bws_cat` and `bws_label` so the categories travel with the data, and penalised by EPA's Clean Water Act Significant Noncompliance flag. Free, bulk, two publishers' own thresholds, and honest — but it is water *pollution*, not water stewardship, and must be labelled as such. **Ceres' Valuing Water Finance Initiative** publishes bands (Leading 50–75% of expectations met, Lagging below 50%) for 72 companies, which is below usable scale. ECHO's DMR discharge data is facility-level with no parent field at all.

### A.3 — Land & Habitat
**Status:** UNGROUNDED  
**Coverage (Oct 2026):** **249 of 1,045** companies measured — the strongest signal in A.  
**Inputs:** USDA Organic certification (70%) with sector land-use risk (30%); EPA violation counts when neither is available  
**Ladder:** Sector risk weights and the EPA violation tiers (0 / 3 / 10 / 20) are editorial.  
**Path forward:** Two independent upgrades, both available now. **Replace the invented EPA violation tiers (0 / 3 / 10 / 20) with EPA's own four-level ECHO classification** plus `Quarters with Noncompliance (of 12)` — a lookup-table rewrite with no new plumbing. Separately, **Forest 500** (Global Canopy) publishes the most precisely reproducible ladder found in this survey, verbatim: "0% is equivalent to 0/5, 1-19% → 1/5, 20-39% → 2/5, 40-59% → 3/5, 60-79% → 4/5, 80-100% → 5/5", over 56 indicators summing to 100 points with published per-indicator answer options. Free bulk Excel behind a registration form — **check its terms for commercial restrictions before shipping**, the same trap CDP sets. It covers 500 commodity-exposed entities; the US-listed subset is unverified and estimated at 40–70, so Forest 500 **narrows** coverage from 249 while deepening it. Note honestly that **USDA Organic publishes no tiers** — certification is binary and scope-based, so every gradation applied on top of it is editorial, as are the sector land-use risk weights under every option found.

### A.4 — Product Lifecycle
**Status:** PARTIAL *(for 15 covered companies)*  
**Coverage (Oct 2026):** **101 of 1,045** companies measured (iFixit, certifications, CDP Forests); **944** receive the `hw_defaults` industry constant. PARTIAL is accurate for the 101 and UNGROUNDED, by this document's own definitions, for the 944.  
**Inputs:** iFixit repairability scores (consumer electronics, ~15 companies)  
**Ladder:** Reproduces iFixit's 1-10 repairability tiers, scaled to 0-100. Grounded for covered companies.  
**Coverage gap:** every other company falls back to certifications, then CDP Forests, then an industry default. Path forward: EU Extended Producer Responsibility datasets.
**Path forward:** **Keep iFixit for the 101 companies where it applies and report nothing for the other 944.** A sub-signal that covers 101 of 1,045 and says so is a better artefact than one that covers 1,045 and invents 944 of them. **Correction, Oct 2026:** the previous note cited EU Extended Producer Responsibility datasets. **There is no central EU EPR register** — EPR is 27 fragmented national registers, and 2026 industry position papers argue *for* a central European register precisely because none exists. The claim has been struck. France's **indice de réparabilité** is genuinely statutory, free, bulk and daily-refreshed under Licence Ouverte 2.0, with a 0–10 score fixed by decree and mandated display bands — and it reaches an estimated **6–12 US-listed companies**, fewer than iFixit already covers, keyed to French legal entities and individual model references. The EU's Ecodesign for Sustainable Products Regulation will not help in time: horizontal repairability scoring is slated for 2027–2029 and phones and tablets for 2030, and the Digital Product Passport has no operational launch date. Nothing can ground the 944 before roughly 2029.

---

## N — Natural Transparency

### N.2 — Reporting Quality
**Status:** PARTIAL *(was UNGROUNDED; changed September 2026)*  
**Coverage (Oct 2026):** PARTIAL for **42 of 1,045** companies. The remaining 1,003 carry the neutral 50, which is excluded from published coverage. The input is CDP, and 24% of the 42 measured values sit at the ceiling — CDP respondents are a self-selected, disclosure-rich population, so this is a measurement of a narrow group, not of the universe. **CDP's licence forbids commercial use**, which caps this sub-signal where it stands and blocks A.1 and A.2 at the same time. See the grounding map.
**Inputs:** reporting-quality level (excellent / good / partial) from CDP disclosure; CDP non-responders receive a mild penalty; neutral 50 otherwise  
**Ladder:** The mapping from reporting level to score (90 / 70 / 45 / 25) is editorial.  
**Path forward:** **Two routes, and the free one is better aligned with the construct.** CDP's own published score bands would fix the saturation this sub-signal shows — D- 1–49%, D 50–80%, C- 1–44%, C 45–80%, B- 1–44%, B 45–75%, A- 1–69%, **A 70–100%**, a 30-point A band against the current single-value pile-up — but **CDP's licence blocks it**. **Correction, Oct 2026:** the previous note cited GRI's own reporting-quality scoring framework. GRI states that it "does not verify, check or pass judgment on the quality of the disclosures within a report," its Sustainability Disclosure Database **has been decommissioned**, registrations are not public, and Report Services are paid and private. The claim has been struck. SASB/ISSB publish jurisdictional profiles, not a per-company register, and the US is not an adopting jurisdiction. The better free route is to stop scoring self-reported quality and score **authority-found reporting failure** instead: SEC staff comment letters (UPLOAD/CORRESP), **Item 4.02 non-reliance restatements**, and ICFR material weaknesses — free, bulk, every US filer, and not saturated.


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

---

## Grounding map — what can be grounded, and what cannot

*Researched October 2026 across roughly seventeen candidate authorities. Full detail,
including every URL and the items that remain unverified, in
`claude/TRUE-NORTH-grounding-map.md`.*

Two separate questions were asked of every candidate source: does an authority publish
**per-company data** for the construct, and does it publish **its own tiers** so the ladder
is reproduced rather than invented? Data without published tiers still leaves the cutoffs
editorial, which is why so much of this document says PARTIAL.

### Groundable now — free bulk data *and* published tiers

| sub-signal | source | the authority's own tiers |
|---|---|---|
| **H.2** | O*NET Job Zones × BLS OEWS | five zones with SVP cutoffs (<4.0 / 4.0–<6.0 / 6.0–<7.0 / 7.0–<8.0 / 8.0+) |
| **U.2** | OSHA ITA 300A + BLS SOII | BLS detailed-NAICS incidence rates, plus BLS's own comparison tool |
| **M.4** | openFDA enforcement | Class I / II / III, defined in 21 CFR 7.3(m) |
| **A.1** | SBTi Target Dashboard | validated / committed / removed; 1.5°C / well-below 2°C |
| **H.4** *(not scored)* | SEC Pay versus Performance | none — but fully iXBRL-tagged and free |

H.2 is the highest-value item in the index: it currently has **zero measured input** and the
replacement is two free government downloads joined in one script.

### Groundable with work

H.3 (O*NET Work Context — and it breaks the 0.930 redundancy with H.1) · M.3 (EPA ECHO
compliance classes, blocked on parent attribution) · M.1 (CFPB statutory tiers) · M.2 (HHS
OCR 500-individual threshold) · A.3 (Forest 500's published percentage bands; EPA ECHO
classes) · U.3 (scrape the full 1,449-company HRC index) · U.4 (AI Incident Database with
MIT/CSET severity, ~10% coverage ceiling) · N.2 (SEC comment letters and Item 4.02
restatements) · N.3 *(not scored — UK Modern Slavery registry, 34,289 organisations, the best
never-built candidate)*

### No source exists — retire or declare bounded

**U.1** — leave at 65 companies and state that it is sector-bounded. No other regulator
publishes per-company resolution outcomes with its own benchmark.
**H.5** — no free per-company source. Demote to a disclosed diagnostic.
**A.2** — water use is not publicly reported per company. Retire or redefine to pollution.
**A.4's 944** — nothing can ground them before roughly 2029.
**N.4 Humanwashing** and **U.5 Moral Courage** — remove from the spec as promises. The EU
Green Claims Directive proposal was withdrawn, the FTC's enforcement dataset stops at 2019,
and no authority publishes claim-substantiation tiers. Keep the internal humanwashing flag as
a labelled diagnostic with no score.

### Three findings that govern everything above

1. **TRI is the only EPA dataset with a parent-company field.** ECHO, FRS and DMR are all
   facility-level with no owner, parent or DUNS. Only TRI carries a maintained
   `STANDARDIZED PARENT COMPANY NAME`. Any plan assuming EPA data can be rolled up to public
   companies is assuming a field that exists in exactly one programme.
2. **B Corp is eliminating its score.** V2 standards (April 2025) replace the 80-point
   threshold with pass/fail on seven mandatory topics; all recertifications fall under them
   from 2027. Both U.3 and M.5 read that score today.
3. **CDP cannot be built on.** Its licence restricts use to internal, non-commercial purposes
   at an unpublished price, which blocks the stated path for A.1, A.2 and N.2 at once.

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

*Last updated: October 2026. Spec v1.11.0 (one spelling per company; fossil rows expire in every store the pipeline updates in place; 21 sources; METHODOLOGY.md corrected to the engine; U.1 measured against CFPB's published per-product relief rates rather than per employee; M.3 and N.5 retired as defects; H.3 scored only where a credible industry RPE median exists). Maintained by Morf Innovations LLC. Apache 2.0 licensed.*
