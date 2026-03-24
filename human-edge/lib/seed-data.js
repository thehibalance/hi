/**
 * HUMAN Score Seed Database v0.2.0
 * 206 companies across 120 categories
 * 
 * All scores are ESTIMATED based on publicly available information.
 * NO AI WAS USED TO GENERATE THESE SCORES.
 * 
 * Methodology: HUMAN Framework v1.0
 * Governed by: The HI Balance
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
    "notes": "High craft in hardware design (H), but aggressive AI adoption in services. Right-to-repair improvements after years of resistance. Industry-leading renewable energy and privacy stance (A, N). Supply chain labor concerns in China (Foxconn, Pegatron) weaken M. Low algorithmic harm \u2014 no engagement-driven feed algorithms.",
    "confidence": "estimated",
    "algorithmic_harm_score": 18,
    "subsidiaries": [
      "Beats Electronics",
      "Shazam",
      "Claris"
    ],
    "primary_contractors": [
      "Foxconn (manufacturing)",
      "Pegatron (assembly)",
      "TSMC (chips)"
    ]
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
    "notes": "YouTube recommendation engine linked to radicalization pipelines and children's content concerns. Search ad model incentivizes engagement over accuracy. Strong AI research but displacing human decision-making at scale. DeepMind pursuing AGI with limited public safety governance. 12,000+ layoffs (2023) while increasing AI capex. Waymo represents augmentation \u2014 but core ad business is optimization-at-all-costs. CDP disclosure strong (A).",
    "confidence": "estimated",
    "algorithmic_harm_score": 52,
    "subsidiaries": [
      "YouTube",
      "DeepMind",
      "Waymo",
      "Verily",
      "Google Cloud",
      "Waze",
      "Fitbit"
    ],
    "primary_contractors": [
      "Cognizant (content moderation)",
      "Accenture (ad review)"
    ]
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
    "notes": "Copilot branding across all products positions AI as augmentation \u2014 but 10,000+ layoffs concurrent with $13B OpenAI investment contradicts narrative. LinkedIn algorithm increasingly engagement-driven. GitHub Copilot raises open-source attribution ethics questions. Strong enterprise human accountability chains. Activision acquisition brings loot box / microtransaction concerns (M). Climate pledges strong but data center water usage growing (A).",
    "confidence": "estimated",
    "algorithmic_harm_score": 22,
    "subsidiaries": [
      "LinkedIn",
      "GitHub",
      "Activision Blizzard",
      "Nuance Communications",
      "Minecraft (Mojang)"
    ],
    "primary_contractors": [
      "Accenture (cloud services)",
      "Infosys (support)"
    ]
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
    "notes": "Dark patterns in Prime cancellation (documented by FTC). Warehouse worker conditions and surveillance algorithms under regulatory scrutiny. Alexa data collection concerns. Ring doorbell policing partnerships raise civil liberties issues. DSP contractor structure distances Amazon from delivery worker conditions. AWS dominance creates infrastructure dependency. Whole Foods acquisition maintained some human-centric operations. Mechanical Turk treats human intelligence as commodity.",
    "confidence": "estimated",
    "algorithmic_harm_score": 45,
    "subsidiaries": [
      "AWS",
      "Whole Foods",
      "Ring",
      "Twitch",
      "MGM",
      "One Medical",
      "Kuiper"
    ],
    "primary_contractors": [
      "Delivery Service Partners (DSPs)",
      "Flex drivers",
      "Mechanical Turk workers"
    ]
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
    "notes": "Content moderation outsourced to contractors with documented PTSD and poor working conditions. Instagram internal research (leaked 2021) showed platform worsens teen body image and mental health. Engagement algorithms amplify outrage, misinformation, and polarization \u2014 repeatedly documented by whistleblowers. 21,000+ layoffs (2022-2023) while investing $15B+ in Reality Labs. Customer support fully automated. WhatsApp end-to-end encryption is a positive transparency signal, but parent company data practices undermine trust.",
    "confidence": "estimated",
    "algorithmic_harm_score": 72,
    "subsidiaries": [
      "Instagram",
      "WhatsApp",
      "Reality Labs",
      "Threads"
    ],
    "primary_contractors": [
      "Accenture (content moderation)",
      "Cognizant (content moderation)",
      "Sama (AI training data)"
    ]
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
    "notes": "Dominant AI chip supplier \u2014 enables AI displacement across all industries but doesn't directly operate displacement algorithms. High craft in chip design (H). Strong employee satisfaction. Environmental cost from manufacturing and customer data center energy use partially attributed (A). Low direct algorithmic harm \u2014 hardware company, not platform.",
    "confidence": "estimated",
    "algorithmic_harm_score": 8,
    "subsidiaries": [
      "Mellanox Technologies",
      "Arm (attempted, failed)"
    ]
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
    "notes": "Autopilot/FSD safety record under NHTSA investigation. CEO social media behavior impacts M dimension. Factory worker safety incidents documented by OSHA. Strong renewable energy mission (A) offset by lithium mining supply chain. Optimus robot program explicitly designed to replace human labor. High automation in manufacturing reduces H. Direct sales model maintains some human touchpoints.",
    "confidence": "estimated",
    "algorithmic_harm_score": 28,
    "subsidiaries": [
      "Tesla Energy",
      "Tesla Insurance",
      "SolarCity"
    ]
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
    "notes": "Recommendation algorithm drives binge behavior \u2014 autoplay, skip intro, continuous viewing designed to maximize watch time. Content algorithm increasingly shapes what gets produced (creative agency concern). Low workforce \u2014 high revenue per employee ratio suggests heavy automation. Strong creative investment in human storytelling offset by algorithmic content selection. No ad-driven engagement \u2014 subscription model is cleaner than ad-supported platforms.",
    "confidence": "estimated",
    "algorithmic_harm_score": 32
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
    "notes": "Enterprise software \u2014 low direct consumer algorithmic harm. Cerner acquisition positions Oracle in healthcare data with significant privacy implications. Aggressive cloud migration displacing on-premise IT workers. CEO compensation among highest in industry (M). Low transparency on AI integration in enterprise products.",
    "confidence": "estimated",
    "algorithmic_harm_score": 12,
    "subsidiaries": [
      "Cerner (healthcare IT)",
      "NetSuite"
    ]
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
    "notes": "WatsonX positioned as augmentation platform \u2014 'AI for business, not replacing business.' Publicly stated AI ethics principles. But quietly discontinued Watson Health after overpromising. Red Hat acquisition maintained open-source ethos. Historical workforce reductions masked as 'rebalancing.' Pioneer in AI ethics research but commercialization sometimes contradicts principles. Weather Company data collection raises privacy questions.",
    "confidence": "estimated",
    "algorithmic_harm_score": 15,
    "subsidiaries": [
      "Red Hat",
      "The Weather Company"
    ]
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
    "notes": "Agentforce/Einstein AI positioned as human augmentation \u2014 copilot model. Public pledge that AI won't replace Salesforce employees (unverified long-term). Strong philanthropic model (1-1-1). But 8,000+ layoffs (2023) while launching AI products contradicts augmentation narrative. Slack acquisition maintained independent culture initially but integration increasing. High employee satisfaction historically but declining post-layoffs.",
    "confidence": "estimated",
    "algorithmic_harm_score": 14,
    "subsidiaries": [
      "Slack",
      "Tableau",
      "MuleSoft",
      "Heroku"
    ]
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
    "notes": "Firefly AI trained on licensed/owned content \u2014 ethical AI training model compared to competitors. Creative tools augment human creators rather than replacing them. But subscription pricing and dark pattern cancellation flows documented. Figma acquisition blocked by regulators (competition concerns). Strong creative community through Behance. Stock photo business threatened by own AI tools \u2014 tension between creator ecosystem and AI efficiency.",
    "confidence": "estimated",
    "algorithmic_harm_score": 10,
    "subsidiaries": [
      "Figma (attempted, blocked)",
      "Frame.io",
      "Behance"
    ]
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
    "notes": "Recommendation algorithm drives discovery but also creates filter bubbles. Playlist algorithm increasingly determines which artists get heard \u2014 shifts power from human curators to machines. Low artist payment per stream (M). AI DJ feature replaces human radio DJs. Podcast push includes AI-generated content. Daniel Ek's comments about artists needing to produce more frequently reflect optimization-over-craft mindset.",
    "confidence": "estimated",
    "algorithmic_harm_score": 30
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
    "notes": "Surge pricing algorithm exploits high-demand situations. Driver classification as contractors distances company from labor protections. Algorithmic management of drivers \u2014 deactivation without human review, opaque rating systems. Uber Files leak revealed lobbying and regulatory evasion. Uber Eats dark kitchen model reduces restaurant human employment. Upfront pricing algorithm lacks transparency.",
    "confidence": "estimated",
    "algorithmic_harm_score": 40,
    "subsidiaries": [
      "Uber Eats",
      "Postmates",
      "Drizly"
    ]
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
    "notes": "Pricing algorithm can manipulate host expectations. Platform displaces hotel workers (structural). But maintains human-to-human connection model at its core. Anti-discrimination policies improved after documented bias. Community impact concerns in housing markets. Relatively low algorithmic manipulation compared to social media platforms.",
    "confidence": "estimated",
    "algorithmic_harm_score": 20
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
    "notes": "Streaks feature gamifies daily engagement \u2014 designed for addiction, primarily targeting minors. Spotlight algorithm mimics TikTok engagement patterns. My AI chatbot for teens raises safety concerns. Snap Map location sharing has stalking implications. But ephemeral messaging model has some privacy benefits. AR features augment rather than replace human creativity.",
    "confidence": "estimated",
    "algorithmic_harm_score": 45
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
    "notes": "For You Page algorithm is the most potent engagement engine ever built \u2014 optimizes for watch time with no human editorial judgment. Documented negative effects on teen attention spans and mental health. Data governance concerns due to ByteDance/China relationship. Content moderation struggles with scale. Creator economy model pays creators but extracts disproportionate value. Algorithm determines cultural relevance \u2014 unprecedented power for a non-human system.",
    "confidence": "estimated",
    "algorithmic_harm_score": 68,
    "subsidiaries": [
      "CapCut",
      "Lemon8"
    ],
    "primary_contractors": [
      "ByteDance (parent, China-based)"
    ]
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
    "notes": "Historically lower algorithmic manipulation than other social platforms \u2014 intent-based rather than engagement-based. Body image concerns in early years addressed with policy changes. Shopping integration is transparent. Banned weight loss ads proactively. Workplace culture issues (discrimination lawsuit settled). Algorithm serves search intent rather than manufacturing engagement.",
    "confidence": "estimated",
    "algorithmic_harm_score": 22
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
    "notes": "Empowers small business owners \u2014 fundamental human-empowerment model. AI tools (Sidekick, Magic) positioned as merchant augmentation. But app ecosystem creates dependency. Laid off 20% of workforce (2023) citing AI as partial reason \u2014 contradicts augmentation messaging. Low direct algorithmic harm \u2014 facilitates commerce rather than manipulating behavior.",
    "confidence": "estimated",
    "algorithmic_harm_score": 8
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
    "notes": "Surveillance algorithms used by government agencies and law enforcement. Predictive policing contracts raise civil liberties concerns. ICE contract facilitated immigration enforcement. Military applications (Project Maven successor work). Alex Karp publicly defends government work as ethical obligation. High craft in engineering but applied to monitoring human populations. Low transparency on specific deployments.",
    "confidence": "estimated",
    "algorithmic_harm_score": 55
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
    "notes": "Building the most powerful AI systems in history \u2014 direct displacement potential across knowledge work. Rapid deployment pace concerns safety researchers (multiple departures). Capped-profit structure is novel but governance turbulence (board crisis 2023) raises accountability questions. GPT models increasingly capable of replacing human writers, coders, analysts. Some augmentation positioning (Copilot via Microsoft) but foundational technology enables displacement at scale. Charter claims 'broadly benefit humanity' but commercial incentives accelerating.",
    "confidence": "estimated",
    "algorithmic_harm_score": 28
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
    "notes": "Constitutional AI approach represents genuine attempt at safety-first development. Responsible scaling policy is industry-leading. But still building systems that displace human knowledge work. B Corp certified (rare for AI company). Higher transparency than competitors on safety research. Slower deployment pace than OpenAI reflects caution. Claude positioned as assistant/augmentation rather than replacement \u2014 but capability growth may outpace positioning.",
    "confidence": "estimated",
    "algorithmic_harm_score": 15
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
    "notes": "Largest private employer in the US \u2014 massive H dimension weight. Increasing self-checkout and automation in stores. Wages historically low but improving. Supply chain labor practices under scrutiny globally. Flipkart/India operations expand reach. Low algorithmic harm \u2014 retail, not platform. But worker surveillance technology increasing.",
    "confidence": "estimated",
    "algorithmic_harm_score": 18,
    "subsidiaries": [
      "Sam's Club",
      "Flipkart",
      "PhonePe"
    ],
    "primary_contractors": [
      "Supply chain vendors (thousands)"
    ]
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
    "notes": "Shipt acquisition maintains gig worker structure (contractor model). Store experience emphasizes human interaction more than competitors. DEI commitments strong but faced political backlash. Employee wages competitive. Algorithmic pricing and inventory management standard for retail. Circle loyalty program collects data but low manipulation.",
    "confidence": "estimated",
    "algorithmic_harm_score": 12,
    "subsidiaries": [
      "Shipt"
    ]
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
    "notes": "Industry-leading employee wages and retention. Human-first retail model \u2014 minimal self-checkout, staffed departments, in-house bakery/meat cutting. Low algorithmic manipulation. Kirkland brand maintains quality focus over optimization. CEO pay ratio among lowest in retail. Membership model creates sustainable revenue without ad-driven engagement. Environmental practices improving. One of the strongest H and U scores in retail.",
    "confidence": "estimated",
    "algorithmic_harm_score": 5
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
    "notes": "Barista craft is genuine human skill. Mobile ordering reduces human interaction. Union-busting allegations severely impact U and M. Howard Schultz era emphasized human-centric culture \u2014 post-Schultz direction uncertain. Environmental commitments (reusable cups) improving A. Store algorithm optimizes labor scheduling \u2014 can feel dehumanizing to workers. Benefits historically strong (healthcare, tuition) but union tensions undermine narrative.",
    "confidence": "estimated",
    "algorithmic_harm_score": 10
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
    "name": "Nestl\u00e9",
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
    "notes": "Beverage manufacturing maintains human involvement. Marketing historically human-creative but increasing AI-generated campaigns. Environmental concerns from plastic waste (A). Water usage in drought-prone regions. Community investment programs strong. Low algorithmic harm \u2014 product company, not platform. Bottling partner model distances corporate from worker conditions. Strong brand storytelling tradition.",
    "confidence": "estimated",
    "algorithmic_harm_score": 8
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
    "notes": "Diversified food/beverage portfolio maintains manufacturing jobs. Frito-Lay factory conditions under scrutiny. Environmental commitments improving \u2014 water stewardship. Marketing increasingly AI-assisted but maintains human creative teams. Low algorithmic harm. CEO pay ratio moderate for industry. Community investment programs active.",
    "confidence": "estimated",
    "algorithmic_harm_score": 8,
    "subsidiaries": [
      "Frito-Lay",
      "Quaker Oats",
      "Gatorade"
    ]
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
    "notes": "Franchise model distances corporate from worker conditions. Dynamic Yield acquisition brought AI-driven menu personalization. Drive-through AI ordering being tested \u2014 direct human displacement. Low craft (H) in food preparation. Worker wages and conditions vary dramatically by franchise. Strong brand but fundamentally optimizing humans out of the operation.",
    "confidence": "estimated",
    "algorithmic_harm_score": 22,
    "subsidiaries": [
      "Dynamic Yield (AI personalization)"
    ],
    "primary_contractors": [
      "Franchise operators (95% of locations)"
    ]
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
    "notes": "Gold standard for ethical business. Transferred ownership to environmental trust. Fair Trade certified factories. Repair program extends product life (right-to-repair leader). Transparent supply chain. High craft in product design. Employee benefits exceptional. Low automation, high human involvement at every level. Environmental mission is core, not marketing. Minimal algorithmic anything \u2014 catalogs and stores, not feeds and algorithms.",
    "confidence": "estimated",
    "algorithmic_harm_score": 3
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
    "notes": "Supply chain labor practices historically problematic but improved with transparency initiatives. High craft in design (H). SNKRS app uses scarcity algorithms but low overall harm. Strong athlete partnerships maintain human storytelling. DTC shift reduces retail worker jobs. Sustainability initiatives improving but still significant manufacturing footprint.",
    "confidence": "estimated",
    "algorithmic_harm_score": 12
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
    "notes": "AI trading algorithms raise market manipulation concerns. Chase app increasingly automated \u2014 human banker access declining. Strong institutional advisory maintains human judgment. Massive workforce but AI investment growing faster than headcount. CEO Jamie Dimon publicly vocal about AI transforming banking \u2014 unclear if augmentation or replacement focus. Regulatory compliance strong but fines history (M).",
    "confidence": "estimated",
    "algorithmic_harm_score": 25,
    "subsidiaries": [
      "Chase",
      "J.P. Morgan Asset Management",
      "J.P. Morgan Wealth Management"
    ]
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
    "notes": "Algorithmic trading pioneer \u2014 AI displacing human traders for decades. Marcus consumer banking experiment largely failed (human touch missing). Asset management maintains high human judgment. CEO pay among highest in finance. Strong talent pipeline but increasingly technical/AI focused. IPO advisory and M&A work is deeply human (high H in investment banking). Platform Solutions losses reflect difficulty of automated consumer finance.",
    "confidence": "estimated",
    "algorithmic_harm_score": 20,
    "subsidiaries": [
      "Marcus by Goldman Sachs",
      "Goldman Sachs Asset Management"
    ]
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
    "notes": "Healthcare fundamentally human \u2014 high structural moat against AI displacement. Talc litigation severely impacts M. Strong R&D investment maintains human scientific craft. Medical device manufacturing requires human precision. Pharmaceutical research maintains human judgment in clinical decisions. Kenvue consumer health spin-off separates lower-moat operations. Environmental compliance improving.",
    "confidence": "estimated",
    "algorithmic_harm_score": 8,
    "subsidiaries": [
      "Janssen Pharmaceuticals",
      "DePuy Synthes",
      "Ethicon"
    ]
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
    "notes": "COVID vaccine development showcased human scientific achievement. AI used in drug discovery augments rather than replaces researchers. High craft in pharmaceutical science. Pricing practices (M) controversial \u2014 insulin, oncology drugs. Patent strategies extend monopolies. Strong regulatory compliance. Environmental footprint from manufacturing.",
    "confidence": "estimated",
    "algorithmic_harm_score": 8
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
    "notes": "Optum's nH Predict algorithm denied elderly patients care \u2014 documented by investigative journalism. Claims denial algorithms prioritize cost over patient outcomes. Change Healthcare acquisition creates data monopoly in health payments. Massive workforce but automating claims processing. CEO compensation among highest in any industry. Strong revenue growth but at what human cost. Healthcare should be the most human industry \u2014 UHG is automating it.",
    "confidence": "estimated",
    "algorithmic_harm_score": 42,
    "subsidiaries": [
      "Optum",
      "UnitedHealthcare",
      "Change Healthcare"
    ]
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
    "notes": "Theme parks are deeply human experiences \u2014 high craft, high empathy. Animation maintains human artistic tradition (Pixar, WDAS). But Disney+ algorithm follows Netflix model for content optimization. ESPN increasingly algorithmic. Massive layoffs (7,000+) while investing in streaming technology. Strong creative legacy but commercial pressure increasingly AI-driven. Worker conditions at parks improving but historically problematic.",
    "confidence": "estimated",
    "algorithmic_harm_score": 18,
    "subsidiaries": [
      "Pixar",
      "Marvel",
      "Lucasfilm",
      "ESPN",
      "Hulu",
      "20th Century Studios",
      "National Geographic"
    ]
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
    "notes": "Content moderation contractor for major tech \u2014 workers exposed to traumatic content with documented mental health impacts. Simultaneously selling AI replacement solutions to clients while maintaining large human workforce. Consulting model is inherently human but increasingly AI-augmented. Strong DEI initiatives. Global workforce provides employment across developing markets. The tension: Accenture profits from both employing humans AND helping clients replace them.",
    "confidence": "estimated",
    "algorithmic_harm_score": 15,
    "subsidiaries": [
      "Avanade (joint venture with Microsoft)"
    ],
    "primary_contractors": [
      "Content moderation workers for Meta, Google, TikTok"
    ]
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
    "notes": "Large workforce but steady automation of customer service. Closing retail stores displaces workers. 5G infrastructure investment maintains technical human roles. Union workforce provides some protection. Customer satisfaction historically low \u2014 automated support systems frustrate consumers. Data throttling and pricing practices (M). Rural broadband investment positive.",
    "confidence": "estimated",
    "algorithmic_harm_score": 15,
    "subsidiaries": [
      "Cricket Wireless",
      "WarnerMedia (divested to WBD)",
      "DirecTV (partial)"
    ]
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
    "notes": "Similar to AT&T \u2014 large workforce, steady automation. Customer service increasingly chatbot-driven. Network investment maintains engineering roles. Fios fiber provides genuine infrastructure value. Historical media acquisitions (Yahoo, AOL) were mismanaged. Customer data practices improved post-supercookie scandal.",
    "confidence": "estimated",
    "algorithmic_harm_score": 12,
    "subsidiaries": [
      "Tracfone",
      "Visible",
      "Yahoo/AOL (Verizon Media, divested)"
    ]
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
    "notes": "Post-acquisition (X/Musk): massive workforce reduction (80%+), trust and safety team gutted, verification system monetized undermining authenticity. Algorithm changes increased engagement-bait visibility. Advertiser exodus reflects brand safety concerns. Pre-acquisition: already had misinformation amplification issues. Blue check monetization is transparency regression.",
    "confidence": "estimated",
    "algorithmic_harm_score": 58
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
