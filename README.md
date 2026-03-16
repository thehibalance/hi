# HI. — Find the HI balance.

**HI.** is an open scoring framework that measures how human a company is across five dimensions: **H**uman Consciousness, **U**nderstanding & Empathy, **M**oral & Ethical Conduct, **A**live & Environmental, **N**atural Transparency.

Every company gets an **HI Grade™** — a simple letter grade (HI Certified, A, B, C, F) that consumers, investors, and procurement teams can use to make informed decisions. The balance between humans and technology, measured.

🌐 [thehibalance.org](https://thehibalance.org) · 🏛 The Deep Thought Foundation · 📄 Patent Pending · ™ HI Grade — Morf Innovations LLC

---

## Live Now

- **Website**: [thehibalance.org](https://thehibalance.org) — 710+ companies, The HI Life rankings
- **API**: [hi-api-production.up.railway.app](https://hi-api-production.up.railway.app/api/v1/stats) — Free public REST API
- **Extension**: Chrome + Safari browser extensions
- **Database**: 710 companies, 592 domains, 328 tickers, 18 data sources

---

## Quick Start

### One Command

```bash
cd pipeline
python3 run_all.py --daily --push    # Run all daily pipelines + auto-push to git/Railway
```

### Run Modes

| Command | What Runs | Time |
|---------|-----------|------|
| `python3 run_all.py --daily` | News, financials, SEC, CEO, score, Heartbeat | ~15 min |
| `python3 run_all.py --weekly` | All daily + Yahoo, FRED, DEI, HRC | ~30 min |
| `python3 run_all.py --monthly` | Everything including SEC EDGAR, CDP, Glassdoor | ~2 hrs |
| `python3 run_all.py --daily --push` | Daily + auto-push to GitHub & Railway | ~16 min |

### First Time Setup

```bash
git clone https://github.com/thehibalance/hi.git
cd hi/pipeline
pip install flask flask-cors yfinance requests --break-system-packages

# API keys (all free)
echo YOUR_KEY > data/fmp_key.txt          # financialmodelingprep.com
echo YOUR_KEY > data/finnhub_key.txt      # finnhub.io
echo YOUR_KEY > data/fred_key.txt         # fred.stlouisfed.org
echo YOUR_KEY > data/alpha_vantage_key.txt # alphavantage.co
echo YOUR_KEY > data/newsapi_key.txt      # newsapi.org

# Run everything
python3 run_all.py --daily --push
```

### Browser Extension

1. Open `chrome://extensions`, enable **Developer mode**
2. Click **Load unpacked** → select `human-edge/`
3. Visit any website — HI Grade™ badge appears for scored companies

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

## The HUMAN Framework

| Dimension | Measures |
|-----------|----------|
| 🧠 **H** — Human Consciousness | Creative agency, craft, accountability |
| 💙 **U** — Understanding & Empathy | Genuine care, emotional presence |
| ⚖️ **M** — Moral & Ethical Conduct | Principled action, fairness, CEO accountability |
| 🌍 **A** — Alive & Environmental | True ecological cost incl. AI infrastructure |
| 🔍 **N** — Natural Transparency | Honest disclosure of AI usage |

## Data Sources (18)

| # | Source | Dimensions | Data | Schedule |
|---|--------|-----------|------|----------|
| 1 | SEC EDGAR | H, M, N | Filings, headcount, R&D | Monthly |
| 2 | EPA ECHO | A, M | Environmental violations | Monthly |
| 3 | BLS | H, U | Wage benchmarks | Monthly |
| 4 | CDP | A, N | Climate disclosure | Monthly |
| 5 | Job Boards | H | AI hiring velocity | Monthly |
| 6 | Glassdoor | U, M | Employee ratings | Monthly |
| 7 | AAPD/DEI | U, M | Disability Equality Index | Weekly |
| 8 | HRC/CEI | U, M | Corporate Equality Index | Weekly |
| 9 | Yahoo Finance | H, M | Headcount, revenue, market cap | Weekly |
| 10 | Alpha Vantage | H, M | R&D spend, earnings, margins | Daily |
| 11 | FMP | H, M, N | Full financials, ratios | Daily |
| 12 | Finnhub | U, M, A, N | ESG scores + company news | Daily |
| 13 | FRED | H, U, M | Economic benchmarks (18 series) | Weekly |
| 14 | Layoffs.fyi | H | Tech layoff history | Monthly |
| 15 | SEC 8-K | H | Material event filings | Daily |
| 16 | WARN Act | H | Legally required layoff notices | Monthly |
| 17 | NewsAPI | All | 150K+ media sources, 30-day coverage | Daily |
| 18 | CEO Pipeline | M | Pay ratio, approval, tenure vs layoffs | Daily |

Plus: **HUMAN Heartbeat** (patent feature) aggregates all signals for real-time score decay detection.

## HUMAN Heartbeat (Patent Feature)

Real-time event monitor that detects score decay before it happens.

| Output | What It Does |
|--------|-------------|
| **Decay Index** (0-100) | Predicts whether a company's HI Grade is about to drop |
| **Alerts** | Flags companies at warning (30+) or critical (50+) decay |
| **Ecosystem Pulse** | Overall market health: healthy / elevated / stressed / critical |

Catches layoff surges, AI acceleration pivots, CEO controversies, ethics/legal events, environmental incidents, and humanwashing patterns.

## Architecture

```
Edge (NO AI)                          Cloud (NO AI)
┌──────────────────────┐    sync     ┌──────────────────────────┐
│ Browser Extension     │◄──────────►│ REST API (Flask)          │
│ • 206 seed companies  │            │ • 18 data pipelines       │
│ • Filter engine       │            │ • CEO accountability      │
│ • Equalizer UI        │            │ • HUMAN Heartbeat monitor │
│ • Side panel + search │            │ • NewsAPI media monitoring│
│ • Deterministic only  │            │ • 710+ companies          │
└──────────────────────┘            └──────────────────────────┘
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

Scoring is transparent math. Anyone can audit every formula. AI-Informed Models are a planned opt-in layer — toggled OFF by default. The user chooses whether AI helps.

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

## Repo Structure

```
hi/
├── human-edge/                    # Chrome + Safari extension (Manifest V3)
├── pipeline/
│   ├── run_all.py                 # Single command master runner
│   ├── scoring_engine.py          # Multi-source scoring (v2)
│   ├── heartbeat_monitor.py       # HUMAN Heartbeat (patent feature)
│   ├── ceo_pipeline.py            # CEO accountability (M dimension)
│   ├── newsapi_pipeline.py        # Broad media monitoring
│   ├── finnhub_pipeline.py        # ESG + company news
│   ├── fmp_pipeline.py            # Full financials
│   ├── yahoo_pipeline.py          # Headcount, revenue
│   ├── alpha_vantage_pipeline.py  # R&D, earnings
│   ├── fred_pipeline.py           # Economic benchmarks
│   ├── sec_edgar_pipeline.py      # SEC filings
│   ├── sec_8k_pipeline.py         # Material events
│   ├── epa_echo_pipeline.py       # Environmental data
│   ├── bls_pipeline.py            # Labor benchmarks
│   ├── cdp_pipeline.py            # Climate disclosure
│   ├── job_board_pipeline.py      # AI hiring ratio
│   ├── glassdoor_pipeline.py      # Employee ratings
│   ├── dei_pipeline.py            # Disability inclusion
│   ├── hrc_pipeline.py            # LGBTQ+ inclusion
│   ├── layoffs_pipeline.py        # Tech layoff tracker
│   ├── warn_pipeline.py           # WARN Act notices
│   └── api_server.py              # REST API (Flask)
├── docs/                          # Website (GitHub Pages)
└── README.md
```

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
- ✅ 18 data pipelines + CEO accountability
- ✅ HUMAN Heartbeat — real-time score decay detection (patent feature)
- ✅ NewsAPI broad media monitoring — 150K+ sources
- ✅ Chrome + Safari extensions
- ✅ REST API on Railway
- ✅ Website at thehibalance.org
- ⏳ Company deduplication cleanup
- ⏳ Chrome Web Store listing
- ⏳ Native iOS app
- ⏳ HI Certification portal
- ⏳ AI-Informed Models (opt-in)

---

[thehibalance.org](https://thehibalance.org) · The Deep Thought Foundation · Patent Pending · HI Grade™ Morf Innovations LLC
