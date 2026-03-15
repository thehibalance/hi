# HI. — Find the HI balance.

**HI.** is an open scoring framework that measures how human a company is across five dimensions: **H**uman Consciousness, **U**nderstanding & Empathy, **M**oral & Ethical Conduct, **A**live & Environmental, **N**atural Transparency.

Every company gets an **HI Grade™** — a simple letter grade (HI Certified, A, B, C, F) that consumers, investors, and procurement teams can use to make informed decisions. The balance between humans and technology, measured.

🌐 [thehibalance.org](https://thehibalance.org) · 🏛 The Deep Thought Foundation · 📄 Patent Pending · ™ HI Grade — Morf Innovations LLC

---

## Live Now

- **Website**: [thehibalance.org](https://thehibalance.org) — Search 710+ companies, The HI Life rankings, company detail pages
- **API**: [hi-api-production.up.railway.app](https://hi-api-production.up.railway.app/api/v1/stats) — Free public REST API
- **Extension**: Chrome + Safari browser extensions (developer install below)
- **Database**: 710 companies, 592 domains, 328 public company tickers, 17 data sources

---

## What's in this repo

```
hi/
├── human-edge/                  # Chrome browser extension (Manifest V3)
│   ├── manifest.json            # Extension config
│   ├── background.js            # Service worker + cloud sync
│   ├── content.js               # Page badge + side panel + equalizer
│   ├── content.css              # Badge + panel styles
│   ├── popup.html               # Extension popup UI
│   ├── popup.js                 # Popup controller + cloud sync
│   └── lib/
│       ├── seed-data.js         # 206 hand-scored companies
│       ├── engine.js            # Deterministic scoring engine (NO AI)
│       └── db.js                # Database layer
│
├── pipeline/                    # Cloud scoring pipeline (17 data sources)
│   ├── sec_edgar_pipeline.py    # SEC EDGAR — headcount, revenue, R&D, filings
│   ├── epa_echo_pipeline.py     # EPA ECHO — environmental violations
│   ├── bls_pipeline.py          # BLS — industry wage & employment benchmarks
│   ├── cdp_pipeline.py          # CDP — climate disclosure scores
│   ├── job_board_pipeline.py    # Job Boards — AI hiring velocity
│   ├── glassdoor_pipeline.py    # Glassdoor — employee ratings, CEO approval
│   ├── dei_pipeline.py          # AAPD/DEI — Disability Equality Index
│   ├── hrc_pipeline.py          # HRC/CEI — Corporate Equality Index
│   ├── yahoo_pipeline.py        # Yahoo Finance — headcount, revenue, market cap
│   ├── alpha_vantage_pipeline.py# Alpha Vantage — R&D spend, earnings, margins
│   ├── fmp_pipeline.py          # FMP — full financials, ratios
│   ├── finnhub_pipeline.py      # Finnhub — ESG scores + company news
│   ├── fred_pipeline.py         # FRED — economic benchmarks (18 series)
│   ├── opencorporates_pipeline.py # OpenCorporates — corporate transparency
│   ├── layoffs_pipeline.py      # Layoffs.fyi — tech layoff history
│   ├── sec_8k_pipeline.py       # SEC 8-K — material event filings
│   ├── warn_pipeline.py         # WARN Act — legally required layoff notices
│   ├── heartbeat_monitor.py     # HUMAN Heartbeat — score decay detection (patent)
│   ├── scoring_engine.py        # Multi-source HUMAN dimension scoring (v2)
│   ├── api_server.py            # REST API server (Flask)
│   ├── sp500_companies.py       # S&P 500 company list
│   └── sp500_domains.py         # Domain mappings
│
├── docs/                        # Website (GitHub Pages)
│   ├── index.html               # thehibalance.org
│   └── CNAME                    # Custom domain config
│
├── LICENSE                      # AGPL-3.0 (extension) / Apache 2.0 (methodology)
├── CONTRIBUTING.md
└── README.md
```

## Quick Start

### Browser Extension (no server needed)

1. Clone: `git clone https://github.com/thehibalance/hi.git`
2. Open `chrome://extensions`, enable **Developer mode**
3. Click **Load unpacked** → select `human-edge/`
4. Visit any website — if the company is in our database, the HI Grade™ badge appears

### Cloud Pipeline (17 data sources)

```bash
cd pipeline
pip install flask flask-cors yfinance requests --break-system-packages

# Free sources (no keys needed)
python3 cdp_pipeline.py
python3 job_board_pipeline.py
python3 glassdoor_pipeline.py
python3 dei_pipeline.py
python3 hrc_pipeline.py
python3 yahoo_pipeline.py
python3 sec_edgar_pipeline.py --limit 10
python3 sec_8k_pipeline.py --limit 20
python3 opencorporates_pipeline.py --limit 20

# Free API key sources
python3 fmp_pipeline.py --limit 20          # financialmodelingprep.com
python3 finnhub_pipeline.py --limit 20      # finnhub.io
python3 fred_pipeline.py                    # fred.stlouisfed.org
python3 alpha_vantage_pipeline.py           # alphavantage.co

# Manual data (download CSVs first)
python3 layoffs_pipeline.py                 # layoffs.fyi CSV
python3 warn_pipeline.py                    # WARN Act CSVs

# Score + Heartbeat
python3 scoring_engine.py
python3 heartbeat_monitor.py

# Start API
python3 api_server.py --port 8080
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

## The HUMAN Framework

| Dimension | Measures | What AI Replaces |
|-----------|----------|-----------------|
| 🧠 **H** — Human Consciousness | Creative agency, craft, accountability | Automation, displacement |
| 💙 **U** — Understanding & Empathy | Genuine care, emotional presence | Simulated empathy |
| ⚖️ **M** — Moral & Ethical Conduct | Principled action, fairness | Optimization at all costs |
| 🌍 **A** — Alive & Environmental | True ecological cost incl. AI infrastructure | Hidden compute footprint |
| 🔍 **N** — Natural Transparency | Honest disclosure of AI usage | Humanwashing, opacity |

## Data Sources (17)

| # | Source | Dimensions | Key Data | Cost |
|---|--------|-----------|----------|------|
| 1 | SEC EDGAR | H, M, N | Filings, headcount, R&D | Free |
| 2 | EPA ECHO | A, M | Environmental violations | Free |
| 3 | BLS | H, U | Wage benchmarks | Free |
| 4 | CDP | A, N | Climate disclosure | Free |
| 5 | Job Boards | H | AI hiring velocity | Free |
| 6 | Glassdoor | U, M | Employee ratings | Free |
| 7 | AAPD/DEI | U, M | Disability Equality Index | Free |
| 8 | HRC/CEI | U, M | Corporate Equality Index | Free |
| 9 | Yahoo Finance | H, M | Headcount, revenue, market cap | Free |
| 10 | Alpha Vantage | H, M | R&D spend, earnings, margins | Free key |
| 11 | FMP | H, M, N | Full financials, ratios | Free key |
| 12 | Finnhub | U, M, A, N | ESG scores + company news | Free key |
| 13 | FRED | H, U, M | Economic benchmarks (18 series) | Free key |
| 14 | OpenCorporates | N, M | Corporate transparency | Free |
| 15 | Layoffs.fyi | H | Tech layoff history | Free CSV |
| 16 | SEC 8-K | H | Material event filings | Free |
| 17 | WARN Act | H | Legally required layoff notices | Free |

## HUMAN Heartbeat (Patent Feature)

Real-time event monitor that detects score decay before it happens. Aggregates signals from Finnhub news, Layoffs.fyi, SEC 8-K filings, and WARN Act data.

| Output | What It Does |
|--------|-------------|
| **Decay Index** (0-100) | Predicts whether a company's HI Grade is about to drop |
| **Alerts** | Flags companies at warning (30+) or critical (50+) decay |
| **Ecosystem Pulse** | Overall market health: healthy / elevated / stressed / critical |

Catches layoff surges, AI acceleration pivots, ethics/legal events, environmental incidents, and humanwashing patterns across multiple signals.

## Architecture

```
Edge (NO AI)                          Cloud (NO AI currently)
┌──────────────────────┐    sync     ┌──────────────────────────┐
│ Browser Extension     │◄──────────►│ REST API (Flask)          │
│ • 206 seed companies  │            │ • 17 data pipelines       │
│ • Filter engine       │            │ • HUMAN Heartbeat monitor │
│ • Equalizer UI        │            │ • Scoring engine v2       │
│ • Side panel + search │            │ • 710+ companies          │
│ • Deterministic only  │            │ • 592 domains indexed     │
└──────────────────────┘            └──────────────────────────┘
         │                                    │
         └──── Both serve ────────────────────┘
                    │
            ┌──────────────┐
            │ thehibalance │
            │    .org      │
            └──────────────┘
                    │
        ┌───────────────────────┐
        │  AI-Informed Models   │
        │  [Toggle: OFF by      │
        │   default]            │
        │                       │
        │ • NLP filing analysis │
        │ • ML humanwashing     │
        │   detection           │
        │ • Sentiment analysis  │
        │ • Predictive scoring  │
        │                       │
        │ User opts IN — never  │
        │ forced. Scores always │
        │ available without AI. │
        └───────────────────────┘
```

Zero AI today. Scoring is transparent math: averages, thresholds, and if/else logic. Anyone can audit every formula. AI-Informed Models are planned as an opt-in layer — toggled OFF by default.

## API

Base URL: `https://hi-api-production.up.railway.app`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/score/{domain}` | HI Grade by domain |
| `GET /api/v1/score/ticker/{ticker}` | HI Grade by stock ticker |
| `GET /api/v1/search?q={query}&limit=10` | Search companies |
| `GET /api/v1/grades/top?limit=10` | Top rated companies |
| `GET /api/v1/grades/bottom?limit=10` | Bottom rated companies |
| `GET /api/v1/stats` | Database statistics |

Free public access. No authentication required.

## Humanwashing Detection

| Flag | Trigger |
|------|---------|
| HW.1 | Revenue per employee >$2M (high automation) |
| HW.2 | R&D growth significantly outpacing headcount |
| HW.3 | AI roles dominate job postings (>35%) |
| HW.4 | Significant environmental violations |
| HW.5 | Refuses CDP climate disclosure |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

- **Methodology Specification**: Apache 2.0
- **Browser Extension & Pipeline**: AGPL-3.0
- **Seed Database**: CC BY-SA 4.0

## Status

- ✅ Provisional patent filed (March 5, 2026)
- ✅ HI Grade™ trademark filed (March 12, 2026)
- ✅ 710 companies scored across 592 domains
- ✅ 17 data pipelines live
- ✅ HUMAN Heartbeat — score decay detection (patent feature)
- ✅ Chrome + Safari extensions
- ✅ REST API on Railway
- ✅ Website at thehibalance.org
- ⏳ Chrome Web Store listing
- ⏳ Native iOS app
- ⏳ HI Certification portal
- ⏳ AI-Informed Models (opt-in)

---

[thehibalance.org](https://thehibalance.org) · The Deep Thought Foundation · Patent Pending · HI Grade™ Morf Innovations LLC
