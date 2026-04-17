<div align="center">

<img src="https://raw.githubusercontent.com/thehibalance/hi/main/docs/logo-512.png" width="120" alt="HI."/>

# Human kind?

**Score every company. Five dimensions AI can't replace.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-v1.1.0-1B3A5C.svg)](https://thehibalance.org/#methodology)
[![API](https://img.shields.io/badge/API-live-16A34A.svg)](https://api.thehibalance.org)
[![Chrome](https://img.shields.io/badge/Chrome-Extension-C49B20.svg)](https://chromewebstore.google.com/detail/cpahbhdlmeinoaffjcpnnofgebcblkhg)
[![iOS](https://img.shields.io/badge/iOS-App%20Store-000.svg)](https://apps.apple.com/app/hi/id6761270596)

**[thehibalance.org](https://thehibalance.org)** · Built without AI to measure AI · Open source

</div>

---

## What is HI Grade?

For 500 years we've made decisions using four filters: **cost, time, convenience, risk.** We left out a fifth — **verified human impact.** Not "does this company feel ethical?" but _"does it treat humans well in ways that leave a data trail?"_

**HI Grade** measures how human a company is across five dimensions. Every company gets a score from 0 to 100, built from 19 active sub-signals and 42 free public data sources. Zero AI in the scoring engine. Zero pay-to-play. Zero self-reporting. Every score is reconstructable from public data.

Whether you're shopping, investing, hiring, researching, or building, HI Grade gives you one number with full audit trail.

## Try it in 30 seconds

```bash
curl https://api.thehibalance.org/api/v1/score/ticker/PTGN
```

Or install the **[Chrome Extension](https://chromewebstore.google.com/detail/cpahbhdlmeinoaffjcpnnofgebcblkhg)** and see every company's HI Grade as you browse.

## The HUMAN Framework

Five dimensions. Each measures something AI can't replace.

| | Dimension | Measures | Active Sub-Signals |
|---|---|---|---|
| 🧠 | **H — Human Consciousness** | Workforce investment, craft, human decision authority | H.1 H.2 H.3 |
| 💙 | **U — Understanding & Empathy** | Customer empathy, worker empathy, relational integrity | U.1 U.2 U.3 U.4 |
| ⚖️ | **M — Moral & Ethical Conduct** | Pricing, data, market, product, stakeholder ethics | M.1 M.2 M.3 M.4 M.5 |
| 🌍 | **A — Alive & Environmental** | Energy, water, land, product lifecycle | A.1 A.2 A.3 A.4 |
| 🔍 | **N — Natural Transparency** | Reporting quality, filing volume, disclosure depth | N.2 N.5 |

**19 active sub-signals. 6 deferred to v1.2** (H.4, H.5, U.5, A.5, N.1, N.3, N.4 — spec'd but not yet scored). Our [methodology page](https://thehibalance.org/#methodology) documents every formula and threshold.

## The Balanced Board

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

## 42 Data Sources, Zero AI

All free, public, auditable. No proprietary databases. No purchased ratings. No pay-to-play. No self-reporting surveys. No LLMs.

| Bucket | Count | Examples |
|---|---|---|
| 🏛️ **Government** | 13 | SEC EDGAR, EPA ECHO, BLS, CFPB, FEC, FDA, FTC, CPSC, OSHA, DOL, EEOC, NHTSA, USPTO |
| 💼 **Financial** | 7 | FMP, Finnhub, Yahoo Finance, Alpha Vantage, FRED, OpenCorporates, NewsAPI |
| 📊 **Public Datasets** | 17 | Glassdoor, HRC CEI, Disability:IN DEI, CDP (Climate/Water/Forests), GRI, SBTi, IRS 990, WARN Act, iFixit, BBB, HIBP, Layoffs.fyi |
| ✅ **Certifications** | 5 | B Corp, Fair Trade USA, USDA Organic, Climate Neutral, 1% for the Planet |
| 🧮 **Computed Aggregates** | 10 | Harm Documentation, AHI, CEO Accountability, RPE, Heartbeat Decay Index |

Full list and methodology per source: **[thehibalance.org/#sources](https://thehibalance.org/#sources)**

## The HUMAN Heartbeat

Companies change. HI Grade moves with them. The Heartbeat watches daily across:

- **SEC 8-K restructuring disclosures** (legally mandated within 4 days)
- **WARN Act notices** (federally mandated workforce reductions)
- **NewsAPI keyword surveillance** (150,000+ news sources)
- **Finnhub insider trading** + **CEO pipeline**

Decay levels: **Stable → Watch → Warning → Critical**. When Oracle laid off 40% of US employees in early 2025, backward-looking SEC filings still showed the pre-layoff workforce. The Heartbeat caught it.

This is what "scores that move" means. No other ethics framework does this daily.

## Known Limitations

We publish what we haven't solved yet — because a transparency framework that hides its own gaps is hypocritical. See [`RUBRIC.md`](RUBRIC.md) for the full Pass-1 inventory of which sub-signal ladders are **GROUNDED**, **PARTIAL**, or **UNGROUNDED** against external authorities.

**Current state (v1.1.0):**

- Several sub-signal scoring ladders use editorial tier cutoffs on authoritative data (e.g., CFPB complaints per $B revenue is authoritative; the tier cutoffs on it are editorial). This is the dominant pattern, explicitly flagged in `RUBRIC.md`.
- 6 sub-signals are spec'd but not yet scored (v1.2 target).
- Harm Documentation covers ~14 categories; historical harm detection pre-2020 is limited to the Major Harm Events dictionary.
- CFPB coverage is financial-services-heavy; ~80% of companies fall back to neutral defaults for U.1/M.1.
- iFixit repairability covers 15 companies; everyone else uses industry defaults.

**Active research:**

- Grounding UNGROUNDED ladders against external frameworks (BLS, SBTi, B Corp)
- Expanding Harm Documentation to pre-2020 events
- v1.2 sub-signals (H.4, H.5, U.5, A.5, N.1, N.3, N.4)
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
┌─ Data Collection (nightly, 180min budget) ─────────────────┐
│  SEC · EPA · BLS · CFPB · FEC · FDA · FTC · CPSC · OSHA    │
│  DOL · EEOC · NHTSA · USPTO · FMP · Finnhub · Yahoo        │
│  NewsAPI · CDP · HRC · Disability:IN · SBTi · GRI · 990    │
└────────────────────────────┬───────────────────────────────┘
                             │
┌─ Scoring Engine (deterministic, no AI) ────────────────────┐
│  19 active sub-signals → 5 dimensions → 1 composite (0-100)│
│  + 4 harm detection systems applied at dimension level     │
│  + 3-layer validation (input · output · MSSI)              │
└────────────────────────────┬───────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   REST API (32)     Chrome Extension     iOS App
   api.thehibalance    441+ brands        App Store
```

**Nightly pipeline:** GitHub Actions at midnight CST. Full pipeline runs in ~60-90 min; skip-collect quarterly re-score in ~5 min. Validation stops publication if anything looks wrong.

**3-layer validation:** 
1. Input validation — no negative headcounts, no impossible Glassdoor ratings
2. Output validation — score stability checks, distribution shape, known leaders
3. MSSI — Maximum Single-Source Impact — no one source moves a sub-signal more than 15 points

## Local Development

```bash
git clone https://github.com/thehibalance/hi.git
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

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to add a company, add a data source, or grind a sub-signal ladder.

## What Makes HI Different

| Framework | Misses |
|---|---|
| ESG (MSCI, Sustainalytics) | No AI displacement. No empathy detection. No humanwashing. Uses LLMs in scoring. Pay-to-play. |
| B Corp | No scoring granularity. No AI dimension. Self-reported. No real-time monitoring. |
| Fair Trade | Certifications only. No technology dimension. |
| Carbon Tools (CDP, Watershed) | Environmental only. |
| Credit Ratings (Moody's, S&P) | Financial only. |
| **HI Grade** | All five HUMAN dimensions. Zero AI. Auditable. Open source. |

We publish our methodology. We publish our limitations. Every sub-signal is auditable. Every score is reconstructable. No AI. No pay-to-play.

## Roadmap

| Capability | Status |
|---|---|
| Chrome Extension v1.1.7 | ✅ Shipped |
| iOS App v1.1.0 | In Apple review |
| Balanced Board methodology | ✅ Shipped |
| Harm Documentation (14 categories) | ✅ Shipped |
| 180-min quarterly workflow | ✅ Shipped |
| Safari extension | Planned |
| Firefox / Edge extensions | Planned |
| State of Human Intelligence report | Planned |
| EU CSRD + Companies House integration | Planned |
| Sub-signals H.4, H.5, U.5, A.5, N.1, N.3, N.4 | v1.2 target |
| Subsidiary Transparency Rule (SEC Exhibit 21) | v1.2 target |

## Intellectual Property

| Asset | Status |
|---|---|
| Provisional Patent (22 claims) | Filed — expires March 2027 |
| HI Grade™ | Trademark filed |
| Humanwashing™ | Common law |
| Algorithmic Harm Index™ | Common law |
| "Human kind?"™ | Trademark pending |
| HUMAN Grade Spec v1.1.0 whitepaper | Copyright registered |
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

The HI Balance · Patent Pending · HI Grade™ · Humanwashing™ · Algorithmic Harm Index™
Morf Innovations LLC · [@thehibalance](https://twitter.com/thehibalance) · [hi@thehibalance.org](mailto:hi@thehibalance.org)

</div>
