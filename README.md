# HI.

> **HI Grade™** — The balance between humans and technology, measured.

**HI.** is the first edge-to-cloud scoring framework that measures how human a company is. Five dimensions — the things AI can't be: conscious, empathetic, ethical, alive, and transparent. Open source methodology. Patent pending.

🌐 [thehibalance.org](https://thehibalance.org) · 🏛 The Deep Thought Foundation · 📄 Patent Pending · ™ HI Grade — Morf Innovations LLC

---

## Architecture

```
┌───────────────────────────────────┐
│           EDGE NODE               │
│     (Browser Extension)           │
│                                   │
│  • Zero AI. Zero black boxes.     │
│  • Deterministic scoring engine   │
│  • AI Toggle + Equalizer          │
│  • Mini pill → full sidebar       │
│  • HUMAN Genome strip             │
│  • Heartbeat decay display        │
│  • Offline: 206 seed companies    │
│  • Online: 440+ from cloud API    │
│                                   │
│  "Every line of code is           │
│   auditable, every decision       │
│   is traceable."                  │
│                                   │
└──────────┬────────────────────────┘
           │ Delta Sync
           ▼
┌───────────────────────────────────┐
│           CLOUD LAYER             │
│     (Railway + GitHub Pages)      │
│                                   │
│  REST API (Flask, 32 endpoints)   │
│  • 18 data pipelines              │
│  • Scoring engine v2              │
│  • 440+ companies                 │
│  • 10 HUMAN features (all live)   │
│  • Search aliases + dedup         │
│  • HUMAN Heartbeat (6 feeds)      │
│  • HUMAN 100 Index                │
│  • HUMAN Genome                   │
│  • HUMAN Lens                     │
│  • HUMAN Shield                   │
│  • Balance floor rule             │
│                                   │
│  AI Enhancement Layer (planned)   │
│  • NLP on SEC filings             │
│  • ML humanwashing detection      │
│  • Predictive decay               │
│  • Toggle: OFF by default         │
│                                   │
└───────────────────────────────────┘
```

The edge node runs **zero AI**. The cloud computes scores from **18 free public data sources**. The AI Enhancement Layer improves inputs — it never changes the scoring formula.

---

## Live Now

- **Website**: [thehibalance.org](https://thehibalance.org) — Search 440+ companies, all 10 HUMAN features, 3-tab dropdown nav
- **API**: [api.thehibalance.org](https://api.thehibalance.org/api/v1/stats) — Free public REST API (32 endpoints)
- **Extension**: Chrome + Safari — mini pill badge, full sidebar panel, AI Toggle, Equalizer
- **Nav**: HI ▾ (App, Extension, API) · HUMAN ▾ (all 10 features) · About HI

---

## 10 HUMAN Features (All Live, Patent Pending)

| # | Feature | Description |
|---|---------|-------------|
| 1 | **HUMAN 100 Index** | ETF-licensable top 100 most human public companies |
| 2 | **HUMAN Heartbeat** | Real-time score decay detection from 6 feeds |
| 3 | **HUMAN Decay** | Per-company decay score 0-100 with alert levels |
| 4 | **HUMAN Shield** | AI displacement resistance — 6 component moat score |
| 5 | **HUMAN Lens** | HI vs ESG gap detection — where traditional ratings miss |
| 6 | **HUMAN Genome** | Sub-signal fingerprint of every company |
| 7 | **HUMAN Contagion** | Industry ethics ripple — how behavior spreads |
| 8 | **HUMAN Watermark** | Real vs performative empathy detection |
| 9 | **HUMAN Wave** | Collective market pressure by dimension and industry |
| 10 | **HUMAN Consciousness** | Consumer ethical footprint — personal portfolio score |

---

## What's in this repo

```
hi/
├── human-edge/                  # Chrome browser extension (Manifest V3)
│   ├── manifest.json            # Extension config (v0.3.0)
│   ├── background.js            # Service worker + cloud sync + heartbeat pulse
│   ├── content.js               # Mini pill + full panel + genome + heartbeat
│   ├── content.css              # Mini pill + panel + dark mode styles
│   ├── popup.html               # Extension popup UI
│   ├── popup.js                 # Popup controller + cloud sync
│   └── lib/
│       ├── seed-data.js         # 206 hand-scored companies
│       ├── engine.js            # Deterministic scoring engine (NO AI)
│       └── db.js                # Database layer
│
├── pipeline/                    # Cloud scoring pipeline (18 data sources)
│   ├── sec_edgar_pipeline.py    # SEC EDGAR — headcount, revenue, R&D, filings
│   ├── epa_echo_pipeline.py     # EPA ECHO — environmental violations, penalties
│   ├── bls_pipeline.py          # BLS — industry wage & employment benchmarks
│   ├── cdp_pipeline.py          # CDP — climate disclosure scores
│   ├── job_board_pipeline.py    # Job Boards — AI hiring velocity
│   ├── glassdoor_pipeline.py    # Glassdoor — employee ratings, CEO approval
│   ├── dei_pipeline.py          # AAPD/DEI — disability inclusion
│   ├── hrc_pipeline.py          # HRC/CEI — LGBTQ+ inclusion
│   ├── yahoo_pipeline.py        # Yahoo Finance — headcount, revenue, market cap
│   ├── alpha_vantage_pipeline.py # Alpha Vantage — earnings, margins
│   ├── fmp_pipeline.py          # FMP — full financials, ratios
│   ├── finnhub_pipeline.py      # Finnhub — ESG scores, news, sentiment
│   ├── fred_pipeline.py         # FRED — 18 economic benchmark series
│   ├── newsapi_pipeline.py      # NewsAPI — 150K+ media sources
│   ├── layoffs_pipeline.py      # Layoffs.fyi — tech layoff history
│   ├── sec_8k_pipeline.py       # SEC 8-K — material event filings
│   ├── warn_pipeline.py         # WARN Act — legally filed layoff notices
│   ├── ceo_pipeline.py          # CEO — pay ratio, approval, accountability
│   ├── scoring_engine.py        # Multi-source HUMAN dimension scoring (v2)
│   ├── heartbeat_monitor.py     # HUMAN Heartbeat: 6-feed decay detection
│   ├── human100_index.py        # HUMAN 100 Index generator
│   ├── grade_arbitrage.py       # HUMAN Lens: HI vs ESG gap
│   ├── ethical_moat.py          # HUMAN Shield: AI displacement resistance
│   ├── contagion_effect.py      # HUMAN Contagion: supply chain ripple
│   ├── consumer_consciousness.py # HUMAN Consciousness: personal footprint
│   ├── empathy_watermark.py     # HUMAN Watermark: real vs performative
│   ├── collective_bargaining.py # HUMAN Wave: market pressure
│   ├── api_server.py            # REST API server (Flask, 32 endpoints)
│   ├── run_all.py               # Single command runner (daily/weekly/monthly)
│   └── sp500_domains.py         # Domain mappings
│
├── docs/                        # Website (GitHub Pages)
│   ├── index.html               # thehibalance.org — single-page app
│   └── CNAME                    # Custom domain config
│
├── LICENSE                      # AGPL-3.0 (extension) / Apache 2.0 (methodology)
├── CONTRIBUTING.md
└── README.md
```

## Quick Start

### Browser Extension (no server needed)

1. Clone this repo: `git clone https://github.com/thehibalance/hi.git`
2. Open `chrome://extensions` in Chrome
3. Enable **Developer mode**
4. Click **Load unpacked** → select the `human-edge/` folder
5. Visit any website — mini pill badge appears for scored companies

The extension starts as a small pill (grade letter + score). Click it → full sidebar panel with all dimensions, genome, heartbeat, and AI Toggle.

### Daily Pipeline (one command)

```bash
cd pipeline
python3 run_all.py --daily --push    # Run daily pipelines + 10 HUMAN features + auto-push
python3 run_all.py --weekly --push   # Weekly pipelines + push
python3 run_all.py --monthly --push  # Full run + push
```

---

## The HI Grade™ Scale

| Grade | Score | Satire |
|-------|-------|--------|
| **HI Certified** | 90-100 | Humans and tech, in harmony. This is what balance looks like. |
| **A** | 80-89 | AI does the math. Humans do the handshakes. Nailed it. |
| **B** | 60-79 | Humans and machines, learning to share the remote. |
| **C** | 42-59 | 42. The answer to everything. Now what's the question? |
| **F** | 0-41 | Don't panic. Every journey starts somewhere. |

The pass/fail line is **42** — the answer to life, the universe, and everything.

**Balance Floor Rule**: Any dimension below 42 caps the grade at C. You can't claim balance when any dimension is failing.

## The HUMAN Framework

| Dimension | Measures | What AI Replaces |
|-----------|----------|-----------------|
| 🧠 **H** — Human Consciousness | Creative agency, craft, accountability | Automation, displacement |
| 💙 **U** — Understanding & Empathy | Genuine care, emotional presence | Simulated empathy |
| ⚖️ **M** — Moral & Ethical Conduct | Principled action, CEO accountability, pay equity | Optimization at all costs |
| 🌍 **A** — Alive & Environmental | True ecological cost incl. AI infrastructure | Hidden compute footprint |
| 🔍 **N** — Natural Transparency | Honest disclosure of AI usage | Humanwashing, opacity |

## Data Sources (18)

| # | Source | Dimensions | Schedule |
|---|--------|-----------|----------|
| 1 | SEC EDGAR | H, M, N | Monthly |
| 2 | EPA ECHO | A, M | Monthly |
| 3 | BLS | H, U | Monthly |
| 4 | CDP | A, N | Monthly |
| 5 | Job Boards | H | Monthly |
| 6 | Glassdoor | U, M | Monthly |
| 7 | AAPD/DEI | U, M | Weekly |
| 8 | HRC/CEI | U, M | Weekly |
| 9 | Yahoo Finance | H, M | Weekly |
| 10 | Alpha Vantage | H, M | Daily |
| 11 | FMP | H, M, N | Daily |
| 12 | Finnhub | U, M, A, N | Daily |
| 13 | FRED | H, U, M | Weekly |
| 14 | Layoffs.fyi | H | Monthly |
| 15 | SEC 8-K | H | Daily |
| 16 | WARN Act | H | Monthly |
| 17 | NewsAPI | All | Daily |
| 18 | CEO Pipeline | M | Daily |

All data sources are free and public.

## API

Base URL: `https://api.thehibalance.org`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/score/{domain}` | HI Grade by domain |
| `GET /api/v1/score/ticker/{ticker}` | HI Grade by stock ticker |
| `GET /api/v1/search?q={query}` | Search companies (aliases + domain matching) |
| `GET /api/v1/grades/top?limit=10` | Top rated companies |
| `GET /api/v1/stats` | Database statistics |
| `GET /api/v1/heartbeat/pulse` | Ecosystem pulse |
| `GET /api/v1/heartbeat/alerts` | Decay alerts |
| `GET /api/v1/heartbeat/{ticker}` | Company heartbeat |
| `GET /api/v1/human100` | HUMAN 100 Index |
| `GET /api/v1/human100/metadata` | Index metadata |
| `GET /api/v1/human100/check/{ticker}` | Check HUMAN 100 membership |
| `GET /api/v1/arbitrage` | HUMAN Lens (HI vs ESG) |
| `GET /api/v1/arbitrage/washers` | ESG washing detection |
| `GET /api/v1/arbitrage/gems` | Hidden gems |
| `GET /api/v1/moat` | HUMAN Shield scores |
| `GET /api/v1/moat/fortresses` | Fortress-level companies |
| `GET /api/v1/moat/vulnerable` | Most vulnerable to AI |
| `GET /api/v1/contagion` | HUMAN Contagion scores |
| `GET /api/v1/empathy` | HUMAN Watermark scores |
| `GET /api/v1/empathy/performative` | Performative empathy detection |
| `GET /api/v1/consciousness` | HUMAN Consciousness benchmarks |
| `GET /api/v1/collective` | HUMAN Wave pressure signals |
| `GET /api/v1/collective/pressure` | Industry pressure rankings |

Free public access. No authentication required.

## What Makes This Different

**1. Edge-to-Cloud Native** — The browser extension runs on deterministic, human-engineered code. Zero AI. Zero black boxes. The cloud computes scores from 18 data sources. No other scoring framework ships consumer-side and enterprise-side simultaneously.

**2. Fully Open Source Methodology** — Every formula, every weight, every threshold is auditable on GitHub. A transparency framework that hides its own math would be hypocritical.

**3. AI Toggle + Equalizer** — Consumers filter companies by HI Grade thresholds across all five dimensions. Strict mode hides AI-heavy companies. Soft mode flags them. No other framework gives consumers this control.

**4. AI Enhancement Layer** — AI improves the inputs, never the formula. NLP on SEC filings, ML humanwashing detection, predictive decay. Toggle OFF by default. The AI makes the telescope sharper — it doesn't move the stars.

## Status

- ✅ Provisional patent filed (March 5, 2026)
- ✅ HI Grade™ trademark filed (March 12, 2026)
- ✅ 440+ companies scored, 18 data sources
- ✅ 10 HUMAN features live (all 10 built and deployed)
- ✅ 32 API endpoints at api.thehibalance.org
- ✅ Balance floor rule (below 42 = capped at C)
- ✅ 3-tab dropdown nav (HI / HUMAN / About HI)
- ✅ Mini pill → full sidebar panel (extension)
- ✅ Dark mode toggle on extension
- ✅ Search & Compare on homepage
- ✅ For Companies section with certification tiers
- ✅ Search aliases (google→Alphabet, facebook→Meta, etc.)
- ✅ Company dedup (4-layer matching)
- ✅ Single command runner (`run_all.py --daily --push`)
- ⏳ Chrome Web Store listing
- ⏳ Native iOS app
- ⏳ AI Enhancement Layer (Phase 1: NLP on SEC filings)
- ⏳ Non-provisional patent (March 2027)

---

**HI.** — Find the HI balance.

*10 HUMAN features. One question: Is it HUMAN?*

[thehibalance.org](https://thehibalance.org) · The Deep Thought Foundation · Patent Pending · HI Grade™ Morf Innovations LLC
