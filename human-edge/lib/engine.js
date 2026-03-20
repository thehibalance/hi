/**
 * HI. Grade Filter Engine
 * 
 * Pure deterministic logic for:
 *   - Computing composite HUMAN scores (HI Grades)
 *   - Applying the floor rule
 *   - Classifying scores into score-only + HI Balanced certification
 *   - Filtering companies against user thresholds
 *   - Detecting humanwashing flags (rule-based)
 * 
 * SPECIFICATION REFERENCE: HUMAN Methodology Spec v1.0
 * Governed by: The Deep Thought Foundation
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

  TIERS: [
    { min: 0, max: 100, grade: "scored", name: "Scored", letter: "",
      stars: "", color: "#1B3A5C", requiresVerification: false,
      satire: "",
      badge: "" },
  ],

  HI_BALANCED_COLOR: "#C49B20",
  SCORE_COLOR: "#1B3A5C",

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
   * Classify a composite score into an HI Grade tier.
   * Companies scoring 90+ from public data are capped at "A" unless HI Balanced.
   * @param {number} composite - The composite HUMAN score (0-100)
   * @param {boolean} verified - Whether the company has completed HI Certification
   * @returns {Object} tier object with grade, satire, badge, etc.
   */
  classifyTier(composite, verified = false) {
    return { ...this.TIERS[0], cappedFromCertified: false };
  },

  /**
   * Check if a company passes all 10 HI Balanced gates.
   * Adaptive threshold: mean + 2 SD, recalculated from market data.
   */
  checkHIBalanced(company, composite, hwFlags, marketStats) {
    const dims = this.DIMENSIONS.map(d => company[d] || 0);
    const belowCount = dims.filter(s => s < 42).length;
    
    // Default threshold if no market stats available
    const threshold = (marketStats && marketStats.hiBalancedThreshold) || 62;
    
    const gates = {
      composite: composite >= threshold,
      allDimsAbove42: belowCount === 0,
      noHumanwashing: hwFlags.length === 0,
      decayBelow30: (company.decay_index || 0) < 30,
      shieldAbove50: (company.shield_score || 50) >= 50,
      noESGWashing: !(company.esg_washing || false),
      notNegativeLeader: !(company.negative_contagion_leader || false),
      noCriticalGaps: !(company.critical_genome_gaps || false),
      notUnderPressure: !(company.under_collective_pressure || false),
      noActiveAlerts: (company.decay_level || 'stable') !== 'critical',
    };
    
    const passed = Object.values(gates).every(v => v);
    return { balanced: passed, gates, threshold };
  },

  /**
   * Get full HI Grade profile for a company.
   * @param {Object} company - Company object from database
   * @returns {Object} Complete score profile
   */
  getProfile(company, marketStats) {
    const { composite, floorTriggered, floorDimension } = this.computeComposite(company);
    const hwFlags = this.detectHumanwashing(company);

    // Balance floor rule: dimensions below 42
    const scores = this.DIMENSIONS.map(d => company[d] || 0);
    const belowCount = scores.filter(s => s < 42).length;
    const minScore = Math.min(...scores);
    const minDim = this.DIMENSIONS[scores.indexOf(minScore)];
    let balanceFloor = false;
    let balanceDim = null;
    let adjustedComposite = composite;
    
    if (belowCount >= 2) {
      balanceFloor = true;
      balanceDim = minDim;
      adjustedComposite = Math.min(composite, 41);
    } else if (belowCount === 1) {
      balanceFloor = true;
      balanceDim = minDim;
      adjustedComposite = Math.min(composite, 49);
    }

    // Check HI Balanced gates
    const balanced = this.checkHIBalanced(company, adjustedComposite, hwFlags, marketStats);
    const isBalanced = balanced.certified;
    const scoreColor = isBalanced ? this.HI_BALANCED_COLOR : this.getScoreColor(adjustedComposite, balanced.threshold);

    return {
      id: company.id,
      name: company.name,
      dimensions: {
        h: company.h, u: company.u, m: company.m, a: company.a, n: company.n
      },
      composite: Math.round(adjustedComposite),
      hiBalanced: isBalanced,
      balancedGates: balanced.gates,
      balancedThreshold: balanced.threshold,
      grade: isBalanced ? "Gold HI Grade" : "scored",
      letter: isBalanced ? "HI." : "",
      scoreColor,
      tier: { color: scoreColor, satire: isBalanced ? "Humans and tech, in harmony. Gold HI Grade earned." : "" },
      floorTriggered,
      floorDimension,
      balanceFloor,
      balanceDim,
      balanceBelowCount: belowCount,
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
  getScoreColor(score, threshold) {
    const t = threshold || 62;
    if (score >= t) return "#16A34A";   // Green — above threshold
    if (score >= 42) return "#D97706";  // Yellow — room to grow
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
