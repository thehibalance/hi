/**
 * HI. Grade Filter Engine — v1.2.0
 * 
 * Pure deterministic logic for:
 *   - Computing composite HUMAN scores (HI Grades)
 *   - Gold HI Grade: 3 gates (Dimensions / Evidence / Momentum)
 *   - Filtering companies against user's personal thresholds
 *   - Detecting humanwashing flags (rule-based)
 * 
 * SPECIFICATION REFERENCE: HUMAN Methodology Spec v1.2.0
 * Governed by: Morf Innovations LLC
 * Brand: HI. — Human kind?
 * 
 * ╔══════════════════════════════════════════════════════╗
 * ║  NO AI. NO ML. NO NEURAL NETWORKS. NO INFERENCE.    ║
 * ║  Every decision is traceable. Every line auditable.  ║
 * ╚══════════════════════════════════════════════════════╝
 *
 * v1.1.0 GATE CHANGES from v1.0:
 *   Old Gate 1 (SCORE):     composite ≥ adaptive threshold
 *   New Gate 1 (DIMENSIONS): all 5 dims ≥ 60
 *
 *   Old Gate 2 (BALANCE):   all dims ≥ 42
 *   New Gate 2 (EVIDENCE):   each dim has ≥1 verified public source
 *
 *   Old Gate 3 (HONESTY):   no Humanwashing™ + AHI < 30
 *   New Gate 3 (MOMENTUM):   not in warning/critical decay (90-day Heartbeat)
 *
 * Why simplified: Humanwashing and AHI are now absorbed INTO dimension
 * scores via the harm pipelines (HW, AHI, PHI, HD), so they no longer
 * need a separate gate. Momentum is a separate gate because backward-
 * looking dimension data can't see real-time signals fast enough
 * (e.g., Oracle layoffs in early 2025 not caught by annual SEC filings).
 */

const HumanEngine = {

  // ═══ CONSTANTS (from Methodology Spec v1.2.0) ═══

  GOLD_DIM_THRESHOLD: 60,   // Each HUMAN dimension must score ≥ 60 (Gate 1)
  GOLD_DECAY_BLOCKING: ['warning', 'critical'],  // Decay levels that block Gold (Gate 3)

  // Score-only system: every company gets a number 0-100.
  // Gold HI Grade is earned by passing 3 gates.
  GOLD_COLOR: '#C49B20',
  SCORE_COLOR: '#1B3A5C',

  DIMENSIONS: ['h', 'u', 'm', 'a', 'n'],

  DIMENSION_LABELS: {
    h: 'Human Consciousness',
    u: 'Understanding & Empathy',
    m: 'Moral & Ethical Conduct',
    a: 'Alive & Environmental',
    n: 'Natural Transparency'
  },

  // Sources that count as "seed only" — fail Evidence gate
  SEED_SOURCES: ['Defaults', 'Manual Scoring', 'Seed Estimate', 'Public Reporting'],

  // ═══ SCORING ═══

  /**
   * Compute composite HUMAN score from dimension scores.
   * Formula (v1.2.0): composite = (H + U + M + A + N) / 5
   * Floor rule (v1.2.0): if any HUMAN dimension < 30, composite is capped at 50.
   *   - Mirrors backend pipeline/scoring_engine.py:compute_composite
   *   - floorTriggered fires whenever min_dim < 30, regardless of cap effect
   *   - floorDimension is the uppercase letter of the lowest dim ('H','U','M','A','N')
   */
  computeComposite(company) {
    const scores = this.DIMENSIONS.map(d => company[d] || 0);
    let composite = Math.round(scores.reduce((sum, s) => sum + s, 0) / 5);
    const minDim = Math.min(...scores);
    let floorTriggered = false;
    let floorDimension = null;
    if (minDim < 30) {
      composite = Math.min(composite, 50);
      floorTriggered = true;
      floorDimension = this.DIMENSIONS[scores.indexOf(minDim)].toUpperCase();
    }
    return { composite, floorTriggered, floorDimension };
  },

  /**
   * Check if a company earns Gold HI Grade (v1.2.0 spec).
   * 3 gates: Dimensions / Evidence / Momentum.
   *
   * Gate 1 — DIMENSIONS: All 5 HUMAN dims ≥ 60
   * Gate 2 — EVIDENCE:   Each dim has ≥1 real public source (not Seed/default)
   * Gate 3 — MOMENTUM:   decay_level not in 'warning' or 'critical'
   *
   * Trusts cloud-provided gate booleans when available (cloud is authoritative).
   * Falls back to local computation otherwise.
   */
  checkGoldHIGrade(company, composite, hwFlags, _legacyArg) {
    // ── GATE 1: DIMENSIONS — all 5 dims ≥ 60 ──
    const dims = this.DIMENSIONS.map(d => company[d] || 0);
    const dimensionsPass = dims.every(s => s >= this.GOLD_DIM_THRESHOLD);

    // ── GATE 2: EVIDENCE — each dim has real source ──
    // Trust cloud-provided value if present, else compute from genome.sources
    let evidencePass = false;
    if (typeof company.cloud_hi_balanced_gates_evidence === 'boolean') {
      evidencePass = company.cloud_hi_balanced_gates_evidence;
    } else if (company.genome) {
      // Each dim needs at least one non-seed source
      evidencePass = ['H', 'U', 'M', 'A', 'N'].every(D => {
        const dd = company.genome[D] || {};
        const srcs = dd.sources || [];
        if (!srcs.length) return false;
        return srcs.some(s => !this.SEED_SOURCES.includes(s));
      });
    } else {
      // No genome data — can't verify, default to false (conservative)
      evidencePass = false;
    }

    // ── GATE 3: MOMENTUM — not in warning/critical decay ──
    const decayLevel = company.decay_level || 'stable';
    const momentumPass = !this.GOLD_DECAY_BLOCKING.includes(decayLevel);

    const gates = {
      dimensions: dimensionsPass,
      evidence: evidencePass,
      momentum: momentumPass,
      // backward-compat aliases for any legacy code reading old keys
      score: dimensionsPass,
      balance: evidencePass,
      honesty: momentumPass,
      integrity: momentumPass
    };

    const isGold = dimensionsPass && evidencePass && momentumPass;

    // Threshold returned for backward compat — in v1.2.0 it's the per-dim threshold (60), not composite
    return { gold: isGold, gates, threshold: this.GOLD_DIM_THRESHOLD };
  },

  /**
   * Get full HI Grade profile for a company.
   * If company has cloud_hi_balanced_gates (object from API), trust those over local computation.
   */
  getProfile(company, _legacyArg) {
    const { composite, floorTriggered, floorDimension } = this.computeComposite(company);
    const hwFlags = this.detectHumanwashing(company);

    // Trust cloud gates if provided
    let goldCheck;
    if (company.cloud_hi_balanced_gates && typeof company.cloud_hi_balanced_gates === 'object') {
      const g = company.cloud_hi_balanced_gates;
      const gates = {
        dimensions: !!g.dimensions,
        evidence: !!g.evidence,
        momentum: !!g.momentum,
        score: !!g.dimensions,
        balance: !!g.evidence,
        honesty: !!g.momentum,
        integrity: !!g.momentum
      };
      goldCheck = {
        gold: !!company.cloud_hi_balanced || (gates.dimensions && gates.evidence && gates.momentum),
        gates,
        threshold: this.GOLD_DIM_THRESHOLD
      };
    } else {
      goldCheck = this.checkGoldHIGrade(company, composite, hwFlags);
    }

    const isGold = goldCheck.gold;
    const scoreColor = isGold ? this.GOLD_COLOR : this.getScoreColor(composite);

    return {
      id: company.id,
      name: company.name,
      dimensions: { h: company.h, u: company.u, m: company.m, a: company.a, n: company.n },
      composite,
      isGold,
      hiBalanced: isGold,             // backward compat
      goldGates: goldCheck.gates,
      goldThreshold: goldCheck.threshold,
      balancedThreshold: goldCheck.threshold,  // backward compat
      grade: isGold ? 'Gold HI Grade' : 'Scored',
      scoreColor,
      tier: { color: scoreColor, satire: isGold ? 'Humans and tech, in harmony. Gold HI Grade earned.' : '' },
      floorTriggered,                 // v1.2.0: any dim < 30 → cap composite at 50
      floorDimension,
      humanwashingFlags: hwFlags,
      confidence: company.confidence || 'estimated',
      source: company.source || 'local'
    };
  },

  // ═══ FILTERING (user's personal thresholds — separate from Gold gates) ═══

  DEFAULT_PREFS: {
    masterToggle: true,       // true = full view, false = filtered
    filterMode: 'soft',
    thresholds: { h: 0, u: 0, m: 0, a: 0, n: 0 },
    minimumConfidence: 'estimated'
  },

  applyFilter(company, prefs) {
    if (prefs.masterToggle) return { passes: true, failedDimensions: [] };

    const failedDimensions = [];
    for (const dim of this.DIMENSIONS) {
      const score = company[dim] || 0;
      const threshold = (prefs.thresholds && prefs.thresholds[dim]) || 0;
      if (score < threshold) failedDimensions.push(dim);
    }

    return { passes: failedDimensions.length === 0, failedDimensions };
  },

  // ═══ HUMANWASHING DETECTION (rule-based, no ML) ═══
  // These are kept for display purposes — but NO LONGER affect Gold gates in v1.2.0.
  // The harm pipelines (HW, AHI, PHI, HD) absorb these into dimension scores.

  detectHumanwashing(company) {
    const flags = [];

    if (company.revenuePerEmployee && company.industryMedianRPE) {
      if (company.revenuePerEmployee > company.industryMedianRPE * 4) {
        flags.push({
          id: 'HW.1',
          name: 'High Automation Signal',
          detail: 'Revenue per employee exceeds 4x industry median',
          severity: 25
        });
      }
    }

    if (company.headcountDelta !== undefined && company.aiInvestDelta !== undefined) {
      if (company.headcountDelta < -0.20 && company.aiInvestDelta > 0.30) {
        flags.push({
          id: 'HW.2',
          name: 'Rapid AI Displacement',
          detail: 'Headcount ↓ >20% YoY while AI CapEx ↑ >30%',
          severity: 30
        });
      }
    }

    if (company.humanServiceChannels === 0 && company.empathyMarketingClaims === true) {
      flags.push({
        id: 'HW.3',
        name: 'Simulated Empathy',
        detail: 'No human customer service but markets empathetic care',
        severity: 25
      });
    }

    if (company.disclosedAIUsage === 'none' && company.detectedAITools === true) {
      flags.push({
        id: 'HW.4',
        name: 'Transparency Gap',
        detail: 'Claims no AI usage but AI tools detected in operations',
        severity: 30
      });
    }

    return flags;
  },

  // ═══ UTILITIES ═══

  /**
   * Get the color for a score value.
   * v1.2.0: Green ≥ 60 (Dimensions gate threshold), Amber ≥ 42, Red < 42.
   */
  getScoreColor(score, _legacyArg) {
    if (score >= this.GOLD_DIM_THRESHOLD) return '#16A34A';   // Green — Gold-eligible
    if (score >= 42) return '#D97706';  // Amber — middling
    return '#DC2626';                   // Red — below threshold
  },

  getDimensionLabel(dim) {
    return this.DIMENSION_LABELS[dim] || dim.toUpperCase();
  },

  clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }
};
