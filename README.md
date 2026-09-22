<div align="center">

<img src="https://raw.githubusercontent.com/thehibalance/hi/main/docs/logo-512.png" width="120" alt="HI."/>

# Human kind?

**Score every company. Five dimensions AI can't replace.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-v1.4.0-1B3A5C.svg)](https://thehibalance.org/#methodology)
[![API](https://img.shields.io/badge/API-live-16A34A.svg)](https://api.thehibalance.org)
[![Chrome](https://img.shields.io/badge/Chrome-Extension-C49B20.svg)](https://chromewebstore.google.com/detail/cpahbhdlmeinoaffjcpnnofgebcblkhg)
[![iOS](https://img.shields.io/badge/iOS-App%20Store-000.svg)](https://apps.apple.com/app/hi/id6761270596)

**[thehibalance.org](https://thehibalance.org)** · No AI in the scoring · Open source

</div>

---

## What is HI Grade™?

For 500 years we've made decisions using four filters: **cost, time, convenience, risk.** We left out a fifth — **verified human impact.** Not "does this company feel ethical?" but _"does it treat humans well in ways that leave a data trail?"_

**HI Grade** measures how human a company is across five dimensions. Every company gets a score from 0 to 100, built from 19 active sub-signals and public data: 22 sources feed today's scores, out of 42 integrated. Zero AI in the scoring engine. Zero pay-to-play. Every pipeline-scored company can be reconstructed from public data.

Whether you're shopping, investing, hiring, researching, or building, HI Grade gives you one number with full audit trail.

## Try it in 30 seconds

```bash
curl https://api.thehibalance.org/api/v1/score/ticker/AAPL
```

Or install the **[Chrome Extension](https://chromewebstore.google.com/detail/cpahbhdlmeinoaffjcpnnofgebcblkhg)** and see every company's HI Grade as you browse.

## The HUMAN Framework

Five dimensions. Each measures something AI can't replace.

| | Dimension | Measures | Active Sub-Signals |
|---|---|---|---|
| 🧠 | **H — Human Consciousness** | Workforce, craft, decision depth, augmentation | H.1 H.2 H.3 H.5 |
| 💙 | **U — Understanding & Empathy** | Customer empathy, worker empathy, relational integrity | U.1 U.2 U.3 U.4 |
| ⚖️ | **M — Moral & Ethical Conduct** | Pricing, data, market, product, stakeholder ethics | M.1 M.2 M.3 M.4 M.5 |
| 🌍 | **A — Alive & Environmental** | Energy, water, land, product lifecycle | A.1 A.2 A.3 A.4 |
| 🔍 | **N — Natural Transparency** | Reporting quality, filing volume, disclosure depth | N.2 N.5 |

**19 active sub-signals. 5 more defined but not yet scored** (H.4, U.5, N.1, N.3, N.4). Our [methodology page](https://thehibalance.org/#methodology) documents every formula and threshold.

## What's new in v1.4

**The nightly run actually refreshes data again.** Every data file looked new to the pipeline after each checkout, so
for months it re-scored April data instead of collecting fresh records. Timestamps are now restored from the
repository's own history, a fetch that comes back empty never overwrites a stored value, and collection works
through the oldest data first within a time budget.

**Collected data finally reaches the scores.** The engine read summary files that hadn't been rebuilt since April.
A new step folds each night's results in, with evidence gates: industry defaults never count as evidence, and a
source has to produce a real record to count at all.

**Three broken matchers found and dealt with.** CFPB returned zero complaints for nearly every company (withdrawn
until fixed). Have I Been Pwned matched name fragments, blaming companies for other sites' breaches (now matched by
exact domain). FEC scored "no committees found" as clean political conduct (now only counts real filings).

**What it cost us, on purpose:** average scores moved less than a point, but coverage fell from 7.8 to 7.3 signals
per company, because evidence we couldn't stand behind was removed.

## What's new in v1.3

**Industry calibration (v1.3.0, v1.3.1).** H.1 compares each company's revenue per employee with its industry. The industry medians used to be hand-set and were off by up to 2.9×, so H.1 was measuring industry rather than behavior. Medians are now measured from the companies we score, REITs and industrial chemicals have their own peer groups, and **50 humanwashing flags that had been issued in error were withdrawn.**

**Deploys are verified.** After every nightly run, the workflow checks that the live API is serving the scores it just published, and fails loudly if not.

**Honest status labels.** The rubric and the sources page now show which sub-signals rest on authoritative data, and which sources are feeding scores today versus integrated but not yet producing data.

**Composite Floor Rule.** If any HUMAN dimension scores below 42, the composite is capped at 50. See `RUBRIC.md` for live examples.

## The Balanced Board™

Most frameworks hide weak dimensions inside a composite average. HI refuses. The **Balanced Board** highlights companies where **every one of the five HUMAN dimensions scores ≥ 60**. No gaps. No hiding.

A company can have a high composite score and still fail the Balanced Board — a red dimension is a red dimension. Composite numbers are navy everywhere; the dimension bars do the storytelling.

The Balanced Board is a descriptive property, not a prestige tier. The math decides, not us.

## Harm Documentation

Public-record harm flows directly into dimension scores. Anchored to DOJ/SEC/state AG records, CDC/NIH attribution data, and court findings.

| System | What it catches | Affects |
|---|---|---|
| **Humanwashing™** | Selling human craft while operating algorithmically | H.1 |
| **Algorithmic Harm Index™** | Algorithmic decisions at scale (blast radius adjusted) | M.3, U.4 |
| **Product Harm Index** | Physical/digital product safety failures | M.4 |
| **Harm Documentation** | Court settlements, attributed deaths, knowing concealment, weapons | M.3 + M.4 |

### "Humans can still choose"

HD does **not** penalize companies for selling products consumers knowingly choose — sugary beverages, alcohol, gambling, unflavored tobacco. These may cause harm, but it flows from informed consumer choice. **HI Grade is not the consumer's parent.**

HD **does** penalize when consent was not possible:

- **Hidden risk** — company knew about a risk and concealed it (J&J talc, tobacco MSA, Pfizer Bextra)
- **Doctor-mediated harm** — pharma companies that misrepresented drug safety to prescribers
- **Weapons** — products designed to harm humans who did not consent to being targeted
- **Environmental contamination** — PFAS, asbestos, unconsenting populations

This is why Lockheed Martin's composite dropped from 69 to 53 when weapons HD shipped. The math caught up with reality.

## Public Data, Zero AI

Free and public, apart from one paid financial feed (FMP). No purchased ratings. No pay-to-play. No LLMs. **22 sources feed today's scores; 42 are integrated.**

| | Sources |
|---|---|
| ✅ **In scores today** (examples) | SEC EDGAR, EPA ECHO, FDA, FTC, FEC, EEOC, FMP, Yahoo Finance, Glassdoor, HRC CEI, Disability:IN, CDP, GRI, SBTi, BBB, iFixit, B Corp, USDA Organic |
| 🔧 **Withheld or rebuilding** (v1.4.0) | CFPB (matching broken — withdrawn), HIBP (re-matching by domain, company by company) |
| ⏳ **Integrated, not yet producing data** | OSHA, DOL, USPTO, CPSC, NHTSA, BLS, IRS 990, WARN Act, Layoffs.fyi, FRED, OpenCorporates, NewsAPI, Alpha Vantage, Finnhub |

The live list comes from the API: `curl https://api.thehibalance.org/api/v1/stats` (`data_sources_list`). Per-source details and status badges: **[thehibalance.org/#sources](https://thehibalance.org/#sources)**

## The HUMAN Heartbeat

Companies change. HI Grade is built to move with them. The Heartbeat watches for:

- **SEC 8-K restructuring disclosures** (legally mandated within 4 days)
- **WARN Act notices** (federally mandated workforce reductions)
- **News coverage** (NewsAPI)
- **Insider trading and CEO changes** (Finnhub)

Decay levels: **Stable → Watch → Warning → Critical**. When a company announces mass layoffs, its latest 10-K can show the pre-layoff workforce for months. The Heartbeat exists so the score doesn't wait for the next annual filing.

**Today:** the SEC feed is live; WARN, NewsAPI and Finnhub are integrated but not yet producing data.

## Known Limitations

We publish what we haven't solved yet — because a transparency framework that hides its own gaps is hypocritical. See [`RUBRIC.md`](RUBRIC.md) for every sub-signal's status: **GROUNDED**, **PARTIAL**, or **UNGROUNDED**.

**Current state (v1.4.0):**

- **No sub-signal is fully grounded yet.** 13 are PARTIAL (authoritative data, tier cutoffs we chose) and 6 are UNGROUNDED. Grounding them is the research priority.
- **Most scores rest on partial data.** The median company has real data behind 7 of 19 sub-signals (mean 7.3 after v1.4.0 removed evidence we couldn't stand behind); the rest are neutral 50s, which pulls scores toward the middle.
- **The floor rule is a cliff.** A dimension at 42.1 keeps the full composite; at 41.9 the composite is capped at 50.
- **About 95 companies carry hand-entered seed data** (`Manual Scoring` in the API). Those parts of their scores aren't reproducible from the pipeline.
- **No customer-complaint data right now.** CFPB scores were withdrawn in v1.4.0 after the company matching proved broken. U.1 and M.1 fall back to employee ratings or a neutral 50 until it's fixed.
- **Breach history is rebuilding.** Matching is now by exact domain, and companies with no website on file can't be checked yet.
- 5 sub-signals are defined but not yet scored.
- iFixit repairability covers 15 companies; everyone else uses certifications, CDP Forests, or an industry default.
- Harm Documentation covers ~14 categories; pre-2020 harm is limited to the Major Harm Events dictionary.

**Active research:**

- Grounding PARTIAL and UNGROUNDED ladders against external frameworks (BLS, SBTi, GRI, B Corp)
- Bringing the integrated-but-silent sources online (OSHA, DOL, USPTO, CPSC, BLS)
- The 5 unscored sub-signals (H.4, U.5, N.1, N.3, N.4)
- International data sources (EU CSRD, Companies House)

If you spot a score that seems wrong, **[open an issue](https://github.com/thehibalance/hi/issues/new)** with the company name, ticker, and what you think the correct answer is. We respond.

## API

Base URL: `https://api.thehibalance.org` · Free · No auth required · Rate limited 100 req/min

```bash
# Single company by ticker
curl https://api.thehibalance.org/api/v1/score/ticker/AAPL

# Search
curl 'https://api.thehibalance.org/api/v1/search?q=patagonia'

# Top companies (verified-first)
curl https://api.thehibalance.org/api/v1/grades/top?limit=10

# The Heartbeat pulse
curl https://api.thehibalance.org/api/v1/heartbeat/pulse

# Balanced Board members
curl https://api.thehibalance.org/api/v1/grades/top?balanced=true
```

**32 endpoints.** Full reference: [thehibalance.org/api](https://thehibalance.org/api)

Each response includes `score_status`: `verified`, `estimated`, or `pending` — and a `harm_documentation` object when applicable. Every number traceable to its source.

## Architecture

```
┌─ Data Collection (nightly) ────────────────────────────────┐
│  SEC · EPA · CFPB · FEC · FDA · FTC · EEOC · FMP · Yahoo   │
│  Glassdoor · CDP · HRC · Disability:IN · BBB · HIBP        │
│  iFixit · B Corp · USDA Organic  (22 producing, 42 wired)  │
└────────────────────────────┬───────────────────────────────┘
                             │
┌─ Scoring Engine (deterministic, no AI) ────────────────────┐
│  19 active sub-signals → 5 dimensions → 1 composite (0-100)│
│  + 4 harm detection systems applied at dimension level     │
│  + 3-layer validation — critical problems stop publishing  │
└────────────────────────────┬───────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   REST API (32)     Chrome Extension     iOS App
   api.thehibalance   as you browse       App Store
```

**Nightly pipeline:** GitHub Actions collects, scores, validates, and commits `all_scores.json`. Railway redeploys the API, and the workflow then checks that the live API is serving exactly what was committed.

**3-layer validation** (a critical problem stops the run; yesterday's scores stay live):
1. Input validation — impossible values rejected (headcount above 3M, revenue/employee above $50M, 80%+ headcount swings, scores outside 0–100)
2. Output validation — distribution shape, minimum company count, composites that move 15+ points flagged
3. MSSI — Maximum Single-Source Impact — any sub-signal moved 15+ points by a single source is flagged for review (a check today, not an automatic cap)

## Local Development

```bash
git clone https://github.com/thehibalance/hi.git   # see note below for macOS / Windows
cd hi/pipeline
pip install -r requirements.txt

# Full pipeline (nightly run equivalent, ~60min)
python3 run_all.py

# Re-score from cached data (~5min)
python3 run_all.py --skip-collect

# Quarterly threshold recalculation
python3 run_all.py --quarterly

# Start API locally (port 8080)
python3 api_server.py --port 8080
```

**macOS / Windows note:** a few files in `pipeline/data/subsignals/` differ only by upper/lower case (e.g. `IBM.json` and `ibm.json`), which case-insensitive file systems can't hold side by side. Git will warn about them on checkout; everything else works. A cleanup is on the roadmap.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to add a company, add a data source, or grind a sub-signal ladder.

## What Makes HI Different

| Framework | Misses |
|---|---|
| ESG (MSCI, Sustainalytics) | No AI displacement. No empathy detection. No humanwashing. Proprietary methods behind a subscription. |
| B Corp | Certification, not a comparable score across all companies. No AI dimension. No real-time monitoring. |
| Fair Trade | Certifications only. No technology dimension. |
| Carbon Tools (CDP, Watershed) | Environmental only. |
| Credit Ratings (Moody's, S&P) | Financial only. |
| **HI Grade** | All five HUMAN dimensions. Zero AI in scoring. Auditable. Open source. |

We publish our methodology. We publish our limitations. Every sub-signal is auditable. Every pipeline score is reconstructable. No AI in scoring. No pay-to-play.

## Roadmap

| Capability | Status |
|---|---|
| Chrome Extension | ✅ Shipped |
| iOS App | ✅ Shipped |
| Balanced Board methodology | ✅ Shipped |
| Harm Documentation (14 categories) | ✅ Shipped |
| Industry calibration (measured medians) | ✅ Shipped v1.3.0 |
| Nightly deploy verification | ✅ Shipped |
| Nightly raw-data refresh fix | In progress |
| Integrated sources producing (OSHA, DOL, USPTO, CPSC, BLS) | In progress |
| Graduated floor rule (replace the 42 cliff) | Researching |
| Safari extension | Planned |
| Firefox / Edge extensions | Planned |
| State of Human Intelligence report | Planned |
| EU CSRD + Companies House integration | Planned |
| Sub-signals H.4, U.5, N.1, N.3, N.4 | Planned |
| Subsidiary Transparency Rule (SEC Exhibit 21) | Planned |

## Intellectual Property

| Asset | Status |
|---|---|
| Provisional Patent (22 claims) | Filed — expires March 2027 |
| HI Grade™ | Trademark filed |
| Humanwashing™ | Common law |
| Algorithmic Harm Index™ | Common law |
| "Human kind?"™ | Trademark pending |
| HUMAN Grade Spec v1.2.0 whitepaper | Copyright registered |
| Methodology + scoring engine | Apache 2.0 (see [LICENSE](LICENSE)) |

## Contributing

Pull requests welcome. Issues especially welcome — we want to hear when a score looks wrong. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

**Three kinds of contributions we specifically need:**

1. **Score challenges** — you think company X should be higher/lower? Open an issue with evidence, we investigate.
2. **Data source additions** — proposing a new public, free, auditable data source? PR with docstring + pipeline integration.
3. **Ladder grounding** — got an academic paper or regulatory framework that could replace one of our editorial thresholds? Gold.

## Acknowledgments

Built on public data from the SEC, EPA, BLS, CFPB, FEC, FDA, FTC, CPSC, OSHA, DOL, EEOC, NHTSA, USPTO. These agencies make HI Grade possible. Government transparency is a public good.

Built on methodology in part from CDP, GRI, SBTi, B Corp, Fair Trade, HRC, Disability:IN. Their work predates ours and informs ours.

## License

Methodology, scoring engine, API server, and pipeline code: **Apache 2.0** — see [LICENSE](LICENSE).

Chrome extension and iOS app: source Apache 2.0. Distributed binaries are subject to the Chrome Web Store Developer Agreement and Apple Developer Program License Agreement, respectively.

Trademarks (HI Grade™, Humanwashing™, Algorithmic Harm Index™, Human kind?™) are property of Morf Innovations LLC and not covered by the Apache 2.0 license. See [NOTICE](NOTICE) for usage guidelines.

---

<div align="center">

## hi.

**Human kind?**

[thehibalance.org](https://thehibalance.org) · [Chrome Extension](https://chromewebstore.google.com/detail/cpahbhdlmeinoaffjcpnnofgebcblkhg) · [iOS App](https://apps.apple.com/app/hi/id6761270596) · [API](https://api.thehibalance.org) · [Methodology](https://thehibalance.org/#methodology) · [Sources](https://thehibalance.org/#sources)

The HI Balance™ · Patent Pending · HI Grade™ · Humanwashing™ · Algorithmic Harm Index™
Morf Innovations LLC · [@thehibalance](https://twitter.com/thehibalance) · [hi@thehibalance.org](mailto:hi@thehibalance.org)

</div>
