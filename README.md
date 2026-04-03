<p align="center">
  <img src="human-edge/icons/icon-128.png" alt="HI." width="80">
</p>

<h1 align="center">Think human intelligence.</h1>

*Built without AI to measure AI. 42 free data sources. 25 sub-signals. Zero AI in the scoring engine. The world's first ethical scoring framework for the age of AI.*

<p align="center">
  <img src="human-edge/icons/icon-128.png" alt="hi." width="28" style="vertical-align:middle"> measures how human a company is across five dimensions — the things AI can't replace: consciousness, empathy, ethics, environment, and transparency. Every company gets a score from 0 to 100. Brands that pass all 3 gates — with verified data — earn <strong>Gold HI Grade</strong>.
</p>

<p align="center">
🌐 <a href="https://thehibalance.org">thehibalance.org</a> · 🍎 <a href="https://apps.apple.com/app/hi/id6761270596">iOS App</a> · 🔌 <a href="https://chromewebstore.google.com/detail/cpahbhdlmeinoaffjcpnnofgebcblkhg">Chrome Extension</a> · 📡 <a href="https://api.thehibalance.org/api/v1/stats">API</a>
</p>

<p align="center">
🏛 The HI Balance · 📄 Patent Pending · ™ HI Grade — Morf Innovations LLC
</p>

---

## <img src="human-edge/icons/icon-128.png" alt="hi." width="28"> Gold HI Grade — 3 Gates

Every company gets a score from 0 to 100. No letters. No tiers. Just the number.

Pass all three gates — verified by 5+ independent data sources — and your score turns gold. The data decides. You can't buy it. You can't apply for it. The data proves it.

### 📊 Gate 1: Score

The composite score must exceed the adaptive threshold — calculated as **mean + 2 standard deviations** of the entire scored market, rounded to a whole number.

**This is a dynamic hybrid model.** The threshold recalculates quarterly as the market shifts. When companies improve, the bar rises. Companies force each other to be better. The math decides, not us.

**Two failsafes protect the standard:**
- **Hard floor:** The threshold never drops below 55
- **Ratchet:** The threshold can only go UP, never down

*Current threshold: 65 (Q2 2026)*

### ⚖ Gate 2: Balance

All 5 HUMAN dimensions must score **≥ 42**. Any dimension below 42? Not balanced. No exceptions.

*42 — the answer to life, the universe, and everything. Also the minimum per dimension to earn gold.*

### 🔒 Gate 3: Integrity

Two checks. Both must pass:

- **No Humanwashing™ flags** — the company isn't performing human values it doesn't practice
- **Algorithmic Harm Index™ < 30** — the company's algorithms aren't dividing, addicting, or manipulating people

### HI Grade Scale

| Color | Range | Meaning |
|-------|-------|---------|
| 🥇 Gold | ≥ threshold + 3 gates + verified | Passed score, balance, and integrity with real data |
| 🟢 Green | ≥ threshold | In Gold territory on score — but hasn't passed all 3 gates |
| 🟡 Amber | ≥ 42 | Balanced but below the Gold threshold |
| 🔴 Red | < 42 | Out of balance. At least one dimension is failing |
| ⬜ Gray | Pending | Estimated from public reporting, not yet verified |

---

## The HUMAN Framework

> *Five dimensions of humanity. Five elements. Love is what activates them all.*

| Dimension | Measures | What AI Replaces |
|-----------|----------|-----------------|
| 🧠 **H** — Human Consciousness | Creative agency, craft, CEO accountability, displacement | Automation, replacement |
| 💙 **U** — Understanding & Empathy | Genuine care, worker empathy, moral courage | Simulated empathy |
| ⚖️ **M** — Moral & Ethical Conduct | Pricing ethics, data ethics, CEO accountability, pay equity | Optimization at all costs |
| 🌍 **A** — Alive & Environmental | Energy, water, land, hardware lifecycle, resource stewardship | Hidden compute footprint |
| 🔍 **N** — Natural Transparency | AI disclosure, environmental reporting, humanwashing detection | Opacity, humanwashing |

### 25 Sub-Signals — All Equal Weight (0.20)

```
H: H.1 Creative Agency · H.2 Craft & Knowledge · H.3 Decision Depth · H.4 CEO Accountability · H.5 Displacement Trajectory
U: U.1 Customer Empathy · U.2 Worker Empathy · U.3 Relational Integrity · U.4 Simulated Empathy · U.5 Moral Courage
M: M.1 Pricing Ethics · M.2 Data Ethics · M.3 Market Ethics · M.4 Product Ethics · M.5 Political Ethics
A: A.1 Energy & Carbon · A.2 Water · A.3 Land & Habitat · A.4 Hardware Lifecycle · A.5 Resource Stewardship
N: N.1 AI Disclosure · N.2 Environmental Reporting · N.3 Labor Auditability · N.4 Humanwashing Detection · N.5 Disclosure Completeness
```

Every sub-signal is weighted equally at 0.20 within its dimension. Every dimension is weighted equally in the composite. The published methodology spec matches the code exactly.

---

## Confidence Tiers

Not all scores are equal. The system tells you how much data backs each score.

| Tier | Criteria | Gold Eligible |
|------|----------|---------------|
| **Verified** | 5+ real data sources | ✅ Yes |
| **Estimated** | 1-4 real data sources | ❌ No |
| **Pending** | Seed data only | ❌ No |

Pending companies show gray scores across all surfaces. Scores may change significantly once verified against 42 data sources.

---

## 42 Data Sources

Zero AI. Zero pay-to-play. Zero self-reporting. All free, public, and auditable.

**Government & Regulatory:** SEC EDGAR (10-K, 10-Q, DEF 14A, Form 4, 8-K), EPA ECHO, CFPB Complaints, OSHA, FTC, EEOC, USPTO, FDA, DOL, FEC, CPSC

**Disclosure & Standards:** CDP Climate, CDP Water, CDP Forests, GRI, SBTi, B Corp Directory, Charity Navigator

**Market & Financial:** Glassdoor, BLS Industry Benchmarks, Have I Been Pwned (HIBP), iFixit Repairability, Layoffs.fyi, WARN Act

**News & Signals:** NewsAPI, SEC 8-K filings, Finnhub, Alpha Vantage, Yahoo Finance

**Extended Pipeline:** BBB, IRS 990, OpenCorporates, HRC Corporate Equality Index, DEI Disability Index

---

## What Makes hi. Different

### The Scoring

- **25 sub-signals, all equal weight.** No single value outranks another. Published methodology matches code.
- **42 data sources, zero AI.** Every sub-signal has a deterministic data source. No black boxes. No surveys. No self-reporting.
- **Humanwashing™ detection.** Revenue/employee ratio vs 4x industry median, headcount vs AI spend, disclosed vs detected AI usage. Industry-normalized.
- **Algorithmic Harm Index™.** Cross-cutting penalty for algorithms that divide, addict, or manipulate.
- **HUMAN Heartbeat.** Real-time decay monitoring. Amazon and Meta at 100 (max decay). Oracle flagged at warning before 30,000 layoffs.

### The Architecture

- **Edge-to-cloud.** Chrome extension + iOS app + REST API (32 endpoints) + nightly pipeline. No other scoring framework ships across all surfaces.
- **Expandable sub-signals.** Tap any dimension to see sub-signal bars, coverage badge, and source list. Uniform across website, app, and extension.
- **Verified-first rankings.** API sorts verified companies before estimated before pending.
- **Nightly pipeline.** GitHub Actions at midnight CST. All 42 sources. Full scoring, merging, validation, and history tracking.

### Security

- **Read-only API** — no write endpoints exist
- **CORS whitelist** — thehibalance.org + browser extension + localhost only
- **Rate limiting** — 100 req/min global, 20 req/min on search
- **Input sanitization** — HTML escape, control chars stripped, query length capped
- **Security headers** — X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, strict Referrer-Policy
- **Extension** — zero AI, zero tracking, zero phone-home, zero user data collection
- **Domain collision prevention** — smart resolution prefers company whose name matches domain base

### The 10 HUMAN Features

| Feature | What It Does |
|---------|-------------|
| **HUMAN Genome™** | Sub-signal fingerprint — expandable in app, extension, and website |
| **HUMAN Decay** | Predicts score drops via trailing regression and real-time signals |
| **HUMAN Heartbeat™** | Real-time monitoring from layoff feeds, news, and SEC filings |
| **HUMAN Watermark** | Detects performative vs genuine empathy |
| **HUMAN Contagion** | Measures ethical ripple through industries |
| **HUMAN Shield** | AI displacement resistance score |
| **HUMAN 100™** | Top 100 companies, verified-first |
| **HUMAN Lens** | HI vs ESG gap detection |
| **HUMAN Wave** | Collective market pressure signals |
| **HUMAN Consciousness** | Company-level ethical footprint |

### Compared to Existing Frameworks

| Framework | What It Misses |
|-----------|---------------|
| **ESG (MSCI, Sustainalytics)** | No AI displacement. No empathy detection. No humanwashing |
| **B Corp** | No scoring granularity. No AI dimension. No real-time monitoring |
| **Fair Trade** | No AI measurement. No technology dimension |
| **Carbon Tools (CDP, Watershed)** | One dimension only |
| **Credit Ratings (Moody's, S&P)** | Financial only |

---

## Current Metrics

| Metric | Value |
|--------|-------|
| Companies scored | 818 |
| Verified (5+ sources) | 301 |
| Data sources | 42 |
| Sub-signals | 25/25 wired (18 strong) |
| Gold companies (verified only) | 4 |
| Scoring engine | v2.1, spec 1.1.0 |
| iOS app | v1.1.0 (live) |
| Chrome extension | v1.1.1 (live) |

---

## What's in This Repo

```
hi/
├── human-edge/                  # Chrome browser extension (Manifest V3)
│   ├── manifest.json
│   ├── background.js            # Service worker + cloud sync
│   ├── content.js               # Human silhouette pill + full panel + 3 gates
│   ├── content.css
│   └── lib/
│       ├── seed-data.js         # Seed companies (pending verification)
│       ├── engine.js            # Deterministic engine + 3 gates
│       └── db.js
│
├── pipeline/                    # Cloud scoring pipeline
│   ├── run_all.py               # collect → score → merge → features
│   ├── scoring_engine.py        # v2.1 (25 sub-signals, equal weights)
│   ├── data_collector.py        # 42 data sources
│   ├── api_server.py            # REST API (Flask, 32 endpoints)
│   └── [42 data pipelines]
│
├── docs/                        # Website (GitHub Pages)
│   ├── index.html               # thehibalance.org
│   ├── privacy.html
│   └── CNAME
│
├── .github/workflows/
│   └── daily-pipeline.yml       # Daily + quarterly automation
│
├── LICENSE                      # Apache 2.0
└── README.md
```

## Privacy

The extension collects **zero user data**. No tracking, no analytics, no cookies, no browsing history. The only network request is a domain lookup to our scoring API. No personal information is transmitted. Full policy: [thehibalance.org/privacy.html](https://thehibalance.org/privacy.html)

---

## Quick Start

```bash
# Extension
git clone https://github.com/thehibalance/hi.git
# chrome://extensions → Developer mode → Load unpacked → human-edge/

# Pipeline
cd pipeline && python3 run_all.py

# Quarterly (recalculates Gold threshold)
python3 run_all.py --quarterly
```

## Automation

| Schedule | Mode | What Happens |
|----------|------|-------------|
| Daily (midnight CST) | Incremental | All 42 sources, commits scores |
| Quarterly (Jan/Apr/Jul/Oct 1) | Full refresh | Recalculates Gold threshold |
| Manual | Your choice | Trigger from Actions tab |

## API

Base URL: `https://api.thehibalance.org` · Free · No auth required

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/stats` | Stats + Gold threshold |
| `GET /api/v1/score/{domain}` | Score by domain |
| `GET /api/v1/score/ticker/{ticker}` | Score by ticker |
| `GET /api/v1/search?q={query}` | Search companies |
| `GET /api/v1/grades/top?limit=10` | Top companies (verified first) |
| `GET /api/v1/heartbeat/pulse` | Ecosystem pulse |
| `GET /api/v1/heartbeat/alerts` | Decay alerts |
| `GET /api/v1/human100` | HUMAN 100 Index |

Response includes `score_status`: `verified`, `estimated`, or `pending`.

## Intellectual Property

| Asset | Status |
|-------|--------|
| Provisional Patent | Filed |
| HI Grade™ | Common law |
| Humanwashing™ | Common law |
| Algorithmic Harm Index™ | Common law |
| Copyright | Registered |
| Open source | Apache 2.0 |

## What's Next

| Capability | Status |
|-----------|--------|
| Phone extension (App Intents + Shortcuts) | Coming soon |
| Safari extension | Coming soon |
| Edge / Firefox extensions | Planned |
| State of Human Intelligence report | Planned |
| International data sources (EU CSRD, Companies House) | Planned |

---

<p align="center">
  <img src="human-edge/icons/icon-128.png" alt="hi." width="48"><br>
  <strong>Think human intelligence.</strong><br><br>
  <a href="https://thehibalance.org">thehibalance.org</a> · <a href="https://apps.apple.com/app/hi/id6761270596">iOS App</a> · <a href="https://chromewebstore.google.com/detail/cpahbhdlmeinoaffjcpnnofgebcblkhg">Chrome Extension</a><br>
  The HI Balance · Patent Pending · HI Grade™ · Humanwashing™ · Algorithmic Harm Index™<br>
  Morf Innovations LLC · @thehibalance
</p>
