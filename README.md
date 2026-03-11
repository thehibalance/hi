# HI. — Find the HI balance.

> The balance between humans and technology, measured.

**HI.** is an open scoring framework that measures how human a company is across five dimensions: **H**uman Consciousness, **U**nderstanding & Empathy, **M**oral & Ethical Conduct, **A**live & Environmental, **N**atural Transparency.

Every company gets an **HI Grade** — a simple letter grade (HI Certified, A, B, C, F) that consumers, investors, and procurement teams can use to make informed decisions.

🌐 [thehibalance.org](https://thehibalance.org) · 🏛 The Deep Thought Foundation · 📄 Patent Pending

---

## What's in this repo

```
hi/
├── human-edge/              # Chrome browser extension (Manifest V3)
│   ├── manifest.json        # Extension config
│   ├── background.js        # Service worker + cloud sync
│   ├── content.js           # Page badge injection + cloud fallback
│   ├── content.css          # Badge styles
│   ├── popup.html           # Extension popup UI
│   ├── popup.js             # Popup controller
│   └── lib/
│       ├── seed-data.js     # 206 hand-scored companies
│       ├── engine.js        # Deterministic scoring engine (NO AI)
│       └── db.js            # Database layer
│
├── pipeline/                # Phase 2 — Cloud scoring pipeline
│   ├── sec_edgar_pipeline.py    # SEC EDGAR data ingestion
│   ├── scoring_engine.py        # HUMAN dimension scoring
│   └── api_server.py            # REST API server
│
├── docs/                    # Documentation
│   └── methodology/         # HUMAN Grade Methodology Spec v1.0
│
├── LICENSE                  # AGPL-3.0 (extension) / Apache 2.0 (methodology)
└── README.md
```

## Quick Start

### Browser Extension (no server needed)

1. Clone this repo
2. Open `chrome://extensions` in Chrome
3. Enable **Developer mode**
4. Click **Load unpacked** → select the `human-edge/` folder
5. Visit any website — if the company is in our database, you'll see the HI Grade badge

### Cloud Pipeline (optional — adds live scoring)

```bash
# Install API dependencies
pip install flask flask-cors

# Pull data from SEC EDGAR (59 public companies)
cd pipeline
python sec_edgar_pipeline.py --limit 10

# Score them
python scoring_engine.py --input data/sec --output data/scores

# Start the API
python api_server.py --port 5000

# The extension auto-connects to localhost:5000
```

## The HI Grade Scale

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
| **H** — Human Consciousness | Creative agency, craft, accountability | Automation, displacement |
| **U** — Understanding & Empathy | Genuine care, emotional presence | Simulated empathy |
| **M** — Moral & Ethical Conduct | Principled action, fairness | Optimization at all costs |
| **A** — Alive & Environmental | True ecological cost incl. AI infrastructure | Hidden compute footprint |
| **N** — Natural Transparency | Honest disclosure of AI usage | Humanwashing, opacity |

## Architecture

```
Edge (NO AI)                          Cloud (AI OK)
┌─────────────────────┐    sync     ┌─────────────────────┐
│ Browser Extension    │◄──────────►│ REST API             │
│ • Seed database      │            │ • SEC EDGAR pipeline │
│ • Filter engine      │            │ • Scoring engine     │
│ • Badge display      │            │ • Score database     │
│ • Deterministic only │            │ • NLP / ML analysis  │
└─────────────────────┘            └─────────────────────┘
```

The edge node is **entirely AI-free**. This is a philosophical commitment: you cannot credibly score companies on AI displacement while running AI on the consumer's device.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/score/{domain}` | HI Grade by domain |
| `GET /api/v1/score/ticker/{ticker}` | HI Grade by stock ticker |
| `GET /api/v1/search?q={query}` | Search companies |
| `GET /api/v1/grades` | List all companies |
| `GET /api/v1/grades/top` | Leaderboard |
| `GET /api/v1/stats` | Database statistics |

## Contributing

We welcome contributions! The methodology spec is open (Apache 2.0) and anyone can audit, improve, or implement it.

- **Score a company**: Follow the methodology spec to score a company and submit a PR
- **Add a data source**: Write a pipeline that outputs JSON in the signal format
- **Improve the extension**: Bug fixes, UI improvements, new features
- **Report issues**: Found a score that seems wrong? Open an issue

## License

- **Methodology Specification**: Apache 2.0
- **Browser Extension & Pipeline**: AGPL-3.0
- **Seed Database**: CC BY-SA 4.0

## Status

- ✅ Provisional patent filed (March 5, 2026)
- ✅ 206 companies scored
- ✅ Chrome extension working
- ✅ SEC EDGAR pipeline built
- ✅ Scoring engine built
- ✅ REST API built
- ✅ Extension ↔ API sync protocol
- ⏳ Additional data sources (EPA, BLS, CDP, Glassdoor)
- ⏳ Chrome Web Store listing
- ⏳ HI Certification portal

---

**HI. Find the HI balance.**

The Deep Thought Foundation · [thehibalance.org](https://thehibalance.org) · Project Anakin
