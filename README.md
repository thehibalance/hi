# HI. — Human Intelligence. The other AI.

> Find the HI balance.

**HI.** is an open scoring framework that measures how human a company is across five dimensions: **H**uman Consciousness, **U**nderstanding & Empathy, **M**oral & Ethical Conduct, **A**live & Environmental, **N**atural Transparency.

Every company gets an **HI Grade™** — a simple letter grade (HI Certified, A, B, C, F) that consumers, investors, and procurement teams can use to make informed decisions. The balance between humans and technology, measured.

🌐 [thehibalance.org](https://thehibalance.org) · 🏛 The Deep Thought Foundation · 📄 Patent Pending · ™ HI Grade — Morf Innovations LLC

---

## Live Now

- **Website**: [thehibalance.org](https://thehibalance.org) — Search 500+ companies, full leaderboard, company detail pages
- **API**: [hi-api-production.up.railway.app](https://hi-api-production.up.railway.app/api/v1/stats) — Free public REST API
- **Extension**: Chrome browser extension (developer install below)
- **Database**: 516 companies, 585 domains, 307 public company tickers

---

## What's in this repo

```
hi/
├── human-edge/                  # Chrome browser extension (Manifest V3)
│   ├── manifest.json            # Extension config
│   ├── background.js            # Service worker + cloud sync + connection check
│   ├── content.js               # Page badge + side panel + equalizer
│   ├── content.css              # Badge + panel styles
│   ├── popup.html               # Extension popup UI
│   ├── popup.js                 # Popup controller + cloud sync
│   └── lib/
│       ├── seed-data.js         # 206 hand-scored companies
│       ├── engine.js            # Deterministic scoring engine (NO AI)
│       └── db.js                # Database layer
│
├── pipeline/                    # Cloud scoring pipeline (6 data sources)
│   ├── sec_edgar_pipeline.py    # SEC EDGAR — headcount, revenue, R&D, filings
│   ├── epa_echo_pipeline.py     # EPA ECHO — environmental violations, penalties
│   ├── bls_pipeline.py          # BLS — industry wage & employment benchmarks
│   ├── cdp_pipeline.py          # CDP — climate disclosure scores
│   ├── job_board_pipeline.py    # Job Boards — AI hiring velocity
│   ├── glassdoor_pipeline.py    # Glassdoor — employee ratings, CEO approval
│   ├── scoring_engine.py        # Multi-source HUMAN dimension scoring (v2)
│   ├── api_server.py            # REST API server (Flask)
│   ├── sp500_companies.py       # S&P 500 company list (315 tickers)
│   ├── sp500_domains.py         # Domain mappings (441 domains for 311 companies)
│   └── run_pipeline.py          # Master runner — all pipelines in one command
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

The extension includes 206 hand-scored companies offline. With the API running, it scores 500+ companies.

### Cloud Pipeline (adds 300+ companies with real data)

```bash
cd pipeline

# Install dependencies
pip install flask flask-cors --break-system-packages

# Run all built-in data sources (instant, no internet needed)
python3 cdp_pipeline.py
python3 job_board_pipeline.py
python3 glassdoor_pipeline.py

# Run SEC EDGAR for S&P 500 (needs internet, ~45 min for all 315)
python3 sec_edgar_pipeline.py --limit 10    # Start with 10 to test
python3 sec_edgar_pipeline.py               # Full run

# Score all companies from all sources
python3 scoring_engine.py

# Start the API (Mac: use 8080, port 5000 conflicts with AirPlay)
python3 api_server.py --port 8080
```

Or use the master runner:

```bash
python3 run_pipeline.py --skip-sec --no-server    # Built-in data only
python3 run_pipeline.py --sec-limit 50             # With SEC + auto-start API
python3 run_pipeline.py                            # Everything
```

## The HI Grade™ Scale

| Grade | Score | Color | Satire |
|-------|-------|-------|--------|
| **HI Certified** | 90-100 | Gold ✦ | Humans and tech, in harmony. This is what balance looks like. |
| **A** | 80-89 | Green | AI does the math. Humans do the handshakes. Nailed it. |
| **B** | 60-79 | Blue | Humans and machines, learning to share the remote. |
| **C** | 42-59 | Orange | 42. The answer to everything. Now what's the question? |
| **F** | 0-41 | Slate Gray | Don't panic. Every journey starts somewhere. |

The pass/fail line is **42** — the answer to life, the universe, and everything.

HI Certified requires paid certification + transparency verification. Companies scoring 90+ from public data are capped at A.

## The HUMAN Framework

| Dimension | Measures | What AI Replaces |
|-----------|----------|-----------------|
| 🧠 **H** — Human Consciousness | Creative agency, craft, accountability | Automation, displacement |
| 💙 **U** — Understanding & Empathy | Genuine care, emotional presence | Simulated empathy |
| ⚖️ **M** — Moral & Ethical Conduct | Principled action, fairness | Optimization at all costs |
| 🌍 **A** — Alive & Environmental | True ecological cost incl. AI infrastructure | Hidden compute footprint |
| 🔍 **N** — Natural Transparency | Honest disclosure of AI usage | Humanwashing, opacity |

## Data Sources

| Source | Dimensions | Type | Cost |
|--------|-----------|------|------|
| SEC EDGAR | H, M, N | Live API | Free |
| EPA ECHO | A, M | Live API | Free |
| BLS | H, U | Live API | Free |
| CDP | A, N | Built-in data | Free |
| Job Boards | H | Built-in data | Free |
| Glassdoor | U, M | Built-in data | Free |

**Signal coverage**: 16 out of 24 sub-signals have real data. The rest use industry-calibrated defaults.

## Architecture

```
Edge (NO AI)                          Cloud (AI OK)
┌──────────────────────┐    sync     ┌──────────────────────┐
│ Browser Extension     │◄──────────►│ REST API (Flask)      │
│ • 206 seed companies  │            │ • 6 data pipelines    │
│ • Filter engine       │            │ • Scoring engine v2   │
│ • Equalizer UI        │            │ • 500+ companies      │
│ • Side panel + search │            │ • 585 domains indexed │
│ • Deterministic only  │            │ • Humanwashing flags  │
└──────────────────────┘            └──────────────────────┘
         │                                    │
         └──── Both serve ────────────────────┘
                    │
            ┌──────────────┐
            │ thehibalance │
            │    .org      │
            └──────────────┘
```

The edge node is **entirely AI-free**. This is a philosophical commitment: you cannot credibly score companies on AI displacement while running AI on the consumer's device.

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
| `GET /api/v1/health` | Health check |

Free public access. No authentication required. Rate limited to 60 req/min.

## Humanwashing Detection

The scoring engine flags five types of humanwashing:

| Flag | Trigger |
|------|---------|
| HW.1 | Revenue per employee >$2M (high automation) |
| HW.2 | R&D growth significantly outpacing headcount |
| HW.3 | AI roles dominate job postings (>35%) |
| HW.4 | Significant environmental violations |
| HW.5 | Refuses CDP climate disclosure |

## Contributing

We welcome contributions! The methodology spec is open (Apache 2.0) and anyone can audit, improve, or implement it.

- **Score a company**: Follow the methodology spec, submit a PR with notes
- **Add a data source**: Write a pipeline that outputs JSON in the signal format
- **Improve the extension**: Bug fixes, UI improvements, new features
- **Report issues**: Found a score that seems wrong? Open an issue
- **Add domain mappings**: Help us map more company domains in `sp500_domains.py`

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

- **Methodology Specification**: Apache 2.0
- **Browser Extension & Pipeline**: AGPL-3.0
- **Seed Database**: CC BY-SA 4.0

## Status

- ✅ Provisional patent filed (March 5, 2026)
- ✅ HI Grade™ trademark filed (March 12, 2026)
- ✅ 516 companies scored across 585 domains
- ✅ 6 data pipelines (SEC, EPA, BLS, CDP, Jobs, Glassdoor)
- ✅ Scoring engine v2 (multi-source fusion)
- ✅ Chrome extension with side panel, equalizer, search
- ✅ REST API live on Railway
- ✅ Website live at thehibalance.org
- ✅ GitHub repo public
- ✅ thehibalance.org + thehibalance.com (redirect) with HTTPS
- ⏳ Chrome Web Store listing
- ⏳ Safari extension (iOS + Mac)
- ⏳ Native iOS app
- ⏳ HI Certification portal
- ⏳ Logo design (balance beam I)

---

**HI. — Human Intelligence. The other AI.**

Find the HI balance. · [thehibalance.org](https://thehibalance.org) · The Deep Thought Foundation · Patent Pending · HI Grade™ Morf Innovations LLC
