/**
 * HI. Grade Filter Engine
 * 
 * Pure deterministic logic for:
 *   - Computing composite HUMAN scores (HI Grades)
 *   - Applying the floor rule
 *   - Classifying scores into 5 tiers (HI Certified, A, B, C, F)
 *   - Filtering companies against user thresholds
 *   - Detecting humanwashing flags (rule-based)
 * 
 * SPECIFICATION REFERENCE: HUMAN Methodology Spec v1.0
 * Governed by: The Deep Thought Foundation
 * Brand: HI. — Human Intelligence
 * 
 * ╔══════════════════════════════════════════════════════╗
 * ║  NO AI. NO ML. NO NEURAL NETWORKS. NO INFERENCE.   ║
 * ║  Every decision is traceable. Every line auditable.  ║
 * ║  Hi — choose human.                                  ║
 * ╚══════════════════════════════════════════════════════╝
 */

const HumanEngine = {

  // ═══ CONSTANTS (from Methodology Spec v1.0) ═══

  DIMENSION_WEIGHT: 0.20, // Each dimension weighted equally at 20%
  FLOOR_THRESHOLD: 10,     // If any dimension below this...
  FLOOR_CAP: 40,           // ...cap composite at this value

  TIERS: [
    { min: 90, max: 100, grade: "HI Certified", name: "HI Certified", letter: "HI",
      stars: "★★★★★", color: "#1a7a3a", requiresVerification: true,
      satire: "Humans and tech, in harmony. This is what balance looks like.",
      badge: "HI Certified — this is what balance looks like." },
    { min: 80, max: 89,  grade: "A", name: "Excellent", letter: "A",
      stars: "★★★★☆", color: "#2e8b57", requiresVerification: false,
      satire: "AI does the math. Humans do the handshakes. Nailed it.",
      badge: "Excellent — nailed the balance." },
    { min: 60, max: 79,  grade: "B", name: "Good", letter: "B",
      stars: "★★★☆☆", color: "#4a90d9", requiresVerification: false,
      satire: "Humans and machines, learning to share the remote.",
      badge: "Good — learning to share the remote." },
    { min: 42, max: 59,  grade: "C", name: "The Answer", letter: "C",
      stars: "★★☆☆☆", color: "#d4a843", requiresVerification: false,
      satire: "42. The answer to everything. Now what's the question?",
      badge: "42 — now what's the question?" },
    { min: 0,  max: 41,  grade: "F", name: "Failing Humanity", letter: "F",
      stars: "★☆☆☆☆", color: "#c0392b", requiresVerification: false,
      satire: "Don't panic. Every journey starts somewhere.",
      badge: "Don't panic." },
  ],

  DIMENSIONS: ['h', 'u', 'm', 'a', 'n'],

  DIMENSION_LABELS: {
    h: "Human Consciousness",
    u: "Understanding & Empathy",
    m: "Moral & Ethical Conduct",
    a: "Alive & Environmental",
    n: "Natural Transparency"
  },

  // ═══ SCORING ═══

  /**
   * Compute composite HUMAN score from dimension scores.
   * Formula: HUMAN = (H + U + M + A + N) / 5
   * Floor rule: if min(H,U,M,A,N) < FLOOR_THRESHOLD, cap at FLOOR_CAP
   * 
   * @param {Object} company - Object with h, u, m, a, n properties (0-100 each)
   * @returns {Object} { composite, floorTriggered, floorDimension }
   */
  computeComposite(company) {
    const scores = this.DIMENSIONS.map(d => company[d] || 0);
    const raw = scores.reduce((sum, s) => sum + s, 0) / 5;

    // Floor rule check
    const minScore = Math.min(...scores);
    const minDimension = this.DIMENSIONS[scores.indexOf(minScore)];
    const floorTriggered = minScore < this.FLOOR_THRESHOLD;
    const composite = floorTriggered ? Math.min(raw, this.FLOOR_CAP) : raw;

    return {
      composite: Math.round(composite * 10) / 10, // 1 decimal place
      floorTriggered,
      floorDimension: floorTriggered ? minDimension : null
    };
  },

  // ═══ TIER CLASSIFICATION ═══

  /**
   * Classify a composite score into an HI Grade tier.
   * Companies scoring 90+ from public data are capped at "A" unless HI Certified.
   * @param {number} composite - The composite HUMAN score (0-100)
   * @param {boolean} verified - Whether the company has completed HI Certification
   * @returns {Object} tier object with grade, satire, badge, etc.
   */
  classifyTier(composite, verified = false) {
    for (const tier of this.TIERS) {
      if (composite >= tier.min && composite <= tier.max) {
        // HI Certified tier requires verification — cap at A if not verified
        if (tier.requiresVerification && !verified) {
          return {
            ...this.TIERS[1], // Return "A" tier instead
            cappedFromCertified: true,
            cappedNote: "Scores above 90 but has not completed HI Certification. Displayed as A until verified."
          };
        }
        return { ...tier, cappedFromCertified: false };
      }
    }
    return { ...this.TIERS[this.TIERS.length - 1], cappedFromCertified: false };
  },

  /**
   * Get full HI Grade profile for a company.
   * @param {Object} company - Company object from database
   * @returns {Object} Complete score profile with grade, satire, etc.
   */
  getProfile(company) {
    const { composite, floorTriggered, floorDimension } = this.computeComposite(company);
    const verified = company.confidence === "verified";
    const tier = this.classifyTier(composite, verified);
    const hwFlags = this.detectHumanwashing(company);

    return {
      id: company.id,
      name: company.name,
      dimensions: {
        h: company.h,
        u: company.u,
        m: company.m,
        a: company.a,
        n: company.n
      },
      composite,
      grade: tier.grade,
      letter: tier.letter,
      tier,
      floorTriggered,
      floorDimension,
      humanwashingFlags: hwFlags,
      confidence: company.confidence || "estimated",
      source: company.source || "local"
    };
  },

  // ═══ FILTERING ═══

  /**
   * Default user preferences.
   */
  DEFAULT_PREFS: {
    masterToggle: true,       // true = full view, false = filtered
    filterMode: "soft",       // "strict" or "soft"
    thresholds: {
      h: 0, u: 0, m: 0, a: 0, n: 0  // Default: show everything
    },
    minimumConfidence: "estimated" // "verified" or "estimated"
  },

  /**
   * Check if a company passes the user's filter thresholds.
   * 
   * @param {Object} company - Company object
   * @param {Object} prefs - User preferences with thresholds
   * @returns {Object} { passes, failedDimensions }
   */
  applyFilter(company, prefs) {
    // If master toggle is ON (full view), everything passes
    if (prefs.masterToggle) {
      return { passes: true, failedDimensions: [] };
    }

    const failedDimensions = [];

    for (const dim of this.DIMENSIONS) {
      const score = company[dim] || 0;
      const threshold = (prefs.thresholds && prefs.thresholds[dim]) || 0;
      if (score < threshold) {
        failedDimensions.push(dim);
      }
    }

    // Check floor rule
    const { floorTriggered } = this.computeComposite(company);
    if (floorTriggered) {
      failedDimensions.push('floor');
    }

    return {
      passes: failedDimensions.length === 0,
      failedDimensions
    };
  },

  // ═══ HUMANWASHING DETECTION (Edge Heuristics) ═══
  // Spec Reference: Section 9, Methodology Spec v1.0
  // These are RULE-BASED heuristics. No ML. No inference.

  /**
   * Detect humanwashing flags using deterministic rules.
   * Edge-side implementation uses structured data fields only.
   * 
   * @param {Object} company - Company object
   * @returns {Array} Array of triggered flag objects
   */
  detectHumanwashing(company) {
    const flags = [];

    // HW.1: High Automation Signal
    // Revenue per employee significantly above industry average
    if (company.revenuePerEmployee && company.industryMedianRPE) {
      if (company.revenuePerEmployee > company.industryMedianRPE * 3) {
        flags.push({
          id: "HW.1",
          name: "High Automation Signal",
          detail: "Revenue per employee exceeds 3x industry median",
          severity: 25
        });
      }
    }

    // HW.2: Rapid AI Displacement
    // Headcount down while AI investment up
    if (company.headcountDelta !== undefined && company.aiInvestDelta !== undefined) {
      if (company.headcountDelta < -0.20 && company.aiInvestDelta > 0.30) {
        flags.push({
          id: "HW.2",
          name: "Rapid AI Displacement",
          detail: "Headcount ↓ >20% YoY while AI CapEx ↑ >30%",
          severity: 30
        });
      }
    }

    // HW.3: Simulated Empathy Indicator
    // No human service + empathy marketing claims
    if (company.humanServiceChannels === 0 && company.empathyMarketingClaims === true) {
      flags.push({
        id: "HW.3",
        name: "Simulated Empathy",
        detail: "No human customer service but markets empathetic care",
        severity: 25
      });
    }

    // HW.4: Transparency Gap
    // Claims no AI but uses known AI tools
    if (company.disclosedAIUsage === "none" && company.detectedAITools === true) {
      flags.push({
        id: "HW.4",
        name: "Transparency Gap",
        detail: "Claims no AI usage but AI tools detected in operations",
        severity: 30
      });
    }

    return flags;
  },

  // ═══ UTILITIES ═══

  /**
   * Get the color for a score value (gradient from red to green).
   */
  getScoreColor(score) {
    if (score >= 75) return "#1a7a3a";
    if (score >= 60) return "#2e8b57";
    if (score >= 45) return "#d4a843";
    if (score >= 30) return "#d47843";
    return "#c0392b";
  },

  /**
   * Format a dimension label.
   */
  getDimensionLabel(dim) {
    return this.DIMENSION_LABELS[dim] || dim.toUpperCase();
  },

  /**
   * Clamp a value between min and max.
   */
  clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }
};
