# HI Grade Methodology
## The math behind being human kind.

**Version 1.1.0 · April 2026 · Apache 2.0 · [thehibalance.org](https://thehibalance.org)**

---

*How HI Grade scores every company on how they treat people.*

---

## Table of contents

1. [Why HI Grade exists](#1-why-hi-grade-exists)
2. [The HUMAN framework](#2-the-human-framework)
3. [The 19 sub-signals](#3-the-19-sub-signals)
4. [Gold HI Grade — the v1.1.0 gate](#4-gold-hi-grade--the-v110-gate)
5. [The AI-HI Balance principle](#5-the-ai-hi-balance-principle)
6. [Humanwashing, AHI, and PHI](#6-humanwashing-ahi-and-phi)
7. [The 42 data sources](#7-the-42-data-sources)
8. [What we measure vs. what we don't](#8-what-we-measure-vs-what-we-dont)
9. [Open source and how to verify](#9-open-source-and-how-to-verify)

---

## 1. Why HI Grade exists

HI Grade started with a question on Earth Day 2025: **if AI is changing everything, who's measuring what we're losing?**

Not just jobs. The craft behind the work. The empathy in the service. The humans in the loop. The balance between what AI handles and what humans still do.

HI Grade exists to measure that balance.

**The balance between Artificial Intelligence and Human Intelligence — measured without AI.**

Every other ESG framework now uses large language models to summarize reports, classify sentiment, and generate scores. We don't. HI Grade uses deterministic math on public data. SEC filings. EPA violations. Government datasets. Third-party certifications. Every sub-signal is a published threshold applied to a public number. No sentiment analysis in scoring. No neural networks making judgments. No hallucinations.

**Edge to cloud, no black boxes — just math and data.**

The code is open source. The data is public. The math is reproducible. Run it yourself and get the same answer we got.

**The name encodes the question.** Is it `hi` — a greeting? Or `HI` — Human Intelligence? That's what HI Grade asks of every company: as AI reshapes what they build and how they serve, how much human is left in the final thing you experience?

### What ESG got wrong

MSCI famously rated ExxonMobil higher than Tesla on environmental factors. Sustainalytics rates tobacco companies on "governance practices" rather than the product they sell. The largest ESG providers charge companies millions to be rated — a pay-to-play system that biases toward those who can afford the fees.

Those frameworks were built before ChatGPT. Before AI could write your customer service emails, make your hiring decisions, and compose the ads you see. Before it became possible for a company to cut 40% of its workforce, replace them with algorithms, and keep marketing itself as "human-first."

HI Grade measures the thing ESG missed: **is there still a human in there?**

---

## 2. The HUMAN framework

HI Grade scores companies across five dimensions. Together they spell HUMAN:

### H — Human Consciousness
*Does the company value and invest in its people as people?*

This dimension asks whether a company treats employees as craft-holders, decision-makers, and co-authors of what they produce — or as interchangeable cost centers to be optimized away. It measures workforce investment, craft depth, human decision depth (are humans still making the decisions or just approving what algorithms decided?), and human augmentation balance.

**High scorers** tend to invest in skill development, keep humans in leadership and judgment roles, and disclose workforce composition honestly. **Low scorers** tend to have high revenue-per-employee anomalies (humanwashing flag), mass layoffs without transition support, and decision-making increasingly delegated to automation without oversight.

### U — Understanding & Empathy
*Does the company actually care about the people it serves?*

This dimension measures how a company treats the humans it interacts with — customers, employees, communities. It captures customer empathy (are complaints resolved? is support accessible?), worker empathy (employee sentiment, wage fairness, workplace safety), relational integrity (how the company treats underrepresented groups), and simulated empathy detection (can you tell if a "personal" interaction is AI-generated?).

**High scorers** have strong customer complaint resolution, positive employee sentiment on platforms like Glassdoor, HRC Corporate Equality Index recognition, and accessibility commitments. **Low scorers** have high consumer-complaint density, worker discrimination findings, and scripted interactions that pass for empathy but lack it.

### M — Morals & Ethics
*Does the company do right by the markets, customers, data, and democracy?*

This dimension covers pricing ethics, data ethics (breaches, privacy practices), market ethics (supply chain integrity, legal penalties, corruption), product ethics (recalls, safety violations, deceptive practices), and political ethics (PAC contributions, lobbying concentration, stakeholder governance).

**High scorers** have clean regulatory records, few data breaches, transparent political activity, Fair Trade/B Corp certifications, and stakeholder-aligned governance structures. **Low scorers** have major SEC/EPA/CFPB enforcement actions, data breaches affecting millions, extreme partisan donation concentration, and product recall histories.

### A — Alive & Environmental
*Does the company treat the living planet as a stakeholder?*

This dimension measures energy and emissions (CDP Climate scores, Climate Neutral certification, SBTi commitments), water stewardship (CDP Water), land and habitat (USDA Organic, CDP Forests, industry deforestation risk), and product lifecycle (iFixit repairability, B Corp Environment score, Fair Trade traceability).

**High scorers** publish verified emissions data, hold certifications requiring third-party verification, and design products for longevity and repairability. **Low scorers** face EPA enforcement, fail to disclose to CDP, and have product lifecycles built for obsolescence.

### N — Natural Transparency
*Can you actually see what the company is doing?*

This dimension measures whether a company's disclosures, filings, and reporting are thorough enough to be verified and trusted. It covers reporting quality (GRI compliance, SEC filing transparency) and filing volume (are they filing the required forms on time and accurately?).

**High scorers** file everything legally required plus voluntary disclosures (GRI, CDP, SBTi), restate rarely, and have strong audit trails. **Low scorers** have restatement histories, late filings, and minimal voluntary disclosure.

### Why these five

Every dimension asks the same underlying question in a different form: **where has AI — or any form of scale-over-humanity — crossed the line from augmenting humans to replacing them without acknowledgment?**

- H asks: Are the people still here, still valued, still deciding?
- U asks: Is the care real, or simulated?
- M asks: Who's accountable when the algorithm makes a mistake?
- A asks: Is efficiency hiding environmental or social cost?
- N asks: Can you verify any of it?

A company can score well on all five while being deeply AI-enabled. That's the point. HI Grade measures *balance*, not AI absence.

---

## 3. The 19 sub-signals

Each HUMAN dimension is computed from 2-5 sub-signals. The current v1.1.0 engine scores **19 sub-signals**. Five additional sub-signals (H.4, N.1, N.3, N.4, U.5) are defined in the spec but not yet scored — they're in active development for v1.2+.

### H — Human Consciousness (4 sub-signals)

- **H.1 Workforce Valuation** — Revenue-per-employee vs. BLS industry median. Humanwashing flag triggers above 4× median.
- **H.2 Craft** — BLS wage data vs. national average, weighted by industry and certification presence.
- **H.3 Human Decision Depth** — SEC headcount disclosures, R&D per employee ratios, CEO pay ratio analysis.
- **H.5 Human Augmentation Index** — AI displacement signals from SEC filings, news monitoring, and headcount changes. *The AI-balance signal.*

### U — Understanding & Empathy (4 sub-signals)

- **U.1 Customer Empathy** — CFPB consumer complaint volume per revenue, complaint resolution rates, BBB ratings where available.
- **U.2 Worker Empathy** — Glassdoor employee ratings, OSHA violation severity, DOL wage/hour enforcement, BLS industry wage benchmarks.
- **U.3 Relational Integrity** — HRC Corporate Equality Index, Disability:IN DEI Index, EEOC discrimination charges, B Corp certification for stakeholder treatment.
- **U.4 Simulated Empathy Detection** — Glassdoor culture scores weighted against industry baseline for signal of AI-scripted vs. human-generated interactions.

### M — Morals & Ethics (5 sub-signals)

- **M.1 Pricing Ethics** — CFPB pricing-related complaints normalized to revenue.
- **M.2 Data Ethics** — Have I Been Pwned breach history, records exposed, breach frequency.
- **M.3 Market Ethics** — SEC litigation disclosure, EPA penalty totals, Fair Trade certification, USDA Organic certification (federal third-party supply chain verification).
- **M.4 Product Ethics** — CPSC recall counts, FDA warning letters, NHTSA investigations, Glassdoor management scores.
- **M.5 Stakeholder Governance** — B Corp certification (stakeholder-centric legal structure), 1% for the Planet membership (revenue-bound environmental pledge), FEC political donation concentration, IRS 990 corporate foundation giving.

### A — Alive & Environmental (4 sub-signals)

- **A.1 Energy & Emissions** — CDP Climate scores, Climate Neutral certification (measured + offset cradle-to-customer emissions), 1% for the Planet membership, SBTi commitments.
- **A.2 Water** — CDP Water Security scores, EPA water violation data.
- **A.3 Land & Habitat** — USDA Organic certification (federal soil health + no synthetic chemicals standard), CDP Forests, industry deforestation risk scoring, EPA violations 3-year window.
- **A.4 Product Lifecycle** — iFixit Repairability Index, B Corp Environment assessment, Fair Trade traceability, USDA Organic product tier, Climate Neutral product footprint accounting.

### N — Natural Transparency (2 sub-signals)

- **N.2 Reporting Quality** — GRI Sustainability Standards compliance, SEC filing transparency score, restatement history.
- **N.5 Filing Volume** — Total SEC filings, OpenCorporates registry depth, disclosure completeness.

For the full scoring ladder per sub-signal — exact thresholds, data sources, and weighting — see the [technical rubric on GitHub](https://github.com/thehibalance/hi/blob/main/RUBRIC.md). Every ladder is either **grounded** (derived from an authoritative source like a government threshold or certification standard) or **editorial** (chosen by HI Grade, with documented reasoning). We label each honestly.

---

## 4. Gold HI Grade — the v1.1.0 gate

A Gold HI Grade is the highest recognition HI Grade awards. It signals that a company has achieved balanced, documented, and currently-maintained performance across all five HUMAN dimensions.

Gold status is earned algorithmically, not purchased.

### The three gates

A company earns Gold when it passes **all three** gates:

**Gate 1 — Dimensions:** All five HUMAN dimensions must score **60 or higher**.

No single weak dimension is allowed. A company with H=72, U=71, M=68, A=70, N=59 fails Gold. The 59 on Natural Transparency disqualifies regardless of strength elsewhere. This prevents companies from averaging away a dimensional failure.

**Gate 2 — Evidence:** Each dimension must have **at least one real public source** grounding it.

A company cannot earn Gold on industry defaults alone. If H.1 for a company defaults to the industry median because we have no SEC data, no job-board data, and no HRC data, that dimension fails the evidence gate — even if the default happens to be 75.

Acceptable sources include SEC, EPA, BLS, CDP, Glassdoor, HRC, Disability:IN, B Corp, Fair Trade, USDA Organic, Climate Neutral, 1% for the Planet, and the other 30+ sources in the pipeline. Manual seed estimates do not count. Industry defaults do not count.

**Gate 3 — Momentum:** The company must not be in **warning or critical decay**.

HI Grade's Heartbeat monitors news, SEC 8-K filings, WARN Act notices, and other signals across a 90-day rolling window. Companies with recent mass layoffs, ethics scandals, CEO accountability events, or environmental incidents are flagged for decay even if their backward-looking dimension scores are strong.

This gate exists because of the "Oracle problem." When Oracle executed mass layoffs in early 2025, their backward-looking SEC filings still showed the pre-layoff workforce. A scoring system that only read last-quarter's 10-K would have given Oracle a high H score the day they cut 40% of US employees. HI Grade's momentum gate catches this in real time.

### Why three gates instead of one composite

A single weighted composite number — the approach most ESG frameworks use — averages away disqualifying signals. A company can be excellent on four dimensions and ethically compromised on the fifth, and still rate highly. HI Grade refuses to do this. Each dimension is an independent check.

The three gates work together:
- Dimensions gate: "Is every facet of this company meeting the bar?"
- Evidence gate: "Can we actually see the facets, or are we guessing?"
- Momentum gate: "Is this still true today, or only historically?"

A company that passes all three is not just scoring well on paper — it's currently, verifiably, and comprehensively living up to the standard.

### How a score is computed

At the highest level:

1. **Collection** — Every night, pipelines pull data from 42 public sources
2. **Sub-signal scoring** — Each sub-signal applies its published ladder (or documented heuristic) to produce a 0-100 score
3. **Dimension aggregation** — Sub-signals within a dimension are weighted and summed
4. **Composite calculation** — Dimensions are weighted and averaged for the composite score
5. **Gate evaluation** — The three Gold gates check the dimensions, evidence, and momentum independently
6. **Decay monitoring** — The Heartbeat system continuously watches for momentum changes

The full weighting matrix, dimension weights, and sub-signal ladders are published in the technical rubric and the source code at [github.com/thehibalance/hi](https://github.com/thehibalance/hi).

---

## 5. The AI-HI Balance principle

Every ESG framework was built before ChatGPT.

They measure environment, governance, social practices — but none of them measure what happens when a company replaces its humans with algorithms and keeps marketing to you like the humans are still there.

**HI Grade measures that.**

### What "balance" means

HI Grade is not anti-AI. A company can use AI extensively — for coding, for logistics, for customer service, for operations — and still earn a Gold HI Grade.

What HI Grade penalizes is **imbalance**: using AI to scale operations while claiming craft, replacing humans without transparency, removing people from decisions that affect other people, and hiding the AI boundary from customers.

The balance we measure has three components:

1. **Transparency** — Does the company tell you what's AI-driven and what's human?
2. **Craft preservation** — Are humans still making the judgment calls that require human judgment?
3. **Displacement accountability** — When AI replaces work, does the company invest in the displaced workers, or just pocket the savings?

A company that uses AI to help its engineers work faster, keeps humans in customer-facing roles, and discloses its AI use in public filings can score Gold. A company that outsources customer service to chatbots, removes humans from the loop, and markets itself as "high-touch" cannot.

### Measured without AI

HI Grade uses no AI in the scoring pipeline.

- No large language models summarizing ESG reports
- No neural networks classifying sentiment
- No machine learning inferring "good" or "bad"
- No AI-generated ratings of any kind

Every score is a deterministic computation on public data. Run the same code on the same data and get the same answer. No hallucinations. No probabilistic judgments. Every decision traceable.

We do use AI to help *build* the system — to write Python, draft documentation, and test edge cases. We don't use AI to *judge* any company. The distinction matters: LLMs are excellent for engineering work and explanation, and untrustworthy for the kind of consistent, auditable, high-stakes judgments ESG ratings require.

This is a deliberate architectural choice. The entire value proposition of HI Grade is reproducibility and trust. An LLM-generated score cannot be reproduced exactly, cannot be audited line-by-line, and cannot defend itself against "why did you rate us that way?" in a regulatory or legal context. Math and data can.

### Edge to cloud, no black boxes

Every piece of the HI Grade system is open:

- The scoring engine runs on Railway — you can see the commit hash that produced any score
- The website runs on GitHub Pages — the entire static site is in the repo
- The Chrome extension and iOS app hit the same public API every user can hit
- The data pipelines are open source
- The methodology — this document — is in the repo

There is no proprietary model. There is no "secret sauce." There is no black box.

If you disagree with a company's score, you can: read the data we used, read the code that computed it, propose a change via GitHub, and if you're right, we'll update the system.

---

## 6. Humanwashing, AHI, and PHI

HI Grade identifies three specific patterns that reveal AI-HI imbalance. Each is a detection system that flows into the dimension scores.

### Humanwashing™

Humanwashing is the practice of selling human craft while operating algorithmically. A company markets itself as handcrafted, personal, or artisanal — but their revenue-per-employee suggests most of the actual output comes from automation.

**How we detect it:** Revenue-per-employee (RPE) compared to the BLS industry median for the company's SIC code. A company at 1-2× its industry median is normal. A company at 4× or more triggers the humanwashing flag.

**Why it matters:** If a coffee brand sells its product with stories of farmers and small roasters, but their RPE is 8× the industry median, something doesn't add up. Either the "handcrafted" story is aspirational marketing covering extensive automation, or the company is extracting value at a rate that the "small, human" narrative disguises.

**How it flows:** The humanwashing flag penalizes H.1 (Workforce Valuation) directly. A flagged company cannot earn a high H.1 score no matter what other signals are present.

### Algorithmic Harm Index (AHI)

AHI measures the *scale* at which a company's algorithmic decisions affect humans. A platform that makes 1,000 automated moderation decisions per day has far lower AHI than one making 10 million. More decisions at algorithmic scale means more opportunities for systemic harm.

**How we detect it:** User base size, decision volume (where disclosed), complaint volume per million users (CFPB + BBB where applicable), algorithmic failure mode severity.

**Why it matters:** A bank's credit-decisioning algorithm affects one person at a time. A social media content-moderation algorithm affects billions at a time. Both can have bugs. AHI adjusts for the blast radius.

**How it flows:** AHI penalties flow into M.3 (Market Ethics) and U.4 (Simulated Empathy Detection), proportional to scale and disclosure.

### Product Harm Index (PHI)

PHI measures physical or digital safety failures of a company's products. Recalls, warning letters, breach disclosures, safety violations.

**How we detect it:** CPSC recalls (physical products), FDA warning letters (regulated products), NHTSA investigations (vehicles), HIBP breach records (digital products), EPA violations (environmental products).

**Why it matters:** Product quality is a proxy for how seriously a company takes its obligation to the humans using its products.

**How it flows:** PHI penalizes M.4 (Product Ethics) directly, weighted by severity.

### Why three separate systems

Each system measures a different surface:
- **Humanwashing** — the *narrative* the company tells
- **AHI** — the *algorithmic scale* they operate at
- **PHI** — the *physical/digital harm* they cause

A company can be clean on all three. Many are. A company can be compromised on just one and still have a serious issue to address. These are not the only signals in HI Grade, but they are the most direct measures of AI-HI imbalance and harm scale.

---

## 7. The 42 data sources

Every HI Grade is computed from 42 public data sources across five categories:

- **13 government & federal agencies** (SEC, EPA, BLS, CFPB, FEC, FDA, FTC, CPSC, OSHA, DOL, EEOC, NHTSA, USPTO) — refreshed nightly
- **7 financial & corporate sources** (Yahoo Finance, Finnhub, FMP, FRED, OpenCorporates, NewsAPI, CEO monitoring) — live API
- **17 public datasets** (Glassdoor, HRC CEI, Disability:IN DEI, CDP Climate/Water/Forests, GRI, SBTi, IRS 990, WARN Act, iFixit, BBB, HIBP, Alpha Vantage, layoff tracking, industry deforestation risk, industry RPE medians) — quarterly refresh
- **5 certification partners** (B Corp, Fair Trade USA/International, USDA Organic, Climate Neutral, 1% for the Planet) — quarterly manual review
- **10 computed aggregates** (revenue per employee, headcount change, R&D per employee, CEO pay ratio, insider trading patterns, filing transparency, patent flow, political donation concentration, consumer complaint density, safety violation severity) — computed nightly from the above

The complete list, with sub-signal mapping, refresh cadence, and coverage per source, is available at [thehibalance.org/sources](https://thehibalance.org/sources.html).

**No proprietary databases. No purchased ratings. No pay-to-play access. Every source is independent of HI Grade's funding or commercial relationships.**

---

## 8. What we measure vs. what we don't

This section exists because credibility requires honesty about limitations.

### Coverage

HI Grade currently scores **817 companies**. The coverage is skewed toward:

- Public US companies with SEC filings (high coverage)
- Major consumer brands (high coverage)
- Companies with third-party certifications (high coverage)
- Private companies without certifications (limited coverage)
- Non-US companies without US-traded stock (limited coverage)

If you search for a company and don't find them, it's usually because the data isn't there yet — not because they're unrateable.

### Data freshness

Refresh cadence varies by source:
- Government data (SEC, EPA, BLS, etc.) — refreshed nightly
- Public datasets (HRC, CDP, GRI, etc.) — refreshed quarterly
- Third-party certifications — refreshed quarterly via manual review (with API wiring planned post-launch)
- Heartbeat/decay signals — refreshed throughout the day from news sources

This means a score reflects the current best-available data, but some slow-moving signals (like a certification renewed last week) may take up to 90 days to appear in scoring.

### What we don't score

We do not currently score:
- Board composition (planned for v1.2)
- Supply chain depth beyond certified partners (planned for v1.2)
- Real-time AI usage disclosure (planned for v1.2)
- Geopolitical exposure (not planned)
- Short-term stock performance (intentionally excluded — HI Grade is not a financial signal)

### What we refuse to do

We do not:
- Accept payment from companies in exchange for rating, higher scores, or data access
- Use AI-generated content in scoring
- Keep our methodology private or proprietary
- Refuse to correct verified mistakes
- Score any company we cannot defend publicly

If a company believes their HI Grade is wrong, they can [request a review](https://thehibalance.org/#contact) with documented evidence. If they're right, we update the score and disclose the change.

### What we promise

- Methodology transparency (this document)
- Source transparency (the sources page)
- Code transparency (the GitHub repo)
- Error correction (disclosed publicly)
- No pay-to-play (ever)

---

## 9. Open source and how to verify

HI Grade is built to be verified.

### GitHub repository

**[github.com/thehibalance/hi](https://github.com/thehibalance/hi)** — the complete system, Apache 2.0 licensed

You can:
- Read the scoring engine (`pipeline/scoring_engine.py`)
- Read each data pipeline (`pipeline/*_pipeline.py`)
- Review the technical rubric (`RUBRIC.md`)
- File issues for bugs, improvements, or disagreements
- Fork the repo and run the entire pipeline on your own infrastructure

### API

**[api.thehibalance.org](https://api.thehibalance.org)** — the same API every user interface hits

You can query any company score, view sub-signal breakdowns, and see the data sources that produced each signal. All endpoints are public. Rate-limited for free use, with higher tiers for institutional users.

### Contact

Questions, feedback, disagreements: [hi@thehibalance.org](mailto:hi@thehibalance.org)

Request a company be scored: [thehibalance.org/#contact](https://thehibalance.org/#contact)

Found a bug in a score or methodology: [github.com/thehibalance/hi/issues](https://github.com/thehibalance/hi/issues)

---

## Version and license

**HI Grade Methodology v1.1.0**

Published: April 2026
License: Apache 2.0
Source: [github.com/thehibalance/hi](https://github.com/thehibalance/hi)

© Morf Innovations LLC. HI Grade™, HUMAN 100™, HUMAN Heartbeat™, HUMAN Shield™, HUMAN Lens™, HUMAN Genome™, HUMAN Contagion™, HUMAN Watermark™, HUMAN Wave™, HUMAN Consciousness™, Humanwashing™, Algorithmic Harm Index™, Product Harm Index™ are trademarks of Morf Innovations LLC. Patent pending.

---

*HI Grade is estimated from public data and is not financial, legal, or investment advice. Not affiliated with or endorsed by any company scored.*
