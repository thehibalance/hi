# HI. — Find the HI balance.

> Find the HI balance.

**HI.** is an open scoring framework that measures how human a company is across five dimensions: **H**uman Consciousness, **U**nderstanding & Empathy, **M**oral & Ethical Conduct, **A**live & Environmental, **N**atural Transparency.

Every company gets an **HI Grade™** — a simple letter grade (HI Certified, A, B, C, F) that consumers, investors, and procurement teams can use to make informed decisions. The balance between humans and technology, measured.

🌐 [thehibalance.org](https://thehibalance.org) · 🏛 The Deep Thought Foundation · 📄 Patent Pending · ™ HI Grade — Morf Innovations LLC

---

## Live Now

- **Website**: [thehibalance.org](https://thehibalance.org) — Search 330+ companies, HUMAN 100 Index, Heartbeat monitor, Genome profiles
- **API**: [hi-api-production.up.railway.app](https://hi-api-production.up.railway.app/api/v1/stats) — Free public REST API (15+ endpoints)
- **Extension**: Chrome + Safari browser extensions with live scores, heartbeat, genome
- **HUMAN 100**: The top 100 most human public companies — ETF-licensable index
- **Heartbeat**: Real-time score decay detection powered by 6 data feeds

---

## Patent Features (4 Live)

| # | Feature | Status | Description |
|---|---------|--------|-------------|
| 1 | **HUMAN Heartbeat** | ✅ Live | Real-time score decay detection from 6 feeds |
| 2 | **Consciousness Decay Index** | ✅ Live | Per-company decay score 0-100 |
| 3 | **HUMAN Genome** | ✅ Live | Sub-signal fingerprint of every company |
| 4 | **HUMAN 100 Index** | ✅ Live | ETF-licensable top 100 ranking |
| 5 | Empathy Authenticity Watermark | ⏳ | Real vs performative empathy detection |
| 6 | Contagion Effect Score | ⏳ | Supply chain ethics ripple |
| 7 | Ethical Moat Indicator | ⏳ | AI displacement resistance |
| 8 | Consumer Consciousness Score | ⏳ | Personal ethical footprint |
| 9 | Grade Arbitrage Detection | ⏳ | HI vs ESG gap detection |
| 10 | Collective Bargaining Signal | ⏳ | Labor power vs corporate power ratio |

---

## What's in this repo

```
hi/
├── human-edge/                  # Chrome browser extension (Manifest V3)
│   ├── manifest.json            # Extension config
│   ├── background.js            # Service worker + cloud sync + heartbeat pulse
│   ├── content.js               # Badge + genome strip + heartbeat + drill-down
│   ├── content.css              # Badge + panel styles
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
│   ├── heartbeat_monitor.py     # Heartbeat: 6-feed decay detection
│   ├── human100_index.py        # HUMAN 100 Index generator
│   ├── api_server.py            # REST API server (Flask, 15+ endpoints)
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
5. Visit any website — if the company is in our database, the HI Grade™ badge appears

The extension includes 206 hand-scored companies offline. With the API connected, it scores 330+ companies with live heartbeat and genome data.

### Daily Pipeline (one command)

```bash
cd pipeline
python3 run_all.py --daily --push    # Run daily pipelines + auto-push
python3 run_all.py --weekly --push   # Weekly pipelines + push
python3 run_all.py --monthly --push  # Full run + push
```

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

## HUMAN Heartbeat (Patent Pending)

Real-time score decay detection powered by 6 feeds: Finnhub, NewsAPI, Layoffs.fyi, SEC 8-K, CEO Pipeline, WARN Act.

Decay levels: Stable (0-9), Watch (10-29), Warning (30-49), Critical (50+).

## HUMAN 100 Index (Patent Pending)

The top 100 most human public companies, ranked by HI Grade™ composite score. Eligibility: publicly traded, 2+ verified data sources, no humanwashing flags. Rebalanced monthly. Designed for ETF licensing.

## API

Base URL: `https://hi-api-production.up.railway.app`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/score/{domain}` | HI Grade by domain |
| `GET /api/v1/score/ticker/{ticker}` | HI Grade by stock ticker |
| `GET /api/v1/search?q={query}` | Search companies |
| `GET /api/v1/grades/top?limit=10` | Top rated companies |
| `GET /api/v1/stats` | Database statistics |
| `GET /api/v1/heartbeat/pulse` | Ecosystem pulse |
| `GET /api/v1/heartbeat/alerts` | Decay alerts |
| `GET /api/v1/heartbeat/{ticker}` | Company heartbeat |
| `GET /api/v1/human100` | HUMAN 100 Index |
| `GET /api/v1/human100/metadata` | Index metadata |
| `GET /api/v1/human100/check/{ticker}` | Check HUMAN 100 membership |

Free public access. No authentication required.

## Status

- ✅ Provisional patent filed (March 5, 2026)
- ✅ HI Grade™ trademark filed (March 12, 2026)
- ✅ 330+ companies scored, 18 data sources
- ✅ 4 patent features live (Heartbeat, Decay, Genome, HUMAN 100)
- ✅ Balance floor rule (below 42 = capped at C)
- ✅ Dimension drill-down with real data insights
- ✅ Chrome extension with heartbeat, genome, auto-collapse
- ✅ REST API live on Railway (15+ endpoints)
- ✅ Website live at thehibalance.org
- ✅ Single command runner (`run_all.py --daily --push`)
- ⏳ Chrome Web Store listing
- ⏳ Native iOS app
- ⏳ 6 more patent features in development

---

**HI. — Find the HI balance.**

[thehibalance.org](https://thehibalance.org) · The Deep Thought Foundation · Patent Pending · HI Grade™ Morf Innovations LLC
