"""
HI. API Key Management
Manages API keys, tiers, and rate limits.

Tiers:
  - free:       100 calls/day, no key required
  - pro:        10,000 calls/day, $49/mo
  - enterprise: unlimited, $499/mo

Keys stored in data/api_keys.json
"""

import json, hashlib, secrets, os
from pathlib import Path
from datetime import datetime

KEYS_FILE = Path("data/api_keys.json")

TIERS = {
    "free": {
        "name": "Free",
        "calls_per_day": 100,
        "calls_per_minute": 10,
        "features": ["scores", "search", "stats"],
        "price": 0,
    },
    "pro": {
        "name": "Pro",
        "calls_per_day": 10000,
        "calls_per_minute": 100,
        "features": ["scores", "search", "stats", "bulk", "webhooks", "human100", "heartbeat", "features"],
        "price": 4900,  # cents
        "stripe_price_id": "",  # Set after creating Stripe product
    },
    "enterprise": {
        "name": "Enterprise",
        "calls_per_day": 999999,
        "calls_per_minute": 1000,
        "features": ["scores", "search", "stats", "bulk", "webhooks", "human100", "heartbeat", "features", "raw", "export", "whitelabel"],
        "price": 49900,  # cents
        "stripe_price_id": "",  # Set after creating Stripe product
    },
}


def load_keys():
    """Load all API keys."""
    if KEYS_FILE.exists():
        return json.load(open(KEYS_FILE))
    return {}


def save_keys(keys):
    """Save all API keys."""
    KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(keys, open(KEYS_FILE, "w"), indent=2)


def generate_key():
    """Generate a new API key."""
    return f"hi_{secrets.token_hex(24)}"


def hash_key(key):
    """Hash a key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def create_key(email, tier="pro", stripe_customer_id=None, stripe_subscription_id=None):
    """Create a new API key for a customer."""
    keys = load_keys()
    raw_key = generate_key()
    hashed = hash_key(raw_key)
    
    keys[hashed] = {
        "email": email,
        "tier": tier,
        "created": datetime.utcnow().isoformat() + "Z",
        "active": True,
        "stripe_customer_id": stripe_customer_id,
        "stripe_subscription_id": stripe_subscription_id,
        "calls_today": 0,
        "calls_total": 0,
        "last_reset": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    
    save_keys(keys)
    return raw_key


def validate_key(raw_key):
    """Validate an API key. Returns tier info or None."""
    if not raw_key:
        return TIERS["free"]
    
    # Strip "Bearer " prefix if present
    if raw_key.startswith("Bearer "):
        raw_key = raw_key[7:]
    
    hashed = hash_key(raw_key)
    keys = load_keys()
    
    if hashed not in keys:
        return None  # Invalid key
    
    entry = keys[hashed]
    if not entry.get("active"):
        return None  # Deactivated
    
    tier = entry.get("tier", "pro")
    
    # Reset daily counter
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if entry.get("last_reset") != today:
        entry["calls_today"] = 0
        entry["last_reset"] = today
    
    # Check daily limit
    tier_info = TIERS.get(tier, TIERS["pro"])
    if entry["calls_today"] >= tier_info["calls_per_day"]:
        return {"error": "daily_limit", "tier": tier, "limit": tier_info["calls_per_day"]}
    
    # Increment counter
    entry["calls_today"] += 1
    entry["calls_total"] += 1
    save_keys(keys)
    
    return {**tier_info, "tier_id": tier, "email": entry["email"]}


def deactivate_key(email=None, stripe_subscription_id=None):
    """Deactivate a key by email or subscription ID."""
    keys = load_keys()
    for hashed, entry in keys.items():
        if (email and entry.get("email") == email) or \
           (stripe_subscription_id and entry.get("stripe_subscription_id") == stripe_subscription_id):
            entry["active"] = False
    save_keys(keys)


def get_usage(raw_key):
    """Get usage stats for a key."""
    hashed = hash_key(raw_key.replace("Bearer ", ""))
    keys = load_keys()
    entry = keys.get(hashed)
    if not entry:
        return None
    tier = TIERS.get(entry.get("tier", "pro"), TIERS["pro"])
    return {
        "tier": entry.get("tier"),
        "calls_today": entry.get("calls_today", 0),
        "calls_total": entry.get("calls_total", 0),
        "daily_limit": tier["calls_per_day"],
        "remaining": max(0, tier["calls_per_day"] - entry.get("calls_today", 0)),
        "active": entry.get("active", True),
    }
