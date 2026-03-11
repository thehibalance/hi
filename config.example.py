# ═══════════════════════════════════════════════════════════════
# HI. Pipeline Configuration
# Copy this file to config.py and update with your values.
# config.py is gitignored — your settings stay local.
# ═══════════════════════════════════════════════════════════════

# ── SEC EDGAR ─────────────────────────────────────────────────
# Required: SEC requires a valid User-Agent with your name/email.
# They will block requests without one.
# Format: "AppName/Version (website; email)"
SEC_USER_AGENT = "HI-Pipeline/1.0 (thehibalance.org; your-email@thehibalance.org)"

# Rate limit: SEC allows 10 requests/second. Stay under.
SEC_RATE_LIMIT = 0.12  # seconds between requests (~8/sec)

# ── API Server ────────────────────────────────────────────────
# Port for the local Flask API server
API_PORT = 5000
API_HOST = "0.0.0.0"

# Production API URL (update when deployed)
API_PRODUCTION_URL = "https://api.thehibalance.org"

# ── Data Directories ─────────────────────────────────────────
# Where pipeline outputs are stored
DATA_DIR_SEC = "data/sec"         # SEC EDGAR raw signals
DATA_DIR_SCORES = "data/scores"   # Scored company data

# ── Extension ─────────────────────────────────────────────────
# Seed database location (relative to repo root)
SEED_DATA_PATH = "human-edge/lib/seed-data.js"

# Cache TTL for cloud lookups (milliseconds)
CACHE_TTL_MS = 86400000  # 24 hours

# ── Scoring ──────────────────────────────────────────────────
# Floor rule parameters (from methodology spec)
FLOOR_THRESHOLD = 10   # Any dimension below this triggers the cap
FLOOR_CAP = 40         # Composite capped at this when triggered

# HI Grade boundaries
GRADE_HI_CERTIFIED = 90  # Requires paid verification
GRADE_A = 80
GRADE_B = 60
GRADE_C = 42             # The answer to everything
GRADE_F = 0

# ── Future Data Sources (Phase 2+) ──────────────────────────
# EPA_API_URL = "https://echo.epa.gov/tools/data-downloads"
# BLS_API_KEY = ""       # Free: https://www.bls.gov/developers/
# CDP_DATA_DIR = "data/cdp"
# GLASSDOOR_API_KEY = "" # If available
