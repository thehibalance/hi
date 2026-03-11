/**
 * HUMAN Score Seed Database v0.2.0
 * 206 companies across 120 categories
 * 
 * All scores are ESTIMATED based on publicly available information.
 * NO AI WAS USED TO GENERATE THESE SCORES.
 * 
 * Methodology: HUMAN Framework v1.0
 * Governed by: The Nahum Foundation
 */

const SEED_COMPANIES = [
  {
    "id": "apple",
    "name": "Apple Inc.",
    "domains": [
      "apple.com",
      "store.apple.com",
      "icloud.com"
    ],
    "tags": [
      "technology",
      "hardware",
      "software"
    ],
    "h": 52,
    "u": 45,
    "m": 38,
    "a": 55,
    "n": 42,
    "notes": "High craft in hardware design, but aggressive AI adoption. Right-to-repair improvements. Renewable energy leadership offset by supply chain concerns.",
    "confidence": "estimated"
  },
  {
    "id": "google",
    "name": "Alphabet / Google",
    "domains": [
      "google.com",
      "youtube.com",
      "cloud.google.com",
      "gmail.com"
    ],
    "tags": [
      "technology",
      "software",
      "advertising"
    ],
    "h": 35,
    "u": 30,
    "m": 28,
    "a": 40,
    "n": 32,
    "notes": "Heavy AI displacement across products. Surveillance capitalism model. Strong renewable commitments but massive data center footprint.",
    "confidence": "estimated"
  },
  {
    "id": "microsoft",
    "name": "Microsoft",
    "domains": [
      "microsoft.com",
      "azure.microsoft.com",
      "office.com",
      "linkedin.com",
      "github.com"
    ],
    "tags": [
      "technology",
      "software",
      "cloud"
    ],
    "h": 38,
    "u": 40,
    "m": 35,
    "a": 42,
    "n": 38,
    "notes": "Major AI investment (Copilot, OpenAI). Decent worker programs. Carbon negative pledge but growing data center demand.",
    "confidence": "estimated"
  },
  {
    "id": "amazon",
    "name": "Amazon",
    "domains": [
      "amazon.com",
      "aws.amazon.com",
      "wholefoods.com",
      "twitch.tv",
      "imdb.com"
    ],
    "tags": [
      "technology",
      "retail",
      "cloud"
    ],
    "h": 28,
    "u": 22,
    "m": 25,
    "a": 30,
    "n": 20,
    "notes": "Aggressive automation. Worker conditions criticized. Massive energy footprint from AWS.",
    "confidence": "estimated"
  },
  {
    "id": "meta",
    "name": "Meta Platforms",
    "domains": [
      "meta.com",
      "facebook.com",
      "instagram.com",
      "whatsapp.com",
      "threads.net"
    ],
    "tags": [
      "technology",
      "social media",
      "advertising"
    ],
    "h": 30,
    "u": 20,
    "m": 18,
    "a": 35,
    "n": 22,
    "notes": "AI-driven content and moderation. Data ethics concerns. Addiction-by-design features. Mass layoffs while increasing AI spend.",
    "confidence": "estimated"
  },
  {
    "id": "nvidia",
    "name": "NVIDIA",
    "domains": [
      "nvidia.com"
    ],
    "tags": [
      "technology",
      "hardware",
      "semiconductors"
    ],
    "h": 55,
    "u": 50,
    "m": 52,
    "a": 35,
    "n": 48,
    "notes": "High-skill engineering workforce. Enables AI displacement elsewhere but maintains deep human R&D.",
    "confidence": "estimated"
  },
  {
    "id": "tesla",
    "name": "Tesla",
    "domains": [
      "tesla.com"
    ],
    "tags": [
      "automotive",
      "technology",
      "energy"
    ],
    "h": 42,
    "u": 28,
    "m": 30,
    "a": 58,
    "n": 25,
    "notes": "Automation-heavy manufacturing. Customer service widely criticized. EV benefits offset by manufacturing impact.",
    "confidence": "estimated"
  },
  {
    "id": "netflix",
    "name": "Netflix",
    "domains": [
      "netflix.com"
    ],
    "tags": [
      "technology",
      "entertainment",
      "streaming"
    ],
    "h": 45,
    "u": 38,
    "m": 42,
    "a": 35,
    "n": 40,
    "notes": "Heavy AI in recommendations. Some original human content investment. Password sharing crackdown ethics.",
    "confidence": "estimated"
  },
  {
    "id": "oracle",
    "name": "Oracle",
    "domains": [
      "oracle.com"
    ],
    "tags": [
      "technology",
      "software",
      "cloud"
    ],
    "h": 42,
    "u": 35,
    "m": 30,
    "a": 38,
    "n": 32,
    "notes": "Enterprise software. Aggressive licensing practices. Growing cloud/AI infrastructure.",
    "confidence": "estimated"
  },
  {
    "id": "ibm",
    "name": "IBM",
    "domains": [
      "ibm.com"
    ],
    "tags": [
      "technology",
      "software",
      "consulting"
    ],
    "h": 45,
    "u": 42,
    "m": 40,
    "a": 42,
    "n": 45,
    "notes": "Long AI history (Watson). Consulting workforce maintains human element. Layoffs for AI replacement.",
    "confidence": "estimated"
  },
  {
    "id": "intel",
    "name": "Intel",
    "domains": [
      "intel.com"
    ],
    "tags": [
      "technology",
      "semiconductors"
    ],
    "h": 52,
    "u": 48,
    "m": 45,
    "a": 38,
    "n": 45,
    "notes": "Deep engineering craft in chip design. US manufacturing investment. Significant water and energy usage.",
    "confidence": "estimated"
  },
  {
    "id": "samsung",
    "name": "Samsung Electronics",
    "domains": [
      "samsung.com"
    ],
    "tags": [
      "technology",
      "hardware",
      "semiconductors"
    ],
    "h": 48,
    "u": 40,
    "m": 35,
    "a": 38,
    "n": 35,
    "notes": "Large manufacturing workforce. Mix of automation and skilled labor. Supply chain labor concerns.",
    "confidence": "estimated"
  },
  {
    "id": "salesforce",
    "name": "Salesforce",
    "domains": [
      "salesforce.com",
      "slack.com",
      "tableau.com"
    ],
    "tags": [
      "technology",
      "software",
      "cloud"
    ],
    "h": 45,
    "u": 50,
    "m": 48,
    "a": 45,
    "n": 50,
    "notes": "1-1-1 philanthropy model. AI integration growing. Decent worker benefits.",
    "confidence": "estimated"
  },
  {
    "id": "adobe",
    "name": "Adobe",
    "domains": [
      "adobe.com"
    ],
    "tags": [
      "technology",
      "software",
      "creative"
    ],
    "h": 48,
    "u": 42,
    "m": 40,
    "a": 42,
    "n": 38,
    "notes": "Creative tools for humans but adding Firefly AI. Content Credentials (C2PA) positive for transparency.",
    "confidence": "estimated"
  },
  {
    "id": "spotify",
    "name": "Spotify",
    "domains": [
      "spotify.com"
    ],
    "tags": [
      "technology",
      "music",
      "streaming"
    ],
    "h": 35,
    "u": 32,
    "m": 30,
    "a": 38,
    "n": 35,
    "notes": "AI playlists displacing human curators. Low artist royalty payments. Podcast layoffs.",
    "confidence": "estimated"
  },
  {
    "id": "uber",
    "name": "Uber",
    "domains": [
      "uber.com",
      "ubereats.com"
    ],
    "tags": [
      "technology",
      "transportation",
      "gig economy"
    ],
    "h": 30,
    "u": 28,
    "m": 25,
    "a": 32,
    "n": 30,
    "notes": "Gig worker model avoids employee protections. Pursuing autonomous vehicles. Surge pricing ethics.",
    "confidence": "estimated"
  },
  {
    "id": "airbnb",
    "name": "Airbnb",
    "domains": [
      "airbnb.com"
    ],
    "tags": [
      "technology",
      "hospitality",
      "marketplace"
    ],
    "h": 45,
    "u": 42,
    "m": 38,
    "a": 35,
    "n": 42,
    "notes": "Enables individual hosts. Housing market impact concerns. Community impact debates.",
    "confidence": "estimated"
  },
  {
    "id": "snapchat",
    "name": "Snap Inc.",
    "domains": [
      "snapchat.com",
      "snap.com"
    ],
    "tags": [
      "technology",
      "social media"
    ],
    "h": 35,
    "u": 30,
    "m": 32,
    "a": 35,
    "n": 28,
    "notes": "AI-driven content. MyAI chatbot targeting young users. Disappearing messages raise transparency questions.",
    "confidence": "estimated"
  },
  {
    "id": "tiktok",
    "name": "TikTok / ByteDance",
    "domains": [
      "tiktok.com"
    ],
    "tags": [
      "technology",
      "social media",
      "entertainment"
    ],
    "h": 25,
    "u": 18,
    "m": 15,
    "a": 30,
    "n": 12,
    "notes": "Highly addictive AI algorithm. Data privacy concerns. Displaces human-curated media.",
    "confidence": "estimated"
  },
  {
    "id": "pinterest",
    "name": "Pinterest",
    "domains": [
      "pinterest.com"
    ],
    "tags": [
      "technology",
      "social media"
    ],
    "h": 42,
    "u": 45,
    "m": 48,
    "a": 38,
    "n": 42,
    "notes": "Less toxic than peers. Supports human creators. Body image policy improvements.",
    "confidence": "estimated"
  },
  {
    "id": "shopify",
    "name": "Shopify",
    "domains": [
      "shopify.com"
    ],
    "tags": [
      "technology",
      "e-commerce",
      "platform"
    ],
    "h": 52,
    "u": 48,
    "m": 50,
    "a": 40,
    "n": 48,
    "notes": "Empowers small human-run businesses. Some AI tools for merchants. Enables creator economy.",
    "confidence": "estimated"
  },
  {
    "id": "stripe",
    "name": "Stripe",
    "domains": [
      "stripe.com"
    ],
    "tags": [
      "technology",
      "fintech",
      "payments"
    ],
    "h": 55,
    "u": 50,
    "m": 55,
    "a": 42,
    "n": 52,
    "notes": "Engineering-driven culture. Climate fund investment. Enables businesses of all sizes.",
    "confidence": "estimated"
  },
  {
    "id": "palantir",
    "name": "Palantir Technologies",
    "domains": [
      "palantir.com"
    ],
    "tags": [
      "technology",
      "data analytics",
      "defense"
    ],
    "h": 50,
    "u": 25,
    "m": 20,
    "a": 35,
    "n": 18,
    "notes": "Skilled human analysts but surveillance applications. Government contracts raise ethical questions.",
    "confidence": "estimated"
  },
  {
    "id": "zoom",
    "name": "Zoom",
    "domains": [
      "zoom.us"
    ],
    "tags": [
      "technology",
      "communications"
    ],
    "h": 42,
    "u": 45,
    "m": 40,
    "a": 38,
    "n": 38,
    "notes": "Connects humans but adding AI summaries. Privacy concerns in early pandemic.",
    "confidence": "estimated"
  },
  {
    "id": "dropbox",
    "name": "Dropbox",
    "domains": [
      "dropbox.com"
    ],
    "tags": [
      "technology",
      "cloud storage"
    ],
    "h": 48,
    "u": 45,
    "m": 50,
    "a": 40,
    "n": 48,
    "notes": "Shifted to virtual-first. AI features growing. Decent privacy stance.",
    "confidence": "estimated"
  },
  {
    "id": "openai",
    "name": "OpenAI",
    "domains": [
      "openai.com",
      "chatgpt.com"
    ],
    "tags": [
      "technology",
      "AI"
    ],
    "h": 40,
    "u": 30,
    "m": 25,
    "a": 22,
    "n": 20,
    "notes": "Core product displaces human workers across industries. Massive compute footprint. Safety team departures.",
    "confidence": "estimated"
  },
  {
    "id": "anthropic",
    "name": "Anthropic",
    "domains": [
      "anthropic.com",
      "claude.ai"
    ],
    "tags": [
      "technology",
      "AI"
    ],
    "h": 45,
    "u": 42,
    "m": 48,
    "a": 28,
    "n": 42,
    "notes": "Safety-focused AI. Constitutional AI approach. Still fundamentally an AI displacement company. Better ethics stance than peers.",
    "confidence": "estimated"
  },
  {
    "id": "basecamp",
    "name": "37signals / Basecamp",
    "domains": [
      "basecamp.com",
      "hey.com",
      "37signals.com"
    ],
    "tags": [
      "technology",
      "software"
    ],
    "h": 82,
    "u": 78,
    "m": 75,
    "a": 60,
    "n": 80,
    "notes": "Small team, anti-growth philosophy. No AI in core products. Strong worker benefits.",
    "confidence": "estimated"
  },
  {
    "id": "duckduckgo",
    "name": "DuckDuckGo",
    "domains": [
      "duckduckgo.com"
    ],
    "tags": [
      "technology",
      "search",
      "privacy"
    ],
    "h": 70,
    "u": 72,
    "m": 85,
    "a": 55,
    "n": 90,
    "notes": "Privacy-first model. Anti-surveillance. Small human team. Very high transparency.",
    "confidence": "estimated"
  },
  {
    "id": "mozilla",
    "name": "Mozilla",
    "domains": [
      "mozilla.org",
      "firefox.com"
    ],
    "tags": [
      "technology",
      "software",
      "nonprofit"
    ],
    "h": 72,
    "u": 68,
    "m": 78,
    "a": 50,
    "n": 85,
    "notes": "Open source foundation model. Human-rights focused. Some AI adoption with ethical guidelines.",
    "confidence": "estimated"
  },
  {
    "id": "signal_app",
    "name": "Signal Foundation",
    "domains": [
      "signal.org"
    ],
    "tags": [
      "technology",
      "communications",
      "privacy",
      "nonprofit"
    ],
    "h": 78,
    "u": 75,
    "m": 92,
    "a": 52,
    "n": 95,
    "notes": "Nonprofit. End-to-end encryption. Anti-surveillance. No data monetization. Maximum transparency.",
    "confidence": "estimated"
  },
  {
    "id": "proton",
    "name": "Proton AG",
    "domains": [
      "proton.me",
      "protonmail.com",
      "protonvpn.com"
    ],
    "tags": [
      "technology",
      "privacy",
      "email"
    ],
    "h": 72,
    "u": 70,
    "m": 88,
    "a": 55,
    "n": 88,
    "notes": "Privacy-first email and VPN. Swiss jurisdiction. Open source clients. No advertising model.",
    "confidence": "estimated"
  },
  {
    "id": "wordpress_auto",
    "name": "Automattic / WordPress",
    "domains": [
      "wordpress.com",
      "automattic.com",
      "tumblr.com"
    ],
    "tags": [
      "technology",
      "software",
      "publishing"
    ],
    "h": 68,
    "u": 62,
    "m": 70,
    "a": 48,
    "n": 75,
    "notes": "Powers 43% of the web. Open source core. Enables human publishers and creators.",
    "confidence": "estimated"
  },
  {
    "id": "framework",
    "name": "Framework Computer",
    "domains": [
      "frame.work"
    ],
    "tags": [
      "technology",
      "hardware"
    ],
    "h": 78,
    "u": 72,
    "m": 82,
    "a": 75,
    "n": 85,
    "notes": "Modular, repairable laptops. Anti-planned-obsolescence. Right-to-repair champion.",
    "confidence": "estimated"
  },
  {
    "id": "fairphone",
    "name": "Fairphone",
    "domains": [
      "fairphone.com"
    ],
    "tags": [
      "technology",
      "hardware",
      "mobile"
    ],
    "h": 80,
    "u": 75,
    "m": 88,
    "a": 82,
    "n": 88,
    "notes": "Fair trade electronics. Modular repairable phones. Conflict-free minerals. B Corp.",
    "confidence": "estimated"
  },
  {
    "id": "system76",
    "name": "System76",
    "domains": [
      "system76.com"
    ],
    "tags": [
      "technology",
      "hardware"
    ],
    "h": 75,
    "u": 68,
    "m": 72,
    "a": 60,
    "n": 78,
    "notes": "US-manufactured Linux computers. Small dedicated team. Open source firmware.",
    "confidence": "estimated"
  },
  {
    "id": "ifixit",
    "name": "iFixit",
    "domains": [
      "ifixit.com"
    ],
    "tags": [
      "technology",
      "repair",
      "education"
    ],
    "h": 82,
    "u": 80,
    "m": 90,
    "a": 78,
    "n": 92,
    "notes": "Right-to-repair advocacy. Free repair guides. Community-driven. Maximum transparency.",
    "confidence": "estimated"
  },
  {
    "id": "walmart",
    "name": "Walmart",
    "domains": [
      "walmart.com"
    ],
    "tags": [
      "retail",
      "grocery"
    ],
    "h": 35,
    "u": 30,
    "m": 32,
    "a": 28,
    "n": 30,
    "notes": "Aggressive automation. Low worker pay history. Supply chain labor concerns.",
    "confidence": "estimated"
  },
  {
    "id": "target",
    "name": "Target",
    "domains": [
      "target.com"
    ],
    "tags": [
      "retail"
    ],
    "h": 45,
    "u": 48,
    "m": 45,
    "a": 42,
    "n": 42,
    "notes": "Better worker pay than Walmart. Community investment. Self-checkout expansion.",
    "confidence": "estimated"
  },
  {
    "id": "costco",
    "name": "Costco",
    "domains": [
      "costco.com"
    ],
    "tags": [
      "retail",
      "grocery"
    ],
    "h": 65,
    "u": 70,
    "m": 72,
    "a": 48,
    "n": 55,
    "notes": "Above-industry wages. Strong worker retention. Human customer service.",
    "confidence": "estimated"
  },
  {
    "id": "etsy",
    "name": "Etsy",
    "domains": [
      "etsy.com"
    ],
    "tags": [
      "retail",
      "marketplace",
      "handmade"
    ],
    "h": 75,
    "u": 65,
    "m": 60,
    "a": 50,
    "n": 62,
    "notes": "Platform for human makers and artisans. B Corp certified. Seller fee controversies.",
    "confidence": "estimated"
  },
  {
    "id": "ikea",
    "name": "IKEA / Ingka Group",
    "domains": [
      "ikea.com"
    ],
    "tags": [
      "retail",
      "furniture",
      "home"
    ],
    "h": 55,
    "u": 58,
    "m": 55,
    "a": 62,
    "n": 52,
    "notes": "Mix of automation and human craft. Renewable investment. Circular economy initiatives.",
    "confidence": "estimated"
  },
  {
    "id": "trader_joes",
    "name": "Trader Joe's",
    "domains": [
      "traderjoes.com"
    ],
    "tags": [
      "retail",
      "grocery"
    ],
    "h": 72,
    "u": 75,
    "m": 68,
    "a": 52,
    "n": 45,
    "notes": "High employee satisfaction. Human-driven store experience. No self-checkout.",
    "confidence": "estimated"
  },
  {
    "id": "home_depot",
    "name": "Home Depot",
    "domains": [
      "homedepot.com"
    ],
    "tags": [
      "retail",
      "home improvement"
    ],
    "h": 50,
    "u": 48,
    "m": 45,
    "a": 38,
    "n": 40,
    "notes": "Human expertise in stores but growing self-checkout and AI.",
    "confidence": "estimated"
  },
  {
    "id": "lowes",
    "name": "Lowe's",
    "domains": [
      "lowes.com"
    ],
    "tags": [
      "retail",
      "home improvement"
    ],
    "h": 48,
    "u": 45,
    "m": 42,
    "a": 38,
    "n": 38,
    "notes": "Similar to Home Depot. Growing automation. Community investment programs.",
    "confidence": "estimated"
  },
  {
    "id": "best_buy",
    "name": "Best Buy",
    "domains": [
      "bestbuy.com"
    ],
    "tags": [
      "retail",
      "electronics"
    ],
    "h": 42,
    "u": 40,
    "m": 42,
    "a": 35,
    "n": 38,
    "notes": "Geek Squad human service model. Reducing floor staff. E-waste recycling.",
    "confidence": "estimated"
  },
  {
    "id": "rei",
    "name": "REI Co-op",
    "domains": [
      "rei.com"
    ],
    "tags": [
      "retail",
      "outdoor"
    ],
    "h": 72,
    "u": 70,
    "m": 75,
    "a": 72,
    "n": 68,
    "notes": "Co-op model. Employee profit sharing. Opt Outside campaign. Environmental advocacy.",
    "confidence": "estimated"
  },
  {
    "id": "nordstrom",
    "name": "Nordstrom",
    "domains": [
      "nordstrom.com"
    ],
    "tags": [
      "retail",
      "fashion"
    ],
    "h": 58,
    "u": 65,
    "m": 55,
    "a": 42,
    "n": 45,
    "notes": "Known for human customer service excellence. Fashion industry supply chain concerns.",
    "confidence": "estimated"
  },
  {
    "id": "temu",
    "name": "Temu",
    "domains": [
      "temu.com"
    ],
    "tags": [
      "retail",
      "marketplace"
    ],
    "h": 12,
    "u": 10,
    "m": 8,
    "a": 15,
    "n": 5,
    "notes": "Extreme low-cost model. Supply chain opacity. Gamification addiction. Near-zero transparency.",
    "confidence": "estimated"
  },
  {
    "id": "shein",
    "name": "Shein",
    "domains": [
      "shein.com",
      "us.shein.com"
    ],
    "tags": [
      "retail",
      "fashion",
      "fast fashion"
    ],
    "h": 15,
    "u": 12,
    "m": 10,
    "a": 8,
    "n": 8,
    "notes": "Ultra-fast fashion. AI-driven design. Worker exploitation allegations. Massive environmental footprint.",
    "confidence": "estimated"
  },
  {
    "id": "wish",
    "name": "Wish / ContextLogic",
    "domains": [
      "wish.com"
    ],
    "tags": [
      "retail",
      "marketplace"
    ],
    "h": 15,
    "u": 12,
    "m": 12,
    "a": 15,
    "n": 10,
    "notes": "Low-cost marketplace. Product quality and safety concerns. Limited transparency.",
    "confidence": "estimated"
  },
  {
    "id": "alibaba",
    "name": "Alibaba Group",
    "domains": [
      "alibaba.com",
      "aliexpress.com"
    ],
    "tags": [
      "retail",
      "technology",
      "marketplace"
    ],
    "h": 25,
    "u": 22,
    "m": 20,
    "a": 25,
    "n": 18,
    "notes": "Massive marketplace with automation. Limited global transparency.",
    "confidence": "estimated"
  },
  {
    "id": "starbucks",
    "name": "Starbucks",
    "domains": [
      "starbucks.com"
    ],
    "tags": [
      "food",
      "beverage",
      "retail"
    ],
    "h": 55,
    "u": 48,
    "m": 42,
    "a": 50,
    "n": 45,
    "notes": "Human barista model but increasing automation. Union-busting controversies. Fair trade sourcing.",
    "confidence": "estimated"
  },
  {
    "id": "ben_jerry",
    "name": "Ben & Jerry's",
    "domains": [
      "benjerry.com"
    ],
    "tags": [
      "food",
      "ice cream"
    ],
    "h": 78,
    "u": 75,
    "m": 80,
    "a": 65,
    "n": 78,
    "notes": "Strong social mission. Fair trade ingredients. Living wage commitment. Social activism.",
    "confidence": "estimated"
  },
  {
    "id": "nestle",
    "name": "Nestlé",
    "domains": [
      "nestle.com"
    ],
    "tags": [
      "food",
      "beverage",
      "consumer goods"
    ],
    "h": 38,
    "u": 30,
    "m": 22,
    "a": 32,
    "n": 28,
    "notes": "Water privatization. Child labor allegations. Baby formula marketing ethics.",
    "confidence": "estimated"
  },
  {
    "id": "coca_cola",
    "name": "Coca-Cola",
    "domains": [
      "coca-cola.com"
    ],
    "tags": [
      "food",
      "beverage"
    ],
    "h": 42,
    "u": 38,
    "m": 32,
    "a": 28,
    "n": 35,
    "notes": "Mixed labor record. Plastic pollution. Water usage concerns. Some sustainability efforts.",
    "confidence": "estimated"
  },
  {
    "id": "pepsi",
    "name": "PepsiCo",
    "domains": [
      "pepsico.com"
    ],
    "tags": [
      "food",
      "beverage",
      "snacks"
    ],
    "h": 42,
    "u": 40,
    "m": 35,
    "a": 32,
    "n": 38,
    "notes": "Similar to Coca-Cola. Positive Water initiatives. Growing sustainability programs.",
    "confidence": "estimated"
  },
  {
    "id": "mcdonalds",
    "name": "McDonald's",
    "domains": [
      "mcdonalds.com"
    ],
    "tags": [
      "food",
      "restaurant",
      "fast food"
    ],
    "h": 35,
    "u": 30,
    "m": 28,
    "a": 25,
    "n": 32,
    "notes": "Automation in ordering. Franchise model. Low-wage workforce. Beef supply chain footprint.",
    "confidence": "estimated"
  },
  {
    "id": "chipotle",
    "name": "Chipotle",
    "domains": [
      "chipotle.com"
    ],
    "tags": [
      "food",
      "restaurant"
    ],
    "h": 55,
    "u": 50,
    "m": 52,
    "a": 52,
    "n": 50,
    "notes": "Food with integrity mission. Human kitchen prep. Better sourcing than fast food peers.",
    "confidence": "estimated"
  },
  {
    "id": "sweetgreen",
    "name": "Sweetgreen",
    "domains": [
      "sweetgreen.com"
    ],
    "tags": [
      "food",
      "restaurant"
    ],
    "h": 48,
    "u": 45,
    "m": 55,
    "a": 58,
    "n": 52,
    "notes": "Infinite Kitchen automation reduces human roles. Local sourcing. Sustainability focus.",
    "confidence": "estimated"
  },
  {
    "id": "chick_fil_a",
    "name": "Chick-fil-A",
    "domains": [
      "chick-fil-a.com"
    ],
    "tags": [
      "food",
      "restaurant",
      "fast food"
    ],
    "h": 58,
    "u": 65,
    "m": 45,
    "a": 35,
    "n": 35,
    "notes": "Strong human customer service culture. Political donation controversies.",
    "confidence": "estimated"
  },
  {
    "id": "whole_foods",
    "name": "Whole Foods Market",
    "domains": [
      "wholefoodsmarket.com"
    ],
    "tags": [
      "food",
      "grocery",
      "organic"
    ],
    "h": 55,
    "u": 50,
    "m": 48,
    "a": 60,
    "n": 45,
    "notes": "Amazon-owned. Previously higher consciousness. Organic focus. Some automation creep.",
    "confidence": "estimated"
  },
  {
    "id": "clif_bar",
    "name": "Clif Bar & Company",
    "domains": [
      "clifbar.com"
    ],
    "tags": [
      "food",
      "snacks",
      "organic"
    ],
    "h": 72,
    "u": 68,
    "m": 75,
    "a": 70,
    "n": 68,
    "notes": "B Corp heritage. Organic ingredients. Community investment.",
    "confidence": "estimated"
  },
  {
    "id": "newman_own",
    "name": "Newman's Own",
    "domains": [
      "newmansown.com"
    ],
    "tags": [
      "food",
      "grocery"
    ],
    "h": 75,
    "u": 72,
    "m": 88,
    "a": 62,
    "n": 75,
    "notes": "100% profits to charity. Organic options. Transparent mission.",
    "confidence": "estimated"
  },
  {
    "id": "dr_bronners",
    "name": "Dr. Bronner's",
    "domains": [
      "drbronner.com"
    ],
    "tags": [
      "personal care",
      "organic"
    ],
    "h": 90,
    "u": 88,
    "m": 92,
    "a": 88,
    "n": 90,
    "notes": "Family-owned. CEO salary capped at 5x lowest worker. Fair trade. Regenerative farming.",
    "confidence": "estimated"
  },
  {
    "id": "king_arthur",
    "name": "King Arthur Baking",
    "domains": [
      "kingarthurbaking.com"
    ],
    "tags": [
      "food",
      "baking"
    ],
    "h": 85,
    "u": 82,
    "m": 85,
    "a": 70,
    "n": 80,
    "notes": "Employee-owned (ESOP). B Corp. Community baking education. Transparent sourcing.",
    "confidence": "estimated"
  },
  {
    "id": "equal_exchange",
    "name": "Equal Exchange",
    "domains": [
      "equalexchange.coop"
    ],
    "tags": [
      "food",
      "coffee",
      "cooperative"
    ],
    "h": 88,
    "u": 85,
    "m": 90,
    "a": 72,
    "n": 88,
    "notes": "Worker-owned cooperative. Fair trade pioneer. Direct farmer relationships.",
    "confidence": "estimated"
  },
  {
    "id": "danone",
    "name": "Danone",
    "domains": [
      "danone.com"
    ],
    "tags": [
      "food",
      "dairy",
      "beverage"
    ],
    "h": 48,
    "u": 45,
    "m": 52,
    "a": 55,
    "n": 48,
    "notes": "B Corp certified (North America). One Planet One Health mission.",
    "confidence": "estimated"
  },
  {
    "id": "patagonia",
    "name": "Patagonia",
    "domains": [
      "patagonia.com"
    ],
    "tags": [
      "retail",
      "outdoor",
      "apparel"
    ],
    "h": 88,
    "u": 85,
    "m": 90,
    "a": 92,
    "n": 88,
    "notes": "Earth ownership model. Repair program. Living wages. Environmental activism.",
    "confidence": "estimated"
  },
  {
    "id": "eileen_fisher",
    "name": "Eileen Fisher",
    "domains": [
      "eileenfisher.com"
    ],
    "tags": [
      "apparel",
      "fashion"
    ],
    "h": 82,
    "u": 78,
    "m": 80,
    "a": 78,
    "n": 75,
    "notes": "B Corp. Circular design. Living wages. Take-back program.",
    "confidence": "estimated"
  },
  {
    "id": "allbirds",
    "name": "Allbirds",
    "domains": [
      "allbirds.com"
    ],
    "tags": [
      "apparel",
      "footwear"
    ],
    "h": 65,
    "u": 60,
    "m": 68,
    "a": 72,
    "n": 70,
    "notes": "Sustainable materials. Carbon footprint labeling. B Corp.",
    "confidence": "estimated"
  },
  {
    "id": "nike",
    "name": "Nike",
    "domains": [
      "nike.com"
    ],
    "tags": [
      "apparel",
      "footwear",
      "sports"
    ],
    "h": 42,
    "u": 38,
    "m": 35,
    "a": 42,
    "n": 38,
    "notes": "Largely automated manufacturing. Supply chain labor history. Sustainability targets growing.",
    "confidence": "estimated"
  },
  {
    "id": "hm",
    "name": "H&M",
    "domains": [
      "hm.com"
    ],
    "tags": [
      "apparel",
      "fast fashion"
    ],
    "h": 28,
    "u": 30,
    "m": 30,
    "a": 28,
    "n": 35,
    "notes": "Fast fashion model. Supply chain labor issues. Some transparency efforts.",
    "confidence": "estimated"
  },
  {
    "id": "zara",
    "name": "Zara / Inditex",
    "domains": [
      "zara.com"
    ],
    "tags": [
      "apparel",
      "fast fashion"
    ],
    "h": 30,
    "u": 28,
    "m": 28,
    "a": 30,
    "n": 30,
    "notes": "Fast fashion at scale. Some sustainability commitments. Supply chain complexity.",
    "confidence": "estimated"
  },
  {
    "id": "everlane",
    "name": "Everlane",
    "domains": [
      "everlane.com"
    ],
    "tags": [
      "apparel",
      "fashion"
    ],
    "h": 55,
    "u": 48,
    "m": 52,
    "a": 55,
    "n": 62,
    "notes": "Radical transparency on pricing and factories. Some ethical sourcing gaps exposed.",
    "confidence": "estimated"
  },
  {
    "id": "dansko",
    "name": "Dansko",
    "domains": [
      "dansko.com"
    ],
    "tags": [
      "footwear",
      "apparel"
    ],
    "h": 78,
    "u": 72,
    "m": 75,
    "a": 65,
    "n": 70,
    "notes": "B Corp. Employee wellness programs. Durable product design.",
    "confidence": "estimated"
  },
  {
    "id": "tentree",
    "name": "Tentree",
    "domains": [
      "tentree.com"
    ],
    "tags": [
      "apparel",
      "sustainable"
    ],
    "h": 62,
    "u": 60,
    "m": 72,
    "a": 80,
    "n": 72,
    "notes": "Plants 10 trees per item. B Corp. Transparent supply chain mapping.",
    "confidence": "estimated"
  },
  {
    "id": "levi",
    "name": "Levi Strauss & Co.",
    "domains": [
      "levi.com",
      "levis.com"
    ],
    "tags": [
      "apparel",
      "denim"
    ],
    "h": 52,
    "u": 50,
    "m": 52,
    "a": 48,
    "n": 50,
    "notes": "Heritage craft brand. Worker Well-being initiative. Water conservation.",
    "confidence": "estimated"
  },
  {
    "id": "gap",
    "name": "Gap Inc.",
    "domains": [
      "gap.com",
      "oldnavy.com",
      "bananarepublic.com",
      "athleta.com"
    ],
    "tags": [
      "apparel",
      "retail"
    ],
    "h": 38,
    "u": 38,
    "m": 35,
    "a": 35,
    "n": 38,
    "notes": "Large-scale manufacturing. Athleta is B Corp. Mixed labor record.",
    "confidence": "estimated"
  },
  {
    "id": "lululemon",
    "name": "Lululemon",
    "domains": [
      "lululemon.com"
    ],
    "tags": [
      "apparel",
      "athletic"
    ],
    "h": 50,
    "u": 48,
    "m": 45,
    "a": 42,
    "n": 42,
    "notes": "Human store experience. Some supply chain concerns. Community yoga programs.",
    "confidence": "estimated"
  },
  {
    "id": "jpmorgan",
    "name": "JPMorgan Chase",
    "domains": [
      "jpmorganchase.com",
      "chase.com"
    ],
    "tags": [
      "finance",
      "banking"
    ],
    "h": 40,
    "u": 35,
    "m": 30,
    "a": 38,
    "n": 35,
    "notes": "Heavy AI adoption in trading. Regulatory fines history.",
    "confidence": "estimated"
  },
  {
    "id": "bofa",
    "name": "Bank of America",
    "domains": [
      "bankofamerica.com"
    ],
    "tags": [
      "finance",
      "banking"
    ],
    "h": 38,
    "u": 35,
    "m": 32,
    "a": 40,
    "n": 35,
    "notes": "Erica AI chatbot. Overdraft fee reforms. Climate finance commitments.",
    "confidence": "estimated"
  },
  {
    "id": "wells_fargo",
    "name": "Wells Fargo",
    "domains": [
      "wellsfargo.com"
    ],
    "tags": [
      "finance",
      "banking"
    ],
    "h": 38,
    "u": 28,
    "m": 18,
    "a": 35,
    "n": 25,
    "notes": "Fake accounts scandal. Repeated regulatory violations.",
    "confidence": "estimated"
  },
  {
    "id": "goldman",
    "name": "Goldman Sachs",
    "domains": [
      "goldmansachs.com"
    ],
    "tags": [
      "finance",
      "investment banking"
    ],
    "h": 45,
    "u": 30,
    "m": 25,
    "a": 35,
    "n": 30,
    "notes": "Elite human talent but growing AI. 1MDB scandal.",
    "confidence": "estimated"
  },
  {
    "id": "vanguard",
    "name": "Vanguard",
    "domains": [
      "vanguard.com"
    ],
    "tags": [
      "finance",
      "investment"
    ],
    "h": 55,
    "u": 60,
    "m": 65,
    "a": 45,
    "n": 58,
    "notes": "Investor-owned structure. Human advisors. Low-cost mission.",
    "confidence": "estimated"
  },
  {
    "id": "fidelity",
    "name": "Fidelity Investments",
    "domains": [
      "fidelity.com"
    ],
    "tags": [
      "finance",
      "investment"
    ],
    "h": 52,
    "u": 55,
    "m": 55,
    "a": 42,
    "n": 50,
    "notes": "Family-owned. Human advisor access. Growing AI tools.",
    "confidence": "estimated"
  },
  {
    "id": "paypal",
    "name": "PayPal",
    "domains": [
      "paypal.com",
      "venmo.com"
    ],
    "tags": [
      "finance",
      "fintech",
      "payments"
    ],
    "h": 38,
    "u": 35,
    "m": 35,
    "a": 35,
    "n": 38,
    "notes": "Account freezing controversies. Mass layoffs.",
    "confidence": "estimated"
  },
  {
    "id": "aspiration",
    "name": "Aspiration",
    "domains": [
      "aspiration.com"
    ],
    "tags": [
      "finance",
      "banking",
      "sustainable"
    ],
    "h": 58,
    "u": 60,
    "m": 65,
    "a": 72,
    "n": 62,
    "notes": "Fossil-fuel-free deposits. Pay-what-is-fair model. Climate-focused banking.",
    "confidence": "estimated"
  },
  {
    "id": "amalgamated",
    "name": "Amalgamated Bank",
    "domains": [
      "amalgamatedbank.com"
    ],
    "tags": [
      "finance",
      "banking",
      "union"
    ],
    "h": 68,
    "u": 65,
    "m": 75,
    "a": 62,
    "n": 70,
    "notes": "Union-owned. B Corp. Divested from fossil fuels. Social justice mission.",
    "confidence": "estimated"
  },
  {
    "id": "johnson_johnson",
    "name": "Johnson & Johnson",
    "domains": [
      "jnj.com"
    ],
    "tags": [
      "healthcare",
      "pharmaceutical"
    ],
    "h": 48,
    "u": 42,
    "m": 28,
    "a": 38,
    "n": 30,
    "notes": "Talc powder lawsuits. Opioid litigation. Some good health access programs.",
    "confidence": "estimated"
  },
  {
    "id": "pfizer",
    "name": "Pfizer",
    "domains": [
      "pfizer.com"
    ],
    "tags": [
      "healthcare",
      "pharmaceutical"
    ],
    "h": 52,
    "u": 45,
    "m": 38,
    "a": 35,
    "n": 35,
    "notes": "COVID vaccine development. Drug pricing concerns.",
    "confidence": "estimated"
  },
  {
    "id": "cvs",
    "name": "CVS Health",
    "domains": [
      "cvs.com"
    ],
    "tags": [
      "healthcare",
      "pharmacy",
      "retail"
    ],
    "h": 48,
    "u": 45,
    "m": 42,
    "a": 35,
    "n": 40,
    "notes": "Pharmacy human interaction. MinuteClinic human care. Growing self-service.",
    "confidence": "estimated"
  },
  {
    "id": "unitedhealth",
    "name": "UnitedHealth Group",
    "domains": [
      "uhg.com",
      "uhc.com"
    ],
    "tags": [
      "healthcare",
      "insurance"
    ],
    "h": 35,
    "u": 28,
    "m": 20,
    "a": 32,
    "n": 22,
    "notes": "AI claim denials controversy. Record profits while denying care.",
    "confidence": "estimated"
  },
  {
    "id": "seventh_gen",
    "name": "Seventh Generation",
    "domains": [
      "seventhgeneration.com"
    ],
    "tags": [
      "household",
      "cleaning",
      "sustainable"
    ],
    "h": 68,
    "u": 65,
    "m": 78,
    "a": 80,
    "n": 75,
    "notes": "B Corp. Plant-based formulas. Transparent ingredients.",
    "confidence": "estimated"
  },
  {
    "id": "burts_bees",
    "name": "Burt's Bees",
    "domains": [
      "burtsbees.com"
    ],
    "tags": [
      "personal care",
      "natural"
    ],
    "h": 62,
    "u": 58,
    "m": 65,
    "a": 68,
    "n": 60,
    "notes": "Natural ingredients focus. B Corp.",
    "confidence": "estimated"
  },
  {
    "id": "toyota",
    "name": "Toyota",
    "domains": [
      "toyota.com"
    ],
    "tags": [
      "automotive"
    ],
    "h": 52,
    "u": 48,
    "m": 50,
    "a": 50,
    "n": 45,
    "notes": "Kaizen philosophy values human workers. Hybrid leadership.",
    "confidence": "estimated"
  },
  {
    "id": "ford",
    "name": "Ford Motor Company",
    "domains": [
      "ford.com"
    ],
    "tags": [
      "automotive"
    ],
    "h": 48,
    "u": 42,
    "m": 42,
    "a": 45,
    "n": 40,
    "notes": "EV transition. UAW labor relationship. Community investment heritage.",
    "confidence": "estimated"
  },
  {
    "id": "gm",
    "name": "General Motors",
    "domains": [
      "gm.com"
    ],
    "tags": [
      "automotive"
    ],
    "h": 42,
    "u": 38,
    "m": 38,
    "a": 48,
    "n": 38,
    "notes": "Cruise autonomous vehicle setbacks. EV investment. Growing automation.",
    "confidence": "estimated"
  },
  {
    "id": "rivian",
    "name": "Rivian",
    "domains": [
      "rivian.com"
    ],
    "tags": [
      "automotive",
      "electric"
    ],
    "h": 55,
    "u": 52,
    "m": 58,
    "a": 65,
    "n": 55,
    "notes": "EV-only manufacturer. Conservation focus. Growing workforce.",
    "confidence": "estimated"
  },
  {
    "id": "subaru",
    "name": "Subaru",
    "domains": [
      "subaru.com"
    ],
    "tags": [
      "automotive"
    ],
    "h": 55,
    "u": 55,
    "m": 58,
    "a": 55,
    "n": 50,
    "notes": "Zero-landfill manufacturing. Strong owner community. Love Promise.",
    "confidence": "estimated"
  },
  {
    "id": "exxon",
    "name": "ExxonMobil",
    "domains": [
      "exxonmobil.com"
    ],
    "tags": [
      "energy",
      "oil",
      "gas"
    ],
    "h": 45,
    "u": 30,
    "m": 12,
    "a": 10,
    "n": 15,
    "notes": "Climate denial funding history. Major environmental footprint.",
    "confidence": "estimated"
  },
  {
    "id": "shell",
    "name": "Shell plc",
    "domains": [
      "shell.com"
    ],
    "tags": [
      "energy",
      "oil",
      "gas"
    ],
    "h": 45,
    "u": 32,
    "m": 18,
    "a": 15,
    "n": 22,
    "notes": "Nigerian delta controversies. Climate pledges but continued fossil expansion.",
    "confidence": "estimated"
  },
  {
    "id": "bp",
    "name": "BP",
    "domains": [
      "bp.com"
    ],
    "tags": [
      "energy",
      "oil",
      "gas"
    ],
    "h": 42,
    "u": 30,
    "m": 15,
    "a": 12,
    "n": 20,
    "notes": "Deepwater Horizon legacy. Rolled back climate targets.",
    "confidence": "estimated"
  },
  {
    "id": "nextera",
    "name": "NextEra Energy",
    "domains": [
      "nexteraenergy.com"
    ],
    "tags": [
      "energy",
      "renewable",
      "utility"
    ],
    "h": 52,
    "u": 48,
    "m": 55,
    "a": 72,
    "n": 55,
    "notes": "World's largest generator of wind and solar. Some lobbying concerns.",
    "confidence": "estimated"
  },
  {
    "id": "enphase",
    "name": "Enphase Energy",
    "domains": [
      "enphase.com"
    ],
    "tags": [
      "energy",
      "solar",
      "technology"
    ],
    "h": 58,
    "u": 52,
    "m": 60,
    "a": 78,
    "n": 60,
    "notes": "Solar microinverter technology. Enabling distributed clean energy.",
    "confidence": "estimated"
  },
  {
    "id": "disney",
    "name": "The Walt Disney Company",
    "domains": [
      "disney.com",
      "disneyplus.com",
      "hulu.com",
      "espn.com"
    ],
    "tags": [
      "entertainment",
      "media",
      "streaming"
    ],
    "h": 52,
    "u": 45,
    "m": 40,
    "a": 38,
    "n": 35,
    "notes": "Creative workforce. Theme park human cast members. IP protection aggressiveness.",
    "confidence": "estimated"
  },
  {
    "id": "nytimes",
    "name": "The New York Times",
    "domains": [
      "nytimes.com"
    ],
    "tags": [
      "media",
      "journalism"
    ],
    "h": 72,
    "u": 58,
    "m": 62,
    "a": 40,
    "n": 70,
    "notes": "Human journalism is core product. Strong editorial standards. OpenAI lawsuit.",
    "confidence": "estimated"
  },
  {
    "id": "guardian",
    "name": "The Guardian",
    "domains": [
      "theguardian.com"
    ],
    "tags": [
      "media",
      "journalism",
      "nonprofit"
    ],
    "h": 75,
    "u": 65,
    "m": 72,
    "a": 48,
    "n": 82,
    "notes": "Scott Trust ownership. No paywall. Climate journalism leadership. High transparency.",
    "confidence": "estimated"
  },
  {
    "id": "substack",
    "name": "Substack",
    "domains": [
      "substack.com"
    ],
    "tags": [
      "media",
      "publishing",
      "platform"
    ],
    "h": 68,
    "u": 58,
    "m": 52,
    "a": 38,
    "n": 55,
    "notes": "Empowers independent human writers. Creator-first economics.",
    "confidence": "estimated"
  },
  {
    "id": "mckinsey",
    "name": "McKinsey & Company",
    "domains": [
      "mckinsey.com"
    ],
    "tags": [
      "consulting",
      "professional services"
    ],
    "h": 55,
    "u": 35,
    "m": 22,
    "a": 38,
    "n": 20,
    "notes": "Elite human talent. Opioid advisory scandal. Low transparency.",
    "confidence": "estimated"
  },
  {
    "id": "deloitte",
    "name": "Deloitte",
    "domains": [
      "deloitte.com"
    ],
    "tags": [
      "consulting",
      "audit"
    ],
    "h": 50,
    "u": 42,
    "m": 38,
    "a": 40,
    "n": 42,
    "notes": "Large human workforce. Growing AI integration. Audit quality concerns.",
    "confidence": "estimated"
  },
  {
    "id": "accenture",
    "name": "Accenture",
    "domains": [
      "accenture.com"
    ],
    "tags": [
      "consulting",
      "technology"
    ],
    "h": 42,
    "u": 38,
    "m": 38,
    "a": 42,
    "n": 40,
    "notes": "Massive AI push. 30K+ layoffs while investing in AI. Helps others automate.",
    "confidence": "estimated"
  },
  {
    "id": "att",
    "name": "AT&T",
    "domains": [
      "att.com"
    ],
    "tags": [
      "telecommunications"
    ],
    "h": 38,
    "u": 30,
    "m": 32,
    "a": 35,
    "n": 28,
    "notes": "Declining customer service quality. Chatbot-first support. Data breach history.",
    "confidence": "estimated"
  },
  {
    "id": "verizon",
    "name": "Verizon",
    "domains": [
      "verizon.com"
    ],
    "tags": [
      "telecommunications"
    ],
    "h": 40,
    "u": 35,
    "m": 35,
    "a": 38,
    "n": 32,
    "notes": "Union workforce. Growing AI in customer service.",
    "confidence": "estimated"
  },
  {
    "id": "tmobile",
    "name": "T-Mobile",
    "domains": [
      "t-mobile.com"
    ],
    "tags": [
      "telecommunications"
    ],
    "h": 42,
    "u": 45,
    "m": 38,
    "a": 35,
    "n": 35,
    "notes": "Better customer service than peers. Human retail experience.",
    "confidence": "estimated"
  },
  {
    "id": "ups",
    "name": "UPS",
    "domains": [
      "ups.com"
    ],
    "tags": [
      "logistics",
      "shipping"
    ],
    "h": 52,
    "u": 45,
    "m": 48,
    "a": 38,
    "n": 42,
    "notes": "Large human driver workforce. Teamsters union. Some automation in sorting.",
    "confidence": "estimated"
  },
  {
    "id": "fedex",
    "name": "FedEx",
    "domains": [
      "fedex.com"
    ],
    "tags": [
      "logistics",
      "shipping"
    ],
    "h": 48,
    "u": 42,
    "m": 42,
    "a": 35,
    "n": 38,
    "notes": "Large workforce. Contractor model for ground raises labor questions.",
    "confidence": "estimated"
  },
  {
    "id": "southwest",
    "name": "Southwest Airlines",
    "domains": [
      "southwest.com"
    ],
    "tags": [
      "transportation",
      "airline"
    ],
    "h": 58,
    "u": 62,
    "m": 55,
    "a": 35,
    "n": 48,
    "notes": "Employee-first culture. Profit sharing.",
    "confidence": "estimated"
  },
  {
    "id": "delta",
    "name": "Delta Air Lines",
    "domains": [
      "delta.com"
    ],
    "tags": [
      "transportation",
      "airline"
    ],
    "h": 52,
    "u": 55,
    "m": 48,
    "a": 35,
    "n": 42,
    "notes": "Profit sharing with employees. Premium service investment.",
    "confidence": "estimated"
  },
  {
    "id": "marriott",
    "name": "Marriott International",
    "domains": [
      "marriott.com"
    ],
    "tags": [
      "hospitality",
      "hotel"
    ],
    "h": 52,
    "u": 50,
    "m": 42,
    "a": 38,
    "n": 38,
    "notes": "Large human workforce. Service culture. Data breach history.",
    "confidence": "estimated"
  },
  {
    "id": "hilton",
    "name": "Hilton",
    "domains": [
      "hilton.com"
    ],
    "tags": [
      "hospitality",
      "hotel"
    ],
    "h": 50,
    "u": 48,
    "m": 45,
    "a": 42,
    "n": 40,
    "notes": "Great Place to Work reputation. Human service focus.",
    "confidence": "estimated"
  },
  {
    "id": "khan_academy",
    "name": "Khan Academy",
    "domains": [
      "khanacademy.org"
    ],
    "tags": [
      "education",
      "nonprofit",
      "technology"
    ],
    "h": 72,
    "u": 78,
    "m": 85,
    "a": 45,
    "n": 80,
    "notes": "Free education mission. AI tutor supplements human learning. Nonprofit. High transparency.",
    "confidence": "estimated"
  },
  {
    "id": "coursera",
    "name": "Coursera",
    "domains": [
      "coursera.org"
    ],
    "tags": [
      "education",
      "technology"
    ],
    "h": 55,
    "u": 52,
    "m": 55,
    "a": 38,
    "n": 50,
    "notes": "Connects human instructors with learners. Growing AI features.",
    "confidence": "estimated"
  },
  {
    "id": "duolingo",
    "name": "Duolingo",
    "domains": [
      "duolingo.com"
    ],
    "tags": [
      "education",
      "technology",
      "language"
    ],
    "h": 35,
    "u": 32,
    "m": 38,
    "a": 35,
    "n": 40,
    "notes": "Replaced human translators with AI. Gamification engagement.",
    "confidence": "estimated"
  },
  {
    "id": "chegg",
    "name": "Chegg",
    "domains": [
      "chegg.com"
    ],
    "tags": [
      "education",
      "technology"
    ],
    "h": 30,
    "u": 28,
    "m": 25,
    "a": 35,
    "n": 30,
    "notes": "AI replacing human tutors. Academic integrity concerns.",
    "confidence": "estimated"
  },
  {
    "id": "clearview_ai",
    "name": "Clearview AI",
    "domains": [
      "clearview.ai"
    ],
    "tags": [
      "technology",
      "surveillance",
      "AI"
    ],
    "h": 20,
    "u": 8,
    "m": 5,
    "a": 30,
    "n": 10,
    "notes": "Facial recognition surveillance. Scraped billions of photos without consent.",
    "confidence": "estimated"
  },
  {
    "id": "nso_group",
    "name": "NSO Group",
    "domains": [
      "nsogroup.com"
    ],
    "tags": [
      "technology",
      "surveillance"
    ],
    "h": 30,
    "u": 5,
    "m": 2,
    "a": 30,
    "n": 5,
    "notes": "Pegasus spyware. Used against journalists and activists.",
    "confidence": "estimated"
  },
  {
    "id": "ring",
    "name": "Ring (Amazon)",
    "domains": [
      "ring.com"
    ],
    "tags": [
      "technology",
      "surveillance",
      "smart home"
    ],
    "h": 30,
    "u": 25,
    "m": 18,
    "a": 30,
    "n": 20,
    "notes": "Police partnership program. Neighborhood surveillance network.",
    "confidence": "estimated"
  },
  {
    "id": "darn_tough",
    "name": "Darn Tough Vermont",
    "domains": [
      "darntough.com"
    ],
    "tags": [
      "apparel",
      "manufacturing"
    ],
    "h": 88,
    "u": 80,
    "m": 82,
    "a": 68,
    "n": 75,
    "notes": "US-manufactured socks. Lifetime guarantee. Anti-planned-obsolescence.",
    "confidence": "estimated"
  },
  {
    "id": "lodge_cast_iron",
    "name": "Lodge Cast Iron",
    "domains": [
      "lodgecastiron.com"
    ],
    "tags": [
      "housewares",
      "manufacturing"
    ],
    "h": 85,
    "u": 75,
    "m": 80,
    "a": 65,
    "n": 72,
    "notes": "US-manufactured since 1896. Employee-owned since 2021. Products last lifetimes.",
    "confidence": "estimated"
  },
  {
    "id": "vermont_country_store",
    "name": "Vermont Country Store",
    "domains": [
      "vermontcountrystore.com"
    ],
    "tags": [
      "retail",
      "general store"
    ],
    "h": 82,
    "u": 80,
    "m": 78,
    "a": 60,
    "n": 70,
    "notes": "Family-owned since 1946. Human customer service. Anti-Amazon positioning.",
    "confidence": "estimated"
  },
  {
    "id": "bobs_red_mill",
    "name": "Bob's Red Mill",
    "domains": [
      "bobsredmill.com"
    ],
    "tags": [
      "food",
      "baking",
      "organic"
    ],
    "h": 85,
    "u": 82,
    "m": 85,
    "a": 68,
    "n": 78,
    "notes": "Employee-owned (ESOP). Founder gave company to workers. Stone-milled grains.",
    "confidence": "estimated"
  },
  {
    "id": "klean_kanteen",
    "name": "Klean Kanteen",
    "domains": [
      "kleankanteen.com"
    ],
    "tags": [
      "housewares",
      "sustainable"
    ],
    "h": 72,
    "u": 68,
    "m": 78,
    "a": 82,
    "n": 75,
    "notes": "B Corp. Climate Neutral. Family-owned. 1% for the Planet.",
    "confidence": "estimated"
  },
  {
    "id": "new_belgium",
    "name": "New Belgium Brewing",
    "domains": [
      "newbelgium.com"
    ],
    "tags": [
      "beverage",
      "beer",
      "craft"
    ],
    "h": 75,
    "u": 70,
    "m": 75,
    "a": 78,
    "n": 72,
    "notes": "B Corp. First wind-powered brewery. Community cycling advocacy.",
    "confidence": "estimated"
  },
  {
    "id": "osprey",
    "name": "Osprey Packs",
    "domains": [
      "osprey.com"
    ],
    "tags": [
      "outdoor",
      "gear"
    ],
    "h": 72,
    "u": 68,
    "m": 72,
    "a": 65,
    "n": 65,
    "notes": "All Mighty Guarantee (lifetime repair). Durable design philosophy.",
    "confidence": "estimated"
  },
  {
    "id": "vita_coco",
    "name": "Vita Coco",
    "domains": [
      "vitacoco.com"
    ],
    "tags": [
      "beverage",
      "coconut water"
    ],
    "h": 58,
    "u": 55,
    "m": 60,
    "a": 58,
    "n": 55,
    "notes": "B Corp. Community development in farming regions.",
    "confidence": "estimated"
  },
  {
    "id": "valve",
    "name": "Valve Corporation",
    "domains": [
      "valvesoftware.com",
      "steampowered.com"
    ],
    "tags": [
      "technology",
      "gaming"
    ],
    "h": 62,
    "u": 50,
    "m": 48,
    "a": 35,
    "n": 35,
    "notes": "Flat organization. Human game development. Enables indie developers.",
    "confidence": "estimated"
  },
  {
    "id": "ea",
    "name": "Electronic Arts",
    "domains": [
      "ea.com"
    ],
    "tags": [
      "technology",
      "gaming"
    ],
    "h": 42,
    "u": 30,
    "m": 25,
    "a": 35,
    "n": 30,
    "notes": "Microtransaction controversies. Loot box gambling. Mass layoffs.",
    "confidence": "estimated"
  },
  {
    "id": "activision",
    "name": "Activision Blizzard (Microsoft)",
    "domains": [
      "activision.com",
      "blizzard.com"
    ],
    "tags": [
      "technology",
      "gaming"
    ],
    "h": 40,
    "u": 25,
    "m": 20,
    "a": 35,
    "n": 25,
    "notes": "Workplace harassment scandals. Creative talent within.",
    "confidence": "estimated"
  },
  {
    "id": "nintendo",
    "name": "Nintendo",
    "domains": [
      "nintendo.com"
    ],
    "tags": [
      "technology",
      "gaming"
    ],
    "h": 68,
    "u": 60,
    "m": 55,
    "a": 42,
    "n": 40,
    "notes": "Strong creative human game design. Family-friendly values.",
    "confidence": "estimated"
  },
  {
    "id": "spacex",
    "name": "SpaceX",
    "domains": [
      "spacex.com"
    ],
    "tags": [
      "aerospace",
      "technology"
    ],
    "h": 58,
    "u": 30,
    "m": 35,
    "a": 35,
    "n": 22,
    "notes": "Deep engineering craft. Grueling work culture. Worker burnout reports.",
    "confidence": "estimated"
  },
  {
    "id": "lockheed",
    "name": "Lockheed Martin",
    "domains": [
      "lockheedmartin.com"
    ],
    "tags": [
      "defense",
      "aerospace"
    ],
    "h": 52,
    "u": 38,
    "m": 25,
    "a": 32,
    "n": 28,
    "notes": "Skilled human engineering. Defense ethics debates.",
    "confidence": "estimated"
  },
  {
    "id": "3m",
    "name": "3M",
    "domains": [
      "3m.com"
    ],
    "tags": [
      "manufacturing",
      "industrial"
    ],
    "h": 55,
    "u": 48,
    "m": 28,
    "a": 22,
    "n": 30,
    "notes": "Innovation culture. PFAS contamination scandal.",
    "confidence": "estimated"
  },
  {
    "id": "procter",
    "name": "Procter & Gamble",
    "domains": [
      "pg.com"
    ],
    "tags": [
      "consumer goods"
    ],
    "h": 42,
    "u": 40,
    "m": 38,
    "a": 38,
    "n": 35,
    "notes": "Large consumer goods. Moderate automation. Some sustainability targets.",
    "confidence": "estimated"
  },
  {
    "id": "unilever",
    "name": "Unilever",
    "domains": [
      "unilever.com"
    ],
    "tags": [
      "consumer goods"
    ],
    "h": 45,
    "u": 42,
    "m": 45,
    "a": 48,
    "n": 42,
    "notes": "Sustainable Living Plan. B Corp subsidiaries.",
    "confidence": "estimated"
  },
  {
    "id": "toms",
    "name": "TOMS",
    "domains": [
      "toms.com"
    ],
    "tags": [
      "apparel",
      "footwear",
      "social enterprise"
    ],
    "h": 60,
    "u": 65,
    "m": 68,
    "a": 52,
    "n": 58,
    "notes": "Impact fund model. B Corp.",
    "confidence": "estimated"
  },
  {
    "id": "warby_parker",
    "name": "Warby Parker",
    "domains": [
      "warbyparker.com"
    ],
    "tags": [
      "retail",
      "eyewear",
      "social enterprise"
    ],
    "h": 58,
    "u": 60,
    "m": 62,
    "a": 48,
    "n": 58,
    "notes": "Buy a Pair Give a Pair. B Corp.",
    "confidence": "estimated"
  },
  {
    "id": "bombas",
    "name": "Bombas",
    "domains": [
      "bombas.com"
    ],
    "tags": [
      "apparel",
      "social enterprise"
    ],
    "h": 62,
    "u": 68,
    "m": 72,
    "a": 52,
    "n": 62,
    "notes": "One purchased = one donated. B Corp. Human customer service.",
    "confidence": "estimated"
  },
  {
    "id": "cotopaxi",
    "name": "Cotopaxi",
    "domains": [
      "cotopaxi.com"
    ],
    "tags": [
      "outdoor",
      "gear",
      "social enterprise"
    ],
    "h": 65,
    "u": 68,
    "m": 75,
    "a": 70,
    "n": 72,
    "notes": "B Corp. Gear for Good. Repurposed materials. 1% for the Planet.",
    "confidence": "estimated"
  },
  {
    "id": "impossible",
    "name": "Impossible Foods",
    "domains": [
      "impossiblefoods.com"
    ],
    "tags": [
      "food",
      "alternative protein"
    ],
    "h": 55,
    "u": 50,
    "m": 58,
    "a": 72,
    "n": 55,
    "notes": "Mission-driven alternative to meat. Significant environmental benefit.",
    "confidence": "estimated"
  },
  {
    "id": "beyond_meat",
    "name": "Beyond Meat",
    "domains": [
      "beyondmeat.com"
    ],
    "tags": [
      "food",
      "alternative protein"
    ],
    "h": 52,
    "u": 48,
    "m": 55,
    "a": 70,
    "n": 52,
    "notes": "Plant-based mission. Environmental benefit. Ultra-processed labeling debate.",
    "confidence": "estimated"
  },
  {
    "id": "cisco",
    "name": "Cisco Systems",
    "domains": [
      "cisco.com"
    ],
    "tags": [
      "technology",
      "networking"
    ],
    "h": 48,
    "u": 42,
    "m": 45,
    "a": 40,
    "n": 42,
    "notes": "Networking infrastructure. Large human workforce. Growing AI integration. Decent sustainability reporting.",
    "confidence": "estimated"
  },
  {
    "id": "hp",
    "name": "HP Inc.",
    "domains": [
      "hp.com"
    ],
    "tags": [
      "technology",
      "hardware"
    ],
    "h": 45,
    "u": 40,
    "m": 42,
    "a": 42,
    "n": 40,
    "notes": "PC and printer manufacturer. Some sustainability programs. Planned obsolescence in ink cartridges.",
    "confidence": "estimated"
  },
  {
    "id": "dell",
    "name": "Dell Technologies",
    "domains": [
      "dell.com"
    ],
    "tags": [
      "technology",
      "hardware"
    ],
    "h": 45,
    "u": 40,
    "m": 40,
    "a": 38,
    "n": 38,
    "notes": "Direct model. Recycling programs. Growing AI server business. Mixed worker reviews.",
    "confidence": "estimated"
  },
  {
    "id": "twitter",
    "name": "X / Twitter",
    "domains": [
      "x.com",
      "twitter.com"
    ],
    "tags": [
      "technology",
      "social media"
    ],
    "h": 25,
    "u": 15,
    "m": 12,
    "a": 30,
    "n": 15,
    "notes": "Mass layoffs. Reduced content moderation. Bot proliferation. Transparency gutted.",
    "confidence": "estimated"
  },
  {
    "id": "lyft",
    "name": "Lyft",
    "domains": [
      "lyft.com"
    ],
    "tags": [
      "technology",
      "transportation",
      "gig economy"
    ],
    "h": 32,
    "u": 35,
    "m": 30,
    "a": 35,
    "n": 35,
    "notes": "Similar gig model to Uber. Some driver support improvements. Pursuing autonomous.",
    "confidence": "estimated"
  },
  {
    "id": "doordash",
    "name": "DoorDash",
    "domains": [
      "doordash.com"
    ],
    "tags": [
      "technology",
      "food delivery",
      "gig economy"
    ],
    "h": 28,
    "u": 25,
    "m": 28,
    "a": 30,
    "n": 28,
    "notes": "Gig delivery model. Driver pay controversies. Restaurant commission debates.",
    "confidence": "estimated"
  },
  {
    "id": "instacart",
    "name": "Instacart",
    "domains": [
      "instacart.com"
    ],
    "tags": [
      "technology",
      "grocery",
      "gig economy"
    ],
    "h": 30,
    "u": 28,
    "m": 30,
    "a": 32,
    "n": 30,
    "notes": "Gig shopper model. IPO raised worker pay questions. Growing automation.",
    "confidence": "estimated"
  },
  {
    "id": "robinhood",
    "name": "Robinhood",
    "domains": [
      "robinhood.com"
    ],
    "tags": [
      "finance",
      "fintech"
    ],
    "h": 32,
    "u": 25,
    "m": 18,
    "a": 35,
    "n": 28,
    "notes": "Gamification of investing. GameStop controversy. Payment for order flow ethics.",
    "confidence": "estimated"
  },
  {
    "id": "coinbase",
    "name": "Coinbase",
    "domains": [
      "coinbase.com"
    ],
    "tags": [
      "finance",
      "crypto",
      "technology"
    ],
    "h": 40,
    "u": 35,
    "m": 32,
    "a": 30,
    "n": 38,
    "notes": "Crypto exchange. Some transparency on operations. Energy concerns from crypto. Mass layoffs.",
    "confidence": "estimated"
  },
  {
    "id": "block_sq",
    "name": "Block (Square)",
    "domains": [
      "block.xyz",
      "squareup.com",
      "cash.app"
    ],
    "tags": [
      "finance",
      "fintech",
      "payments"
    ],
    "h": 45,
    "u": 42,
    "m": 40,
    "a": 35,
    "n": 40,
    "notes": "Empowers small businesses. Cash App financial inclusion. Bitcoin mining energy concerns.",
    "confidence": "estimated"
  },
  {
    "id": "tyson",
    "name": "Tyson Foods",
    "domains": [
      "tysonfoods.com"
    ],
    "tags": [
      "food",
      "meat",
      "agriculture"
    ],
    "h": 35,
    "u": 25,
    "m": 20,
    "a": 18,
    "n": 22,
    "notes": "Worker safety issues. Environmental pollution. Animal welfare concerns. Large human workforce.",
    "confidence": "estimated"
  },
  {
    "id": "kraft_heinz",
    "name": "Kraft Heinz",
    "domains": [
      "kraftheinzcompany.com"
    ],
    "tags": [
      "food",
      "consumer goods"
    ],
    "h": 38,
    "u": 35,
    "m": 32,
    "a": 30,
    "n": 32,
    "notes": "Large processed food company. Cost-cutting culture. Some sustainability programs.",
    "confidence": "estimated"
  },
  {
    "id": "general_mills",
    "name": "General Mills",
    "domains": [
      "generalmills.com"
    ],
    "tags": [
      "food",
      "consumer goods"
    ],
    "h": 42,
    "u": 40,
    "m": 42,
    "a": 42,
    "n": 40,
    "notes": "Regenerative agriculture investment. Some organic brands. Moderate sustainability.",
    "confidence": "estimated"
  },
  {
    "id": "kellogg",
    "name": "Kellanova / WK Kellogg",
    "domains": [
      "kellanova.com"
    ],
    "tags": [
      "food",
      "consumer goods"
    ],
    "h": 40,
    "u": 38,
    "m": 38,
    "a": 38,
    "n": 35,
    "notes": "Worker strike history. Split into two companies. Some sustainability programs.",
    "confidence": "estimated"
  },
  {
    "id": "annie_homegrown",
    "name": "Annie's Homegrown",
    "domains": [
      "annies.com"
    ],
    "tags": [
      "food",
      "organic"
    ],
    "h": 62,
    "u": 58,
    "m": 65,
    "a": 68,
    "n": 60,
    "notes": "Organic focus. General Mills owned. Bunny mascot. Regenerative farming support.",
    "confidence": "estimated"
  },
  {
    "id": "blue_bottle",
    "name": "Blue Bottle Coffee",
    "domains": [
      "bluebottlecoffee.com"
    ],
    "tags": [
      "food",
      "coffee"
    ],
    "h": 65,
    "u": 62,
    "m": 58,
    "a": 55,
    "n": 55,
    "notes": "Craft coffee focus. Human baristas. Nestle-owned. Sustainability commitments.",
    "confidence": "estimated"
  },
  {
    "id": "oatly",
    "name": "Oatly",
    "domains": [
      "oatly.com"
    ],
    "tags": [
      "food",
      "beverage",
      "alternative dairy"
    ],
    "h": 55,
    "u": 52,
    "m": 58,
    "a": 68,
    "n": 58,
    "notes": "Plant-based mission. Sustainability marketing. Blackstone investment controversy.",
    "confidence": "estimated"
  },
  {
    "id": "wayfair",
    "name": "Wayfair",
    "domains": [
      "wayfair.com"
    ],
    "tags": [
      "retail",
      "furniture",
      "e-commerce"
    ],
    "h": 32,
    "u": 30,
    "m": 28,
    "a": 28,
    "n": 25,
    "notes": "Algorithm-driven retail. Mass layoffs. Drop-shipping model reduces human craft connection.",
    "confidence": "estimated"
  },
  {
    "id": "chewy",
    "name": "Chewy",
    "domains": [
      "chewy.com"
    ],
    "tags": [
      "retail",
      "pets",
      "e-commerce"
    ],
    "h": 55,
    "u": 65,
    "m": 55,
    "a": 38,
    "n": 45,
    "notes": "Known for exceptional human customer service. Handwritten cards. Pet sympathy gestures.",
    "confidence": "estimated"
  },
  {
    "id": "zappos",
    "name": "Zappos",
    "domains": [
      "zappos.com"
    ],
    "tags": [
      "retail",
      "footwear",
      "e-commerce"
    ],
    "h": 58,
    "u": 68,
    "m": 55,
    "a": 38,
    "n": 48,
    "notes": "Legendary customer service culture. Amazon-owned. Holacracy experiment.",
    "confidence": "estimated"
  },
  {
    "id": "ebay",
    "name": "eBay",
    "domains": [
      "ebay.com"
    ],
    "tags": [
      "retail",
      "marketplace",
      "e-commerce"
    ],
    "h": 48,
    "u": 40,
    "m": 42,
    "a": 35,
    "n": 42,
    "notes": "Enables individual sellers. Growing automation. Some sustainability programs.",
    "confidence": "estimated"
  },
  {
    "id": "kaiser",
    "name": "Kaiser Permanente",
    "domains": [
      "kaiserpermanente.org"
    ],
    "tags": [
      "healthcare",
      "insurance"
    ],
    "h": 55,
    "u": 55,
    "m": 52,
    "a": 42,
    "n": 48,
    "notes": "Integrated care model. Large physician workforce. Mental health access improvements.",
    "confidence": "estimated"
  },
  {
    "id": "mayo_clinic",
    "name": "Mayo Clinic",
    "domains": [
      "mayoclinic.org"
    ],
    "tags": [
      "healthcare",
      "nonprofit"
    ],
    "h": 78,
    "u": 75,
    "m": 72,
    "a": 45,
    "n": 65,
    "notes": "Patient-first nonprofit model. Leading medical research. Human-centered care. Deep expertise.",
    "confidence": "estimated"
  },
  {
    "id": "one_medical",
    "name": "One Medical (Amazon)",
    "domains": [
      "onemedical.com"
    ],
    "tags": [
      "healthcare",
      "technology"
    ],
    "h": 48,
    "u": 50,
    "m": 40,
    "a": 35,
    "n": 38,
    "notes": "Tech-enabled primary care. Human doctors. Amazon acquisition raises data concerns.",
    "confidence": "estimated"
  },
  {
    "id": "yeti",
    "name": "YETI",
    "domains": [
      "yeti.com"
    ],
    "tags": [
      "outdoor",
      "housewares"
    ],
    "h": 55,
    "u": 50,
    "m": 52,
    "a": 48,
    "n": 45,
    "notes": "Durable product design. Premium quality focus. Moderate supply chain transparency.",
    "confidence": "estimated"
  },
  {
    "id": "hydroflask",
    "name": "Hydro Flask",
    "domains": [
      "hydroflask.com"
    ],
    "tags": [
      "housewares",
      "outdoor"
    ],
    "h": 55,
    "u": 50,
    "m": 55,
    "a": 58,
    "n": 50,
    "notes": "Reusable bottle advocate. Parks for All program. Durable design.",
    "confidence": "estimated"
  },
  {
    "id": "leatherman",
    "name": "Leatherman",
    "domains": [
      "leatherman.com"
    ],
    "tags": [
      "tools",
      "manufacturing"
    ],
    "h": 78,
    "u": 65,
    "m": 72,
    "a": 55,
    "n": 62,
    "notes": "US-manufactured multi-tools. 25-year warranty. Skilled craftspeople. Portland heritage.",
    "confidence": "estimated"
  },
  {
    "id": "filson",
    "name": "Filson",
    "domains": [
      "filson.com"
    ],
    "tags": [
      "apparel",
      "outdoor",
      "heritage"
    ],
    "h": 80,
    "u": 70,
    "m": 72,
    "a": 58,
    "n": 65,
    "notes": "US-manufactured since 1897. Lifetime guarantee. Heritage craft. Durable goods philosophy.",
    "confidence": "estimated"
  },
  {
    "id": "red_wing",
    "name": "Red Wing Shoes",
    "domains": [
      "redwingshoes.com"
    ],
    "tags": [
      "footwear",
      "manufacturing"
    ],
    "h": 82,
    "u": 72,
    "m": 75,
    "a": 55,
    "n": 68,
    "notes": "US-manufactured work boots since 1905. Resoling and repair program. Multi-generational craft.",
    "confidence": "estimated"
  },
  {
    "id": "vitamix",
    "name": "Vitamix",
    "domains": [
      "vitamix.com"
    ],
    "tags": [
      "housewares",
      "manufacturing"
    ],
    "h": 75,
    "u": 68,
    "m": 72,
    "a": 55,
    "n": 62,
    "notes": "US-manufactured since 1921. Family-owned. 10-year warranty. Quality over planned obsolescence.",
    "confidence": "estimated"
  },
  {
    "id": "mjolk",
    "name": "Le Creuset",
    "domains": [
      "lecreuset.com"
    ],
    "tags": [
      "housewares",
      "cookware"
    ],
    "h": 78,
    "u": 65,
    "m": 68,
    "a": 55,
    "n": 58,
    "notes": "French artisan cookware since 1925. Hand-cast and hand-inspected. Lifetime warranty.",
    "confidence": "estimated"
  },
  {
    "id": "birkenstocks",
    "name": "Birkenstock",
    "domains": [
      "birkenstock.com"
    ],
    "tags": [
      "footwear"
    ],
    "h": 72,
    "u": 60,
    "m": 62,
    "a": 58,
    "n": 55,
    "notes": "German-manufactured since 1774. Cork and natural materials. Durable design. Heritage craft.",
    "confidence": "estimated"
  },
  {
    "id": "grove_collab",
    "name": "Grove Collaborative",
    "domains": [
      "grove.co"
    ],
    "tags": [
      "household",
      "sustainable",
      "e-commerce"
    ],
    "h": 58,
    "u": 58,
    "m": 65,
    "a": 72,
    "n": 62,
    "notes": "B Corp. Plastic-neutral. Sustainable household products. Tree planting program.",
    "confidence": "estimated"
  },
  {
    "id": "thrive_market",
    "name": "Thrive Market",
    "domains": [
      "thrivemarket.com"
    ],
    "tags": [
      "retail",
      "grocery",
      "sustainable"
    ],
    "h": 55,
    "u": 60,
    "m": 62,
    "a": 58,
    "n": 55,
    "notes": "B Corp. Membership model. Free memberships for low-income families. Organic and sustainable.",
    "confidence": "estimated"
  },
  {
    "id": "pact",
    "name": "Pact",
    "domains": [
      "wearpact.com"
    ],
    "tags": [
      "apparel",
      "organic",
      "sustainable"
    ],
    "h": 60,
    "u": 55,
    "m": 68,
    "a": 70,
    "n": 65,
    "notes": "Organic cotton. Fair Trade certified. Carbon-neutral shipping. Transparent pricing.",
    "confidence": "estimated"
  },
  {
    "id": "pela_case",
    "name": "Pela Case",
    "domains": [
      "pelacase.com"
    ],
    "tags": [
      "technology",
      "accessories",
      "sustainable"
    ],
    "h": 58,
    "u": 55,
    "m": 65,
    "a": 78,
    "n": 62,
    "notes": "Compostable phone cases. B Corp. Climate Neutral. Plastic-free mission.",
    "confidence": "estimated"
  },
  {
    "id": "who_gives_crap",
    "name": "Who Gives A Crap",
    "domains": [
      "whogivesacrap.org"
    ],
    "tags": [
      "household",
      "sustainable",
      "social enterprise"
    ],
    "h": 68,
    "u": 72,
    "m": 78,
    "a": 75,
    "n": 75,
    "notes": "B Corp. 50% profits to sanitation charities. Sustainable materials. Transparent impact.",
    "confidence": "estimated"
  },
  {
    "id": "reuters",
    "name": "Reuters / Thomson Reuters",
    "domains": [
      "reuters.com"
    ],
    "tags": [
      "media",
      "journalism",
      "data"
    ],
    "h": 68,
    "u": 52,
    "m": 58,
    "a": 38,
    "n": 62,
    "notes": "Wire service journalism. Human reporters worldwide. Growing AI tools. Trust principles.",
    "confidence": "estimated"
  },
  {
    "id": "propublica",
    "name": "ProPublica",
    "domains": [
      "propublica.org"
    ],
    "tags": [
      "media",
      "journalism",
      "nonprofit"
    ],
    "h": 82,
    "u": 70,
    "m": 85,
    "a": 42,
    "n": 90,
    "notes": "Nonprofit investigative journalism. Public interest mission. High transparency. Donor-funded.",
    "confidence": "estimated"
  },
  {
    "id": "ap_news",
    "name": "Associated Press",
    "domains": [
      "apnews.com"
    ],
    "tags": [
      "media",
      "journalism"
    ],
    "h": 72,
    "u": 55,
    "m": 65,
    "a": 38,
    "n": 68,
    "notes": "Cooperative news organization. Global human reporting network. Some AI adoption in sports/finance.",
    "confidence": "estimated"
  },
  {
    "id": "wikipedia",
    "name": "Wikimedia Foundation",
    "domains": [
      "wikipedia.org",
      "wikimedia.org"
    ],
    "tags": [
      "education",
      "nonprofit",
      "technology"
    ],
    "h": 80,
    "u": 72,
    "m": 85,
    "a": 42,
    "n": 92,
    "notes": "Volunteer-created knowledge. Nonprofit. No ads. Maximum transparency. Human editors.",
    "confidence": "estimated"
  },
  {
    "id": "archive_org",
    "name": "Internet Archive",
    "domains": [
      "archive.org"
    ],
    "tags": [
      "technology",
      "nonprofit",
      "education"
    ],
    "h": 78,
    "u": 72,
    "m": 82,
    "a": 40,
    "n": 88,
    "notes": "Digital library for all. Nonprofit. Wayback Machine. Copyright legal battles. Open access mission.",
    "confidence": "estimated"
  },
  {
    "id": "reformation",
    "name": "Reformation",
    "domains": [
      "thereformation.com"
    ],
    "tags": [
      "apparel",
      "sustainable",
      "fashion"
    ],
    "h": 55,
    "u": 50,
    "m": 58,
    "a": 72,
    "n": 65,
    "notes": "Sustainable fashion. Carbon-neutral. RefScale environmental tracking.",
    "confidence": "estimated"
  },
  {
    "id": "wegmans",
    "name": "Wegmans",
    "domains": [
      "wegmans.com"
    ],
    "tags": [
      "retail",
      "grocery"
    ],
    "h": 72,
    "u": 75,
    "m": 70,
    "a": 50,
    "n": 52,
    "notes": "Consistently rated best employer. Employee-first culture. Scholarship programs.",
    "confidence": "estimated"
  },
  {
    "id": "publix",
    "name": "Publix",
    "domains": [
      "publix.com"
    ],
    "tags": [
      "retail",
      "grocery"
    ],
    "h": 68,
    "u": 70,
    "m": 62,
    "a": 45,
    "n": 48,
    "notes": "Employee-owned (ESOP). Strong service culture. Community involvement.",
    "confidence": "estimated"
  },
  {
    "id": "aldi",
    "name": "ALDI",
    "domains": [
      "aldi.us",
      "aldi.com"
    ],
    "tags": [
      "retail",
      "grocery"
    ],
    "h": 50,
    "u": 45,
    "m": 48,
    "a": 45,
    "n": 38,
    "notes": "Efficiency model. Above-minimum wages. Growing organic selection.",
    "confidence": "estimated"
  },
  {
    "id": "biogen",
    "name": "Biogen",
    "domains": [
      "biogen.com"
    ],
    "tags": [
      "healthcare",
      "pharmaceutical",
      "biotech"
    ],
    "h": 58,
    "u": 50,
    "m": 45,
    "a": 42,
    "n": 42,
    "notes": "Human-intensive R&D. Alzheimer drug controversies. Carbon neutral since 2014.",
    "confidence": "estimated"
  },
  {
    "id": "moderna",
    "name": "Moderna",
    "domains": [
      "moderna.com"
    ],
    "tags": [
      "healthcare",
      "pharmaceutical",
      "biotech"
    ],
    "h": 55,
    "u": 45,
    "m": 42,
    "a": 38,
    "n": 40,
    "notes": "mRNA platform. COVID vaccine. Growing AI in drug discovery.",
    "confidence": "estimated"
  },
  {
    "id": "pat_provisions",
    "name": "Patagonia Provisions",
    "domains": [
      "patagoniaprovisions.com"
    ],
    "tags": [
      "food",
      "sustainable"
    ],
    "h": 85,
    "u": 80,
    "m": 88,
    "a": 90,
    "n": 85,
    "notes": "Patagonia's food arm. Regenerative organic. Supply chain transparency.",
    "confidence": "estimated"
  },
  {
    "id": "leatherman",
    "name": "Leatherman",
    "domains": [
      "leatherman.com"
    ],
    "tags": [
      "tools",
      "manufacturing"
    ],
    "h": 78,
    "u": 65,
    "m": 72,
    "a": 55,
    "n": 62,
    "notes": "US-manufactured multi-tools. 25-year warranty. Skilled craftspeople.",
    "confidence": "estimated"
  },
  {
    "id": "filson",
    "name": "Filson",
    "domains": [
      "filson.com"
    ],
    "tags": [
      "apparel",
      "outdoor",
      "heritage"
    ],
    "h": 80,
    "u": 70,
    "m": 72,
    "a": 58,
    "n": 65,
    "notes": "US-manufactured since 1897. Lifetime guarantee. Heritage craft.",
    "confidence": "estimated"
  },
  {
    "id": "red_wing",
    "name": "Red Wing Shoes",
    "domains": [
      "redwingshoes.com"
    ],
    "tags": [
      "footwear",
      "manufacturing"
    ],
    "h": 82,
    "u": 72,
    "m": 75,
    "a": 55,
    "n": 68,
    "notes": "US-manufactured work boots since 1905. Resoling program. Multi-generational craft.",
    "confidence": "estimated"
  },
  {
    "id": "vitamix",
    "name": "Vitamix",
    "domains": [
      "vitamix.com"
    ],
    "tags": [
      "housewares",
      "manufacturing"
    ],
    "h": 75,
    "u": 68,
    "m": 72,
    "a": 55,
    "n": 62,
    "notes": "US-manufactured since 1921. Family-owned. 10-year warranty.",
    "confidence": "estimated"
  },
  {
    "id": "le_creuset",
    "name": "Le Creuset",
    "domains": [
      "lecreuset.com"
    ],
    "tags": [
      "housewares",
      "cookware"
    ],
    "h": 78,
    "u": 65,
    "m": 68,
    "a": 55,
    "n": 58,
    "notes": "French artisan cookware since 1925. Hand-cast and hand-inspected.",
    "confidence": "estimated"
  },
  {
    "id": "birkenstock",
    "name": "Birkenstock",
    "domains": [
      "birkenstock.com"
    ],
    "tags": [
      "footwear",
      "manufacturing"
    ],
    "h": 72,
    "u": 60,
    "m": 62,
    "a": 58,
    "n": 55,
    "notes": "German-manufactured since 1774. Cork and natural materials. Heritage craft.",
    "confidence": "estimated"
  }
];

// Statistics
if (typeof console !== 'undefined') {
  console.log('[HUMAN Score] Seed database: ' + SEED_COMPANIES.length + ' companies loaded');
}

if (typeof window !== 'undefined') { window.SEED_COMPANIES = SEED_COMPANIES; }
if (typeof module !== 'undefined') { module.exports = { SEED_COMPANIES }; }
