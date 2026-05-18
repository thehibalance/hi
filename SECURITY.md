# Security Policy

## Reporting a vulnerability

**Do not open a public issue for security vulnerabilities.**

Email: **security@thehibalance.org** (or **hi@thehibalance.org** if the security address isn't active yet)

Include:
- Description of the vulnerability
- Steps to reproduce
- Impact (what can an attacker do?)
- Suggested fix if you have one

We acknowledge within **48 hours** and aim to patch critical vulnerabilities within **7 days**.

## Scope

### In scope

- `api.thehibalance.org` — the REST API
- `thehibalance.org` — the main website
- Chrome Extension (published on Chrome Web Store)
- iOS App (published on App Store)
- All code in this repository

### Out of scope

- Third-party data providers (SEC, EPA, etc.) — report to them directly
- Self-hosted deployments of this code by others
- Scoring accuracy complaints — use [score-challenge issues](https://github.com/thehibalance/hi/issues/new)

## What we care about

- **Data exfiltration** — anything that could leak user PII (though we don't collect much)
- **API abuse** — rate limit bypasses, unauthorized write access
- **Extension injection** — XSS, content-script escape, CSP bypass
- **Supply chain** — malicious dependencies, typosquatting
- **Key leakage** — if you find an API key in our commits, report it immediately

## What we don't care about

- Missing security headers on marketing pages with no user input
- "X-Powered-By" header disclosures
- Rate limits as observed (these are by design)
- Clickjacking on `thehibalance.org` (all content is public)
- SPF/DMARC configs on non-transactional domains

## Rewards

We don't currently run a bounty program. We will:
- Publicly credit you in a SECURITY_THANKS.md file (if you want)
- Send swag once we have swag
- Owe you a beer

## PGP

Not currently set up. Use email.

---

Thank you for making HI Grade™ safer.
