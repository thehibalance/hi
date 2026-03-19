"""
HI. Stripe Integration
Handles subscription webhooks and checkout sessions.

Setup:
  1. Create Stripe account at stripe.com
  2. Create two products: "HI. Pro" ($49/mo) and "HI. Enterprise" ($499/mo)
  3. Copy price IDs into STRIPE_PRICES below
  4. Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in environment
  5. Add webhook endpoint in Stripe dashboard: https://api.thehibalance.org/stripe/webhook

Usage:
  This module is imported by api_server.py — no separate process needed.
"""

import os, json
from datetime import datetime

# Stripe config — set these in Railway environment variables
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Stripe price IDs — set these after creating products in Stripe dashboard
STRIPE_PRICES = {
    "pro": os.environ.get("STRIPE_PRICE_PRO", ""),
    "enterprise": os.environ.get("STRIPE_PRICE_ENTERPRISE", ""),
}

HAS_STRIPE = False
stripe = None

try:
    import stripe as _stripe
    stripe = _stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
        HAS_STRIPE = True
except ImportError:
    pass


def create_checkout_session(tier, email=None, success_url=None, cancel_url=None):
    """Create a Stripe checkout session for a tier."""
    if not HAS_STRIPE:
        return {"error": "Stripe not configured. Set STRIPE_SECRET_KEY environment variable."}
    
    price_id = STRIPE_PRICES.get(tier)
    if not price_id:
        return {"error": f"No price configured for tier: {tier}. Set STRIPE_PRICE_{tier.upper()} environment variable."}
    
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=email,
            success_url=success_url or "https://thehibalance.org/api#success",
            cancel_url=cancel_url or "https://thehibalance.org/api#pricing",
            metadata={"tier": tier},
        )
        return {"url": session.url, "session_id": session.id}
    except Exception as e:
        return {"error": str(e)}


def handle_webhook(payload, sig_header):
    """Handle Stripe webhook events."""
    if not HAS_STRIPE or not STRIPE_WEBHOOK_SECRET:
        return {"error": "Stripe webhooks not configured"}
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return {"error": f"Webhook signature verification failed: {str(e)}"}
    
    from api_keys import create_key, deactivate_key
    
    event_type = event["type"]
    data = event["data"]["object"]
    
    if event_type == "checkout.session.completed":
        # New subscription — generate API key
        email = data.get("customer_email", data.get("customer_details", {}).get("email", ""))
        tier = data.get("metadata", {}).get("tier", "pro")
        customer_id = data.get("customer", "")
        subscription_id = data.get("subscription", "")
        
        raw_key = create_key(
            email=email,
            tier=tier,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
        )
        
        # TODO: Send email with API key via your email service
        # For now, log it
        print(f"  ✓ New {tier} subscription: {email} → key generated")
        
        # Save to a pending keys file so you can email manually
        pending_file = "data/pending_keys.json"
        pending = json.load(open(pending_file)) if os.path.exists(pending_file) else []
        pending.append({
            "email": email,
            "tier": tier,
            "key_prefix": raw_key[:12] + "...",
            "full_key": raw_key,
            "created": datetime.utcnow().isoformat() + "Z",
        })
        json.dump(pending, open(pending_file, "w"), indent=2)
        
        return {"status": "key_created", "email": email, "tier": tier}
    
    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled — deactivate key
        subscription_id = data.get("id", "")
        deactivate_key(stripe_subscription_id=subscription_id)
        print(f"  ✗ Subscription cancelled: {subscription_id}")
        return {"status": "key_deactivated"}
    
    elif event_type == "customer.subscription.updated":
        # Subscription changed — could be upgrade/downgrade
        # For now just log
        print(f"  ↻ Subscription updated: {data.get('id', '')}")
        return {"status": "noted"}
    
    elif event_type == "invoice.payment_failed":
        # Payment failed — warn but don't deactivate yet
        print(f"  ⚠ Payment failed: {data.get('customer_email', '')}")
        return {"status": "payment_failed"}
    
    return {"status": "unhandled", "type": event_type}


def register_stripe_routes(app):
    """Register Stripe endpoints on the Flask app."""
    from flask import request, jsonify
    
    @app.route("/stripe/checkout", methods=["POST"])
    def stripe_checkout():
        """Create a checkout session."""
        data = request.get_json() or {}
        tier = data.get("tier", "pro")
        email = data.get("email")
        
        if tier not in ["pro", "enterprise"]:
            return jsonify({"error": "Invalid tier. Use 'pro' or 'enterprise'."}), 400
        
        result = create_checkout_session(tier, email)
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    
    @app.route("/stripe/webhook", methods=["POST"])
    def stripe_webhook():
        """Handle Stripe webhook events."""
        payload = request.get_data()
        sig = request.headers.get("Stripe-Signature", "")
        result = handle_webhook(payload, sig)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    
    @app.route("/api/v1/key/usage")
    def key_usage():
        """Check API key usage."""
        from api_keys import get_usage
        key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "")
        if not key:
            return jsonify({"error": "Provide API key via X-API-Key header"}), 401
        usage = get_usage(key)
        if not usage:
            return jsonify({"error": "Invalid API key"}), 401
        return jsonify(usage)
    
    @app.route("/api/v1/pricing")
    def pricing():
        """Return pricing info."""
        from api_keys import TIERS
        return jsonify({
            "tiers": {k: {"name": v["name"], "price_cents": v["price"], 
                         "calls_per_day": v["calls_per_day"], "features": v["features"]}
                      for k, v in TIERS.items()},
            "stripe_configured": HAS_STRIPE,
        })
    
    print(f"  Stripe: {'configured' if HAS_STRIPE else 'not configured (set STRIPE_SECRET_KEY)'}")
