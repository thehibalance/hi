/**
 * HI. Grade Filter Engine
 * 
 * Pure deterministic logic for:
 *   - Computing composite HUMAN scores (HI Grades)
 *   - Applying the floor rule
 *   - Gold HI Grade: 3 gates (score, balance, honesty)
 *   - Filtering companies against user thresholds
 *   - Detecting humanwashing flags (rule-based)
 * 
 * SPECIFICATION REFERENCE: HUMAN Methodology Spec v1.0
 * Governed by: The HI Balance
 * Brand: HI. — Think human intelligence.
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

  // Score-only system: every company gets a number 0-100.
  // Gold HI Grade is earned by passing 3 gates. No letter grades.
  GOLD_COLOR: "#C49B20",
  SCORE_COLOR: "#1B3A5C",

  // Adaptive threshold defaults (overridden by market stats)
  GOLD_HARD_FLOOR: 55,  // Threshold never drops below this

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
    let composite = floorTriggered ? Math.min(raw, this.FLOOR_CAP) : raw;
    
    // Round to whole number (same as cloud scoring engine)
    composite = Math.round(composite);

    return {
      composite,
      floorTriggered,
      floorDimension: floorTriggered ? minDimension : null
    };
  },

  // ═══ TIER CLASSIFICATION ═══

  /**
   * Classify a composite score. Score-only system — no letter grades.
   * Returns display info. Gold status is determined by checkGoldHIGrade().
   */
  classifyScore(composite) {
    return {
      composite,
      color: this.getScoreColor(composite),
    };
  },

  /**
   * Check if a company earns Gold HI Grade.
   * 3 gates, 3 categories. The data decides.
   *
   * Gate 1 — SCORE: Composite ≥ adaptive threshold (mean + 2σ, hard floor 55, ratchet up only)
   * Gate 2 — BALANCE: All 5 HUMAN dimensions ≥ 42
   * Gate 3 — HONESTY: No Humanwashing™ flags AND Algorithmic Harm Index™ below 30
   *
   * Score, balance, and honesty.
   */
  checkGoldHIGrade(company, composite, hwFlags, marketStats) {
    const dims = this.DIMENSIONS.map(d => company[d] || 0);
    const belowCount = dims.filter(s => s < 42).length;
    
    // Adaptive threshold: mean + 2σ from market data, with hard floor and ratchet
    // Accept threshold directly or from marketStats object
    let threshold = 62;
    if (typeof marketStats === 'number') {
      threshold = marketStats;  // Direct threshold value
    } else if (marketStats && marketStats.hiBalancedThreshold) {
      threshold = marketStats.hiBalancedThreshold;
    }
    threshold = Math.round(threshold);  // Always whole numbers
    
    // Gate 3: Honesty — both Humanwashing™ and Algorithmic Harm Index™
    const ahiScore = company.algorithmic_harm_score || company.ahi_score || 0;
    const honesty = hwFlags.length === 0 && ahiScore < 30;
    
    const gates = {
      score: composite >= threshold,       // Gate 1: Score
      balance: belowCount === 0,           // Gate 2: Balance (all dims ≥ 42)
      honesty: honesty,                    // Gate 3: Honesty (Humanwashing™ + AHI™)
    };
    
    const isGold = Object.values(gates).every(v => v);
    return { gold: isGold, gates, threshold };
  },

  /**
   * Get full HI Grade profile for a company.
   * Score-only system: number 0-100, color-coded.
   * Gold HI Grade earned by passing 3 gates.
   * @param {Object} company - Company object from database
   * @returns {Object} Complete score profile
   */
  getProfile(company, marketStats) {
    const { composite, floorTriggered, floorDimension } = this.computeComposite(company);
    const hwFlags = this.detectHumanwashing(company);

    // Check Gold HI Grade (3 gates)
    const goldCheck = this.checkGoldHIGrade(company, composite, hwFlags, marketStats);
    const isGold = goldCheck.gold;
    const scoreColor = isGold ? this.GOLD_COLOR : this.getScoreColor(composite, goldCheck.threshold);

    // Balance info (for display — dimensions below 42)
    const scores = this.DIMENSIONS.map(d => company[d] || 0);
    const belowCount = scores.filter(s => s < 42).length;
    const minScore = Math.min(...scores);
    const minDim = this.DIMENSIONS[scores.indexOf(minScore)];

    return {
      id: company.id,
      name: company.name,
      dimensions: {
        h: company.h, u: company.u, m: company.m, a: company.a, n: company.n
      },
      composite,
      isGold,
      hiBalanced: isGold,  // backward compat for content.js / popup.js
      goldGates: goldCheck.gates,
      goldThreshold: goldCheck.threshold,
      balancedThreshold: goldCheck.threshold,  // backward compat alias
      grade: isGold ? "Gold HI Grade" : "Scored",
      scoreColor,
      tier: { color: scoreColor, satire: isGold ? "Humans and tech, in harmony. Gold HI Grade earned." : "" },
      floorTriggered,
      floorDimension,
      belowCount,
      weakestDim: minDim,
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
   * Get the color for a score value.
   * Green = above Gold threshold, Yellow = above 42, Red = below 42.
   */
  getScoreColor(score, threshold) {
    const t = threshold || 62;
    if (score >= t) return "#16A34A";   // Green — Gold territory
    if (score >= 42) return "#D97706";  // Amber — balanced but not Gold
    return "#DC2626";                   // Red — out of balance
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
