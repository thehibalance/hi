/**
 * HI. Grade Content Script
 * 
 * Runs on every web page. Detects the current domain,
 * looks up the HI Grade, and displays a floating badge.
 * 
 * NO AI. Pure DOM manipulation and database lookups.
 */

(async function() {
  'use strict';

  // Logo image URL for panel header
  const HI_LOGO_URL = typeof chrome !== 'undefined' && chrome.runtime ? chrome.runtime.getURL('icons/icon-128.png') : '';
  const HI_LOGO_WHITE_URL = typeof chrome !== 'undefined' && chrome.runtime ? chrome.runtime.getURL('icons/icon-white-128.png') : '';

  // Initialize database
  await HumanDB.init();

  // Get current domain and look up company
  const domain = HumanDB.getCurrentDomain();
  if (!domain) return;

  // Don't show badge on our own site
  if (domain === 'thehibalance.org' || domain === 'www.thehibalance.org') return;

  let company = HumanDB.getByDomain(domain);
  let fromLocal = !!company;

  // ═══ CLOUD CHECK (Phase 2 Track D) ═══
  // Always try the cloud API — if found, use cloud data (fresher).
  // If not found in cloud, fall back to local seed database.
  try {
    const response = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => resolve(null), 4000);
      chrome.runtime.sendMessage(
        { type: 'CLOUD_LOOKUP', domain: domain },
        (resp) => {
          clearTimeout(timeout);
          resolve(resp);
        }
      );
    });

    if (response && response.data) {
      const d = response.data;
      company = {
        name: d.company,
        h: d.D_H, u: d.D_U, m: d.D_M, a: d.D_A, n: d.D_N,
        tags: d.tags || [],
        domains: d.domains || [domain],
        notes: d.notes || '',
        source: 'cloud',
        cloud_grade: d.hi_grade || null,
        cloud_composite: d.composite || null,
        cloud_satire: d.satire || null,
        cloud_hi_balanced: d.hi_balanced || false,
        cloud_hi_balanced_threshold: Math.round(d.hi_balanced_threshold || 62),
        decay_index: d.decay_index || 0,
        decay_level: d.decay_level || 'stable',
        decay_factors: d.decay_factors || [],
        balance_floor: d.balance_floor || false,
        triggering_dimension: d.triggering_dimension || null,
        key_signals: d.key_signals || {},
        genome: d.genome || {},
        data_sources: d.data_sources || [],
      };
    }
  } catch (e) {
    // Cloud unavailable — use local data if we have it
    if (!company) {
      try {
        chrome.runtime.sendMessage({ type: 'QUEUE_LOOKUP', domain: domain });
      } catch (qe) { }
    }
  }

  if (!company) {
    // Show "Request HI Grade" mini badge
    if (document.getElementById('human-score-badge')) return;
    const reqBadge = document.createElement('div');
    reqBadge.id = 'human-score-badge';
    reqBadge.className = 'human-badge human-badge--mini';
    reqBadge.innerHTML = `
      <div class="human-badge__mini" style="padding:0;background:transparent !important;border:none !important;box-shadow:none !important;cursor:pointer">
        <svg width="56" height="66" viewBox="0 0 68 80" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.2))">
          <path d="M24,0 C30,-3 38,-3 44,0 C52,4 54,12 54,20 C54,30 46,38 34,38 C22,38 14,30 14,20 C14,12 16,4 24,0 Z M4,66 C4,48 16,40 34,40 C52,40 64,48 64,66 L64,72 C64,74 62,76 60,76 L8,76 C6,76 4,74 4,72 Z" fill="white" stroke="#1B3A5C" stroke-width="2"/>
          <text x="34" y="24" text-anchor="middle" fill="#1B3A5C" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="12" font-weight="900">HI.</text>
          <text x="34" y="62" text-anchor="middle" fill="#1B3A5C" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="16" font-weight="700">?</text>
        </svg>
      </div>
    `;
    reqBadge.addEventListener('click', () => {
      window.open('https://thehibalance.org/#request&company=' + encodeURIComponent(domain), '_blank');
    });
    document.body.appendChild(reqBadge);
    return;
  }

  // Load user preferences
  const prefs = await loadPreferences();

  // Compute score profile — pass cloud threshold so gates compute correctly
  const cloudThreshold = company.cloud_hi_balanced_threshold || 62;
  const profile = HumanEngine.getProfile(company, cloudThreshold);
  
  // Override composite/satire from cloud when available (cloud is authoritative)
  // But gates are ALWAYS computed locally from actual numbers — never trust stale cloud gates
  if (company.source === 'cloud' && company.cloud_composite) {
    profile.composite = Math.round(company.cloud_composite);
    if (company.cloud_satire) profile.satire = company.cloud_satire;
    
    // Recompute gates with cloud composite (authoritative score)
    const hwFlags = profile.humanwashingFlags || [];
    const recheck = HumanEngine.checkGoldHIGrade(company, profile.composite, hwFlags, cloudThreshold);
    profile.isGold = recheck.gold;
    profile.hiBalanced = recheck.gold;
    profile.goldGates = recheck.gates;
    profile.goldThreshold = recheck.threshold;
    profile.balancedThreshold = recheck.threshold;  // backward compat
    profile.grade = recheck.gold ? "Gold HI Grade" : "Scored";
    profile.scoreColor = recheck.gold ? '#C49B20' : HumanEngine.getScoreColor(profile.composite, recheck.threshold);
    const t = recheck.threshold || 62;
    profile.tier = { color: profile.scoreColor, satire: recheck.gold ? "Passed all 3 gates. Score, balance, and honesty. The math decides, not us." : (profile.composite >= t ? "Almost gold. The humans are still in charge here." : profile.composite >= 42 ? "42 — the minimum for balance. The answer was always 42." : "DON'T PANIC. But maybe start asking questions.") };
  }
  
  // Attach heartbeat data
  profile.decay_index = company.decay_index || 0;
  profile.decay_level = company.decay_level || 'stable';
  profile.decay_factors = company.decay_factors || [];
  profile.balance_floor = company.balance_floor || false;
  profile.triggering_dimension = company.triggering_dimension || null;
  profile.key_signals = company.key_signals || {};
  profile.genome = company.genome || {};
  profile.data_sources = company.data_sources || [];

  // Apply filter
  const filterResult = HumanEngine.applyFilter(company, prefs);

  // Create and inject the floating badge
  createBadge(profile, filterResult, prefs);

})();

/**
 * Load user preferences from chrome.storage or use defaults.
 */
async function loadPreferences() {
  try {
    if (typeof chrome !== 'undefined' && chrome.storage) {
      const stored = await chrome.storage.local.get('userPrefs');
      if (stored.userPrefs) {
        return { ...HumanEngine.DEFAULT_PREFS, ...stored.userPrefs };
      }
    }
  } catch (e) {
    // Fallback to defaults
  }
  return { ...HumanEngine.DEFAULT_PREFS };
}

/**
 * Create the floating score badge on the page.
 */
function createBadge(profile, filterResult, prefs) {
  // Don't create duplicate badges
  if (document.getElementById('human-score-badge')) return;

  const badge = document.createElement('div');
  badge.id = 'human-score-badge';
  badge.className = 'human-badge human-badge--mini'; // Start mini
  if (profile.decay_level === 'critical') badge.className += ' human-badge--critical-pulse';

  // Determine badge state
  const isFiltered = !prefs.masterToggle && !filterResult.passes;
  const isSoftFiltered = isFiltered && prefs.filterMode === 'soft';
  const isHardFiltered = isFiltered && prefs.filterMode === 'strict';

  badge.innerHTML = buildMiniHTML(profile);

  // Store profile data on badge for panel access
  badge._profile = profile;
  badge._filterResult = filterResult;
  badge._prefs = prefs;

  // Click mini pill to open full panel
  badge.addEventListener('click', (e) => {
    if (badge.classList.contains('human-badge--mini')) {
      openFullPanel(profile, filterResult, prefs);
    }
  });

  // Dark mode on mini pill
  try {
    chrome.storage.local.get('darkMode', (r) => {
      if (r.darkMode) { badge.classList.add('human-badge--dark'); }
    });
  } catch(e) {}

  document.body.appendChild(badge);

  // Fetch ecosystem pulse (for panel use later)
  try {
    chrome.runtime.sendMessage({ type: 'PULSE_LOOKUP' }, (pulse) => {
      if (pulse && pulse.pulse) {
        badge._pulse = pulse;
      }
    });
  } catch (e) {}
}

/**
 * Build the mini pill HTML — grade letter + score + warning dot.
 */
function buildMiniHTML(profile) {
  const threshold = profile.balancedThreshold || 62;
  const scoreColor = HumanEngine.getScoreColor(profile.composite, threshold);
  const decayLevel = profile.decay_level || 'stable';
  
  // Human silhouette path
  const silhouette = 'M24,0 C30,-3 38,-3 44,0 C52,4 54,12 54,20 C54,30 46,38 34,38 C22,38 14,30 14,20 C14,12 16,4 24,0 Z M4,66 C4,48 16,40 34,40 C52,40 64,48 64,66 L64,72 C64,74 62,76 60,76 L8,76 C6,76 4,74 4,72 Z';
  
  // Pulse animation based on decay level
  const pulseAnim = {
    'critical': 'pulse-critical 0.8s ease-in-out infinite',
    'warning': 'pulse-critical 1s ease-in-out infinite',
    'watch': 'pulse-watch 1.5s ease-in-out infinite',
    'stable': 'pulse-stable 2.5s ease-in-out infinite',
  };
  const heartAnim = pulseAnim[decayLevel] || pulseAnim['stable'];
  
  // Color mapping
  const colorMap = {
    '#16A34A': '#16A34A',
    '#D97706': '#D97706', 
    '#DC2626': '#DC2626',
  };
  const fillColor = profile.hiBalanced ? '#C49B20' : scoreColor;
  
  if (profile.hiBalanced) {
    // Gold: centered HI. across whole shape, gentle glow
    return `
      <div class="human-badge__mini" style="padding:0;background:transparent !important;border:none !important;box-shadow:none !important">
        <svg width="56" height="66" viewBox="0 0 68 80" style="animation:gold-glow 3s ease-in-out infinite;filter:drop-shadow(0 2px 8px rgba(196,155,32,0.4))">
          <path d="${silhouette}" fill="#C49B20"/>
          <text x="34" y="48" text-anchor="middle" fill="white" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="22" font-weight="900" letter-spacing="-1">HI.</text>
        </svg>
      </div>
    `;
  }
  
  // Regular: score in head, pulsing heart in torso
  return `
    <div class="human-badge__mini" style="padding:0;background:transparent !important;border:none !important;box-shadow:none !important">
      <svg width="56" height="66" viewBox="0 0 68 80" style="filter:drop-shadow(0 2px 8px ${fillColor}40)">
        <path d="${silhouette}" fill="${fillColor}"/>
        <text x="34" y="24" text-anchor="middle" fill="white" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="15" font-weight="900">${profile.composite}</text>
        <g style="animation:${heartAnim};transform-origin:34px 58px">
          <text x="34" y="64" text-anchor="middle" fill="white" font-size="18">♥</text>
        </g>
      </svg>
    </div>
  `;
}

/**
 * Build the badge HTML content.
 */
function buildBadgeHTML(profile, filterResult, prefs, isSoftFiltered) {
  const scoreColor = HumanEngine.getScoreColor(profile.composite, profile.balancedThreshold);
  const tierColor = profile.tier.color;
  const confidenceBadge = profile.confidence === 'estimated' 
    ? '<span class="human-badge__confidence">EST</span>' 
    : '';

  const floorWarning = profile.floorTriggered 
    ? `<div class="human-badge__floor-warning">⚠ Floor rule: ${HumanEngine.getDimensionLabel(profile.floorDimension)} below ${HumanEngine.FLOOR_THRESHOLD}</div>` 
    : '';

  const filterWarning = isSoftFiltered
    ? `<div class="human-badge__filter-warning">Below your thresholds: ${filterResult.failedDimensions.map(d => d === 'floor' ? 'Floor Rule' : d.toUpperCase()).join(', ')}</div>`
    : '';

  const hwFlags = profile.humanwashingFlags.length > 0
    ? `<div class="human-badge__hw-flags">${profile.humanwashingFlags.map(f => `<span class="human-badge__hw-flag" title="${f.detail}">⚑ ${f.name}</span>`).join('')}</div>`
    : '';

  return `
    <div class="human-badge__header">
      <div class="human-badge__grade" style="color: ${tierColor}">
        
      </div>
      <div class="human-badge__meta">
        <div class="human-badge__company">${profile.name} ${confidenceBadge}</div>
        <div class="human-badge__tier" style="color: ${tierColor}">
          HI Grade™ · ${profile.composite}
        </div>
        ${profile.decay_level !== 'stable' && profile.decay_index > 0 ? 
          `<div class="human-badge__header-heartbeat" style="font-size:10px;margin-top:2px;line-height:1.3;color:${{critical:'#DC2626',warning:'#DC2626',watch:'#D97706'}[profile.decay_level]||'#6B7280'}">♥ ${profile.decay_level.charAt(0).toUpperCase()+profile.decay_level.slice(1)} · Decay: ${profile.decay_index}<div style="font-size:9px;opacity:0.8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:200px">${(profile.decay_factors||[]).slice(0,2).join(' · ')}</div></div>` 
          : '<div class="human-badge__header-heartbeat" style="font-size:10px;margin-top:2px;color:#16A34A" id="human-badge-header-pulse">♥ Stable</div>'}
      </div>
      <div class="human-badge__toggle-indicator">▾</div>
    </div>
    <div class="human-badge__details">
      <div class="human-badge__satire">"${profile.tier.satire}"</div>
      <div class="human-badge__dimensions">
        ${buildDimensionBars(profile.dimensions, profile.goldThreshold || profile.balancedThreshold || 62)}
      </div>
      ${profile.tier.cappedFromCertified ? '<div class="human-badge__floor-warning">⚡ Scores 90+ but has not passed all 3 gates.</div>' : ''}
      ${floorWarning}
      ${hwFlags}
      ${profile.balance_floor ? `<div class="human-badge__decay human-badge__decay--warning">⚖ Balance Floor: ${['h','u','m','a','n'].filter(d => (profile.dimensions[d] || 0) < 42).length} Dimension${['h','u','m','a','n'].filter(d => (profile.dimensions[d] || 0) < 42).length > 1 ? 's' : ''} below 42. Floor triggered.</div>` : ''}
      ${profile.decay_level !== 'stable' && profile.decay_index > 0 ? `
        <div class="human-badge__decay human-badge__decay--${profile.decay_level}" style="padding:8px 10px">
          <div style="font-weight:700;font-size:12px">♥ Heartbeat: ${profile.decay_level.charAt(0).toUpperCase() + profile.decay_level.slice(1)} · Decay: ${profile.decay_index}/100</div>
          ${profile.decay_factors.map(f => `<div style="font-size:10px;margin-top:4px;padding-left:14px;position:relative"><span style="position:absolute;left:0">›</span>${f}</div>`).join('')}
        </div>` : ''}
      ${filterWarning}
      ${buildGenomeStrip(profile)}
      <div class="human-badge__pulse" id="human-badge-pulse"></div>
      ${profile.source === 'cloud' ? '<div class="human-badge__source">☁ Live score from thehibalance.org</div>' : '<div class="human-badge__source">📦 Local database</div>'}
      <div class="human-badge__disclaimer">Estimated from public data. Not financial or legal advice.</div>
    </div>
  `;
}

/**
 * Build the dimension bar visualizations.
 */

const GENOME_LABELS = {
  'H.1':'Creative Agency','H.2':'Craft','H.3':'Decision Depth','H.4':'Accountability','H.5':'Displacement',
  'U.1':'Empathy','U.2':'Worker Care','U.3':'Relational','U.4':'Moral Courage','U.5':'Simulated Empathy',
  'U.6_dei':'DEI','U.7_hrc':'HRC',
  'M.1':'Pricing','M.2':'Data Ethics','M.3':'Market','M.4':'CEO','M.5':'Pay Equity',
  'M.6_dei':'DEI','M.7_hrc':'HRC',
  'A.1':'Carbon','A.2':'AI Energy','A.3':'EPA Compliance','A.4':'Resources',
  'N.1':'AI Disclosure','N.2':'Env. Reporting','N.3':'Labor Audit','N.4':'Humanwashing','N.5':'Disclosure'
};

function buildGenomeStrip(profile) {
  const genome = profile.genome || {};
  const dims = ['H','U','M','A','N'];
  const hasGenome = dims.some(d => genome[d] && Object.keys(genome[d].scores || {}).length > 0);
  if (!hasGenome) return '';

  const companyName = encodeURIComponent(profile.name || '');
  let html = '<div style="margin-top:8px;padding:8px 0;border-top:1px solid #EEF1F5;cursor:pointer" onclick="window.open(\'https://thehibalance.org\', \'_blank\')">';
  html += '<div style="font-size:10px;font-weight:700;color:#1B3A5C;letter-spacing:0.5px;margin-bottom:6px">🧬 HUMAN GENOME</div>';

  dims.forEach(d => {
    const dd = genome[d];
    if (!dd || !dd.scores) return;
    const entries = Object.entries(dd.scores).sort((a,b) => a[0].localeCompare(b[0]));
    html += '<div style="display:flex;align-items:center;gap:3px;margin-bottom:3px">';
    html += `<span style="font-size:9px;font-weight:700;color:#1B3A5C;width:10px">${d}</span>`;
    entries.forEach(([key, val]) => {
      val = Math.round(val);
      const bg = HumanEngine.getScoreColor(val, profile.balancedThreshold || profile.goldThreshold);
      const label = GENOME_LABELS[key] || key;
      html += `<div style="flex:1;height:14px;background:${bg};border-radius:2px;position:relative;min-width:12px" title="${label}: ${val}"><span style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:7px;color:white;font-weight:700">${val}</span></div>`;
    });
    html += '</div>';
  });

  html += '<div style="font-size:9px;color:#3A7BBF;margin-top:4px;font-weight:600">View full breakdown on thehibalance.org →</div>';
  html += '<div style="font-size:8px;color:#999;margin-top:2px">Patent Pending · Sub-signal fingerprint</div>';
  html += '</div>';
  return html;
}

function buildDimensionBars(dimensions, threshold) {
  return HumanEngine.DIMENSIONS.map(dim => {
    const score = dimensions[dim] || 0;
    const color = HumanEngine.getScoreColor(score, threshold || 62);
    const label = dim.toUpperCase();
    const fullLabel = HumanEngine.getDimensionLabel(dim);
    return `
      <div class="human-badge__dim human-badge__dim--clickable" data-dim="${dim}" title="Click for details: ${fullLabel}">
        <span class="human-badge__dim-label">${label}</span>
        <div class="human-badge__dim-bar">
          <div class="human-badge__dim-fill" style="width: ${score}%; background: ${color}"></div>
        </div>
        <span class="human-badge__dim-score">${score}</span>
        <span class="human-badge__dim-arrow">›</span>
      </div>
    `;
  }).join('');
}

/**
 * Toggle the badge between compact and expanded states.
 */
function toggleExpanded(badge, profile, filterResult, prefs) {
  badge.classList.toggle('human-badge--expanded');
  badge.classList.remove('human-badge--compact');
}

// ═══ FULL DETAIL PANEL ═══

/**
 * Build human-readable insights for a dimension based on available data.
 */
function buildDimInsights(dim, profile) {
  const ks = profile.key_signals || {};
  const g = profile.genome || {};
  const dd = g[dim.toUpperCase()] || {};
  const srcs = dd.sources || profile.data_sources || [];
  const ins = [];

  if (dim === 'h') {
    if (ks.headcount) ins.push({ t: 'Workforce Size', v: ks.headcount.toLocaleString() + ' employees', n: ks.headcount > 50000 ? 'Large workforce maintained' : 'Smaller workforce' });
    if (ks.revenue_per_employee) ins.push({ t: 'Revenue per Employee', v: '$' + (ks.revenue_per_employee / 1000).toFixed(0) + 'K', n: ks.revenue_per_employee > 2000000 ? 'Very high — suggests heavy automation' : 'Healthy ratio' });
    if (ks.headcount_change_pct != null) ins.push({ t: 'Headcount Change', v: ks.headcount_change_pct + '%', n: ks.headcount_change_pct < -5 ? 'Significant workforce reduction' : ks.headcount_change_pct > 5 ? 'Growing workforce' : 'Stable workforce' });
    if (ks.ai_hiring_ratio != null) ins.push({ t: 'AI Hiring Ratio', v: (ks.ai_hiring_ratio * 100).toFixed(0) + '% of open roles', n: ks.ai_hiring_ratio > 0.35 ? 'AI roles dominate job postings' : 'Balanced hiring mix' });
  } else if (dim === 'u') {
    if (ks.glassdoor_rating) ins.push({ t: 'Employee Rating', v: '★ ' + ks.glassdoor_rating + '/5', n: ks.glassdoor_rating >= 4 ? 'Employees feel valued' : 'Room for improvement' });
    if (ks.dei_score != null) ins.push({ t: 'Disability Inclusion', v: ks.dei_score + '/100', n: ks.dei_score >= 80 ? 'Strong disability inclusion' : 'Opportunity to improve' });
    if (ks.hrc_score != null) ins.push({ t: 'LGBTQ+ Equality', v: ks.hrc_score + '/100', n: ks.hrc_score >= 80 ? 'Strong workplace equality' : 'Opportunity to improve' });
  } else if (dim === 'm') {
    if (ks.ceo_accountability_score != null) ins.push({ t: 'CEO Accountability', v: ks.ceo_accountability_score + '/100', n: ks.ceo_accountability_score < 30 ? 'Leadership accountability critically low' : ks.ceo_accountability_score < 50 ? 'Needs attention' : 'Reasonable accountability' });
    if (ks.epa_violations != null) ins.push({ t: 'EPA Violations', v: ks.epa_violations + ' recorded', n: ks.epa_violations > 5 ? 'Significant regulatory issues' : ks.epa_violations > 0 ? 'Some concerns' : 'Clean record' });
    if (ks.dei_score != null) ins.push({ t: 'DEI Score', v: ks.dei_score + '/100', n: 'Blended into ethical conduct' });
    if (ks.hrc_score != null) ins.push({ t: 'HRC Score', v: ks.hrc_score + '/100', n: 'Blended into ethical conduct' });
  } else if (dim === 'a') {
    if (ks.cdp_climate) ins.push({ t: 'CDP Climate Grade', v: ks.cdp_climate, n: ks.cdp_climate <= 'B' ? 'Strong climate disclosure' : 'Room for improvement' });
    if (ks.epa_violations != null) ins.push({ t: 'Environmental Violations', v: ks.epa_violations + '', n: ks.epa_violations > 0 ? 'Compliance issues detected' : 'No violations' });
  } else if (dim === 'n') {
    if (ks.cdp_climate) ins.push({ t: 'Climate Transparency', v: ks.cdp_climate !== 'N/A' ? 'Disclosed to CDP' : 'Not disclosed', n: ks.cdp_climate !== 'N/A' ? 'Voluntarily reports climate data' : 'Has not disclosed' });
    if (profile.humanwashingFlags && profile.humanwashingFlags.length) ins.push({ t: 'Humanwashing Flags', v: profile.humanwashingFlags.length + ' detected', n: profile.humanwashingFlags[0].detail || '' });
  }

  if (srcs.length) ins.push({ t: 'Data Sources', v: srcs.join(', '), n: 'These sources informed this score' });

  if (!ins.length) return '<div class="human-panel__signal"><span class="human-panel__signal-name" style="color:#888">Score based on industry defaults. More data will refine this.</span></div>';

  return ins.map(x => `
    <div class="human-panel__signal" style="padding:6px 0;border-bottom:1px solid #f0f0f0">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="human-panel__signal-name" style="font-weight:600">${x.t}</span>
        <span style="font-weight:700;font-size:12px;color:${HumanEngine.getScoreColor(profile.dimensions[dim] || 50, profile.balancedThreshold)}">${x.v}</span>
      </div>
      <div style="font-size:10px;color:#888;margin-top:2px">${x.n}</div>
    </div>
  `).join('');
}

const DIM_DESCRIPTIONS = {
  h: {
    name: "Human Consciousness",
    icon: "🧠",
    what: "Measures the depth of genuine human involvement — creative agency, craft, accountability, and whether humans meaningfully shape outcomes or just approve AI output.",
    signals: ["Creative Agency Ratio", "Craft & Tacit Knowledge", "Human Decision Depth", "Accountability Chain", "AI Displacement Trajectory"],
  },
  u: {
    name: "Understanding & Empathy",
    icon: "💙",
    what: "Measures whether the company demonstrates real human empathy toward workers, customers, and communities — or relies on AI-simulated empathy.",
    signals: ["Empathy Expression", "Worker Empathy", "Relational Integrity", "Moral Courage", "Simulated Empathy Detection"],
  },
  m: {
    name: "Moral & Ethical Conduct",
    icon: "⚖️",
    what: "Measures principled action — pricing ethics, data ethics, market behavior, CEO accountability, and leadership pay equity. Starts at 100, deducted for violations.",
    signals: ["Pricing Ethics", "Data Ethics", "Market Ethics", "CEO Accountability", "Leadership Pay Equity"],
  },
  a: {
    name: "Alive & Environmental",
    icon: "🌍",
    what: "Measures true environmental cost including the hidden footprint of AI infrastructure — energy, water, land use, and hardware lifecycle.",
    signals: ["Energy Score", "Water Score", "Land & Habitat", "Hardware Lifecycle"],
  },
  n: {
    name: "Natural Transparency",
    icon: "🔍",
    what: "Measures whether the company is genuinely open about AI usage, environmental impact, and labor practices — or hiding behind humanwashing.",
    signals: ["AI Disclosure Quality", "Environmental Reporting", "Labor Auditability", "Humanwashing Detection", "Disclosure Completeness"],
  },
};

/**
 * Open the combined full panel — all data in one view.
 */
function openFullPanel(profile, filterResult, prefs) {
  try {
  const existing = document.getElementById('human-detail-panel');
  if (existing) existing.remove();

  const panel = document.createElement('div');
  panel.id = 'human-detail-panel';
  panel.className = 'human-panel';

  const scoreColor = profile.hiBalanced ? '#C49B20' : HumanEngine.getScoreColor(profile.composite, profile.balancedThreshold);
  const pulseColors = {'critical':'#DC2626','warning':'#DC2626','watch':'#D97706','stable':'#16A34A'};
  const pulseColor = pulseColors[profile.decay_level] || '#16A34A';
  const pulseDotHTML = profile.decay_index > 0 
    ? `<span style="font-size:12px;font-weight:700;color:${pulseColor};margin-left:8px${profile.decay_level==='critical'||profile.decay_level==='warning'?';animation:blink 2s infinite':''}">♥${profile.decay_index}</span>`
    : `<span style="font-size:12px;color:#16A34A;margin-left:8px">♥</span>`;

  // Build all dimensions with inline insights
  const allDimsHTML = HumanEngine.DIMENSIONS.map(d => {
    const s = profile.dimensions[d] || 0;
    const c = HumanEngine.getScoreColor(s, profile.balancedThreshold);
    const info = DIM_DESCRIPTIONS[d];
    const insights = buildDimInsights(d, profile);
    return `
      <div style="margin-bottom:12px">
        <div class="human-panel__dim-row" style="cursor:pointer" onclick="var det=this.nextElementSibling;det.style.display=det.style.display==='block'?'none':'block'">
          <span class="human-panel__row-icon">${info.icon}</span>
          <span class="human-panel__row-label">${d.toUpperCase()}</span>
          <div class="human-panel__row-bar">
            <div class="human-panel__row-fill" style="width: ${s}%; background: ${c}"></div>
          </div>
          <span class="human-panel__row-score" style="color: ${c}">${s}</span>
          <span style="font-size:10px;color:#999;margin-left:4px">▾</span>
        </div>
        <div style="display:none;padding:8px 12px;background:#f8f9fa;border-radius:0 0 8px 8px;margin-top:-2px">
          <div style="font-size:11px;color:#555;margin-bottom:6px">${info.what}</div>
          ${insights}
        </div>
      </div>`;
  }).join('');

  // Genome strip
  const genomeHTML = buildGenomeStrip(profile);

  // Heartbeat/decay section
  let decayHTML = '';
  if (profile.decay_level !== 'stable' && profile.decay_index > 0) {
    const decayColors = {'critical':'#DC2626','warning':'#DC2626','watch':'#D97706','stable':'#16A34A'};
    const dc = decayColors[profile.decay_level] || '#6B7280';
    decayHTML = `
      <div style="background:${dc}10;border:1px solid ${dc}30;border-radius:8px;padding:10px 12px;margin-top:8px">
        <div style="font-weight:700;font-size:12px;color:${dc}">♥ ${profile.decay_level.charAt(0).toUpperCase() + profile.decay_level.slice(1)} · Decay: ${profile.decay_index}/100</div>
        ${profile.decay_factors.map(f => `<div style="font-size:10px;margin-top:4px;padding-left:14px;position:relative;color:#444"><span style="position:absolute;left:0">›</span>${f}</div>`).join('')}
      </div>`;
  }

  // Balance floor
  let floorHTML = '';
  if (profile.balance_floor) {
    floorHTML = `<div style="background:#FFF7ED;border:1px solid #FDBA74;border-radius:8px;padding:8px 12px;margin-top:8px;font-size:11px;color:#9A3412">⚖ Balance Floor: ${(() => { const bc = ['h','u','m','a','n'].filter(d => (profile.dimensions[d]||0) < 42).length; return bc + ' Dimension' + (bc > 1 ? 's' : '') + ' below 42. Floor triggered.'; })()}</div>`;
  }

  // Pulse
  const badge = document.getElementById('human-score-badge');
  const pulse = badge ? badge._pulse : null;
  let pulseHTML = '';
  if (pulse && pulse.pulse) {
    const pc = { healthy: '#16A34A', elevated: '#D97706', stressed: '#DC2626', critical: '#DC2626' };
    const pColor = pc[pulse.pulse] || '#6B7280';
    pulseHTML = `<div style="font-size:11px;color:${pColor};margin-top:8px;text-align:center">♥ Ecosystem: <strong>${pulse.pulse.toUpperCase()}</strong> · ${pulse.alerts_count || 0} alerts</div>`;
  }

  panel.innerHTML = `
    <div class="human-panel__header">
      <div class="human-panel__back" id="panelBack" style="visibility:hidden">←</div>
      <div class="human-panel__title"><img src="${chrome.runtime.getURL('icons/icon-128.png')}" style="height:40px;width:auto;border-radius:6px" alt="HI."></div>
      <div class="human-panel__close" id="panelClose">✕</div>
    </div>

    <div class="human-panel__company">
      <div class="human-panel__grade" style="${profile.hiBalanced ? 'background:#C49B20;color:white;border-radius:50%;width:64px;height:64px;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 0 16px rgba(196,155,32,0.3);font-size:36px' : 'color:'+scoreColor+';font-size:36px'}">${profile.hiBalanced ? '<img src="' + chrome.runtime.getURL('icons/icon-white-128.png') + '" style="height:36px;width:auto" alt="HI.">' : profile.composite}</div>
      <div>
        <div class="human-panel__name">${profile.name}</div>
        <div class="human-panel__tier" style="color: ${scoreColor}">HI Grade™${pulseDotHTML}</div>
        <div class="human-panel__brand">Think human intelligence.</div>
      </div>
    </div>
    ${profile.hiBalanced ? '<div style="padding:4px 16px;font-size:11px;color:#C49B20;font-weight:600">HI. All 3 gates passed</div><div style="padding:2px 16px;font-size:20px;font-weight:900;color:#C49B20">'+profile.composite+'</div>' : ''}
    ${profile.tier.satire ? `<div class="human-panel__satire">"${profile.tier.satire}"</div>` : ''}

    ${(() => {
      const gates = profile.goldGates || {};
      const total = Object.keys(gates).length || 3;
      const passed = Object.values(gates).filter(v => v).length;
      const threshold = Math.round(profile.goldThreshold || profile.balancedThreshold || 62);
      const gc = (k,v) => '<div style="font-size:10px;padding:2px 0;color:' + (v ? '#16A34A' : '#DC2626') + '">' + (v ? '✓' : '✗') + ' ' + k + '</div>';
      return '<div style="padding:8px 16px;margin-top:4px">' +
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px"><span style="font-size:11px;font-weight:700;color:#1B3A5C">' + passed + '/' + total + ' GATES</span><div style="flex:1;height:4px;background:#EEF1F5;border-radius:2px"><div style="height:100%;width:' + (passed/total*100) + '%;background:' + (passed === total ? '#C49B20' : '#1B3A5C') + ';border-radius:2px"></div></div></div>' +
        '<div style="font-size:9px;font-weight:700;color:#1B3A5C;letter-spacing:1px;margin-bottom:4px">📊 SCORE</div>' +
        gc('Composite ≥ ' + threshold, gates.score) +
        '<div style="font-size:9px;font-weight:700;color:#C49B20;letter-spacing:1px;margin:6px 0 4px">⚖ BALANCE</div>' +
        gc('All dimensions ≥ 42', gates.balance) +
        '<div style="font-size:9px;font-weight:700;color:#16A34A;letter-spacing:1px;margin:6px 0 4px">🔒 HONESTY</div>' +
        gc('No Humanwashing™ flags', gates.honesty) +
        gc('Algorithmic Harm Index™ < 30', gates.honesty) +
        '</div>';
    })()}

    <div style="padding:0 16px">
      <div style="font-size:11px;font-weight:700;color:#1B3A5C;letter-spacing:0.5px;margin-bottom:8px">DIMENSIONS</div>
      ${allDimsHTML}
    </div>

    ${floorHTML ? `<div style="padding:0 16px">${floorHTML}</div>` : ''}
    ${decayHTML ? `<div style="padding:0 16px">${decayHTML}</div>` : ''}

    <div style="padding:0 16px">
      ${genomeHTML}
    </div>

    ${pulseHTML ? `<div style="padding:0 16px">${pulseHTML}</div>` : ''}

    <div style="padding:0 16px;margin-top:8px">
      ${profile.source === 'cloud' ? '<div style="font-size:9px;color:#999;text-align:center">☁ Live score from thehibalance.org</div>' : '<div style="font-size:9px;color:#999;text-align:center">📦 Local database</div>'}
    </div>

    <div class="human-panel__toggle-section">
      <div class="human-panel__toggle-row">
        <div>
          <div class="human-panel__toggle-label" id="panelToggleLabel">Full View</div>
          <div class="human-panel__toggle-sub" id="panelToggleSub">Showing all companies with scores</div>
        </div>
        <label class="human-panel__switch">
          <input type="checkbox" id="panelMasterToggle" checked>
          <span class="human-panel__switch-slider"></span>
        </label>
      </div>
    </div>

    <div class="human-panel__equalizer" id="panelEqualizer2" style="display:none">
      <div class="human-panel__eq-header">
        <span class="human-panel__section-title">Dimension Thresholds</span>
        <button class="human-panel__eq-mode" id="panelFilterMode2">Soft</button>
      </div>
      ${HumanEngine.DIMENSIONS.map(d => {
        const info = DIM_DESCRIPTIONS[d];
        return `
          <div class="human-panel__eq-slider">
            <span class="human-panel__eq-icon">${info.icon}</span>
            <span class="human-panel__eq-label">${d.toUpperCase()}</span>
            <input type="range" class="human-panel__eq-input" id="panelSlider2_${d}" min="0" max="100" value="0">
            <span class="human-panel__eq-value" id="panelValue2_${d}">0</span>
          </div>
        `;
      }).join('')}
    </div>

    <div class="human-panel__connection" id="panelConnection">
      <span class="human-panel__connection-dot" id="panelConnDot">●</span>
      <span id="panelConnText">Checking connection...</span>
    </div>

    <div style="padding:12px 16px;text-align:center">
      <a href="https://thehibalance.org" target="_blank" style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:var(--navy,#1B3A5C);color:white;border-radius:10px;font-size:12px;font-weight:700;text-decoration:none;letter-spacing:0.5px">📱 Get the App · thehibalance.org</a>
    </div>

    <div class="human-panel__footer">
      <div>Think human intelligence.</div>
      <div class="human-panel__footer-sub">thehibalance.org · The HI Balance</div>
    </div>

    <div class="human-panel__disclaimer">
      Gold HI Grade threshold (currently ${Math.round(profile.balancedThreshold || 62)}) is adaptive — recalculated quarterly as mean + 2 standard deviations. 3 gates: Score, Balance, Honesty. Scores are estimated from public data. Not financial or legal advice.
    </div>
  `;

  document.body.appendChild(panel);

  // Connection status
  (async () => {
    const dot = document.getElementById('panelConnDot');
    const text = document.getElementById('panelConnText');
    if (!dot || !text) return;
    try {
      const resp = await new Promise((resolve) => {
        chrome.runtime.sendMessage({ type: 'CHECK_CONNECTION' }, (r) => resolve(r));
      });
      if (resp && resp.connected) {
        dot.style.color = '#1a7a3a';
        text.textContent = `Connected · ${resp.companies||0} companies · API live`;
      } else {
        dot.style.color = '#D97706';
        text.textContent = 'Offline · Using local database';
      }
    } catch (e) {
      dot.style.color = '#D97706';
      text.textContent = 'Offline · Using local database';
    }
  })();

  // Close panel
  document.getElementById('panelClose').addEventListener('click', () => panel.remove());

  // Master toggle
  const panelToggle = document.getElementById('panelMasterToggle');
  const panelToggleLabel = document.getElementById('panelToggleLabel');
  const panelToggleSub = document.getElementById('panelToggleSub');

  if (panelToggle && panelToggleLabel && panelToggleSub) {
  loadPreferences().then(currentPrefs => {
    panelToggle.checked = currentPrefs.masterToggle;
    panelToggleLabel.textContent = currentPrefs.masterToggle ? 'Full View' : 'AI Filter Active';
    panelToggleSub.textContent = currentPrefs.masterToggle ? 'Showing all companies with scores' : 'Filtering by your thresholds';
    const eq = document.getElementById('panelEqualizer2');
    if (eq) eq.style.display = currentPrefs.masterToggle ? 'none' : 'block';
    // Load slider values
    HumanEngine.DIMENSIONS.forEach(d => {
      const slider = document.getElementById('panelSlider2_' + d);
      const valEl = document.getElementById('panelValue2_' + d);
      if (slider && currentPrefs.thresholds && currentPrefs.thresholds[d] !== undefined) {
        slider.value = currentPrefs.thresholds[d];
        if (valEl) valEl.textContent = currentPrefs.thresholds[d];
      }
      if (slider) {
        slider.addEventListener('input', async () => {
          if (valEl) valEl.textContent = slider.value;
          const p = await loadPreferences();
          if (!p.thresholds) p.thresholds = {};
          p.thresholds[d] = parseInt(slider.value);
          try { chrome.storage.sync.set(p); } catch(e) {}
        });
      }
    });
    // Filter mode button
    const modeBtn = document.getElementById('panelFilterMode2');
    if (modeBtn) {
      modeBtn.textContent = currentPrefs.filterMode === 'strict' ? 'Strict' : 'Soft';
      modeBtn.addEventListener('click', async () => {
        const p = await loadPreferences();
        p.filterMode = p.filterMode === 'strict' ? 'soft' : 'strict';
        modeBtn.textContent = p.filterMode === 'strict' ? 'Strict' : 'Soft';
        try { chrome.storage.sync.set(p); } catch(e) {}
      });
    }
  });

  panelToggle.addEventListener('change', async () => {
    const currentPrefs = await loadPreferences();
    currentPrefs.masterToggle = panelToggle.checked;
    panelToggleLabel.textContent = panelToggle.checked ? 'Full View' : 'AI Filter Active';
    panelToggleSub.textContent = panelToggle.checked ? 'Showing all companies with scores' : 'Filtering by your thresholds';
    const eq = document.getElementById('panelEqualizer2');
    if (eq) eq.style.display = panelToggle.checked ? 'none' : 'block';
    try { chrome.storage.sync.set(currentPrefs); } catch (e) {}
  });
  } // end if (panelToggle && panelToggleLabel && panelToggleSub)
  } catch(err) { console.error('HI. panel error:', err); }
}

/**
 * Open the full detail panel — injected into the page.
 */
function openDetailPanel(profile, dim) {
  // Remove existing panel
  const existing = document.getElementById('human-detail-panel');
  if (existing) existing.remove();

  const panel = document.createElement('div');
  panel.id = 'human-detail-panel';
  panel.className = 'human-panel';

  const dimInfo = DIM_DESCRIPTIONS[dim];
  const dimScore = profile.dimensions[dim] || 0;
  const dimColor = HumanEngine.getScoreColor(dimScore, profile.balancedThreshold);
  const tierColor = profile.tier.color;

  panel.innerHTML = `
    <div class="human-panel__header">
      <div class="human-panel__back" id="panelBack">← Back</div>
      <div class="human-panel__title"><img src="${chrome.runtime.getURL('icons/icon-128.png')}" style="height:40px;width:auto;border-radius:6px" alt="HI."></div>
      <div class="human-panel__close" id="panelClose">✕</div>
    </div>

    <div class="human-panel__company">
      <div class="human-panel__grade" style="${profile.hiBalanced ? 'background:#C49B20;color:white;border-radius:50%;width:64px;height:64px;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 0 16px rgba(196,155,32,0.3);font-size:36px' : 'color:'+scoreColor+';font-size:36px'}">${profile.hiBalanced ? '<img src="' + chrome.runtime.getURL('icons/icon-white-128.png') + '" style="height:36px;width:auto" alt="HI.">' : profile.composite}</div>
      <div>
        <div class="human-panel__name">${profile.name}</div>
        <div class="human-panel__tier" style="color: ${scoreColor}">HI Grade™${pulseDotHTML}</div>
        <div class="human-panel__brand">Think human intelligence.</div>
      </div>
    </div>
    ${profile.tier.satire ? `<div class="human-panel__satire">"${profile.tier.satire}"</div>` : ''}

    <div class="human-panel__dim-detail">
      <div class="human-panel__dim-header">
        <span class="human-panel__dim-icon">${dimInfo.icon}</span>
        <span class="human-panel__dim-name">${dim.toUpperCase()} — ${dimInfo.name}</span>
        <span class="human-panel__dim-score" style="color: ${dimColor}">${dimScore}</span>
      </div>
      <div class="human-panel__dim-bar-large">
        <div class="human-panel__dim-fill-large" style="width: ${dimScore}%; background: ${dimColor}"></div>
      </div>
      <div class="human-panel__dim-desc">${dimInfo.what}</div>
      <div class="human-panel__signals-title">How This Score Was Formed</div>
      <div class="human-panel__signals">
        ${buildDimInsights(dim, profile)}
      </div>
    </div>

    <div class="human-panel__all-dims">
      <div class="human-panel__section-title">All Dimensions</div>
      ${HumanEngine.DIMENSIONS.map(d => {
        const s = profile.dimensions[d] || 0;
        const c = HumanEngine.getScoreColor(s, profile.balancedThreshold);
        const info = DIM_DESCRIPTIONS[d];
        const active = d === dim ? ' human-panel__dim-row--active' : '';
        return `
          <div class="human-panel__dim-row${active}" data-panel-dim="${d}">
            <span class="human-panel__row-icon">${info.icon}</span>
            <span class="human-panel__row-label">${d.toUpperCase()}</span>
            <div class="human-panel__row-bar">
              <div class="human-panel__row-fill" style="width: ${s}%; background: ${c}"></div>
            </div>
            <span class="human-panel__row-score" style="color: ${c}">${s}</span>
          </div>
        `;
      }).join('')}
    </div>

    <div class="human-panel__toggle-section">
      <div class="human-panel__toggle-row">
        <div>
          <div class="human-panel__toggle-label" id="panelToggleLabel">Full View</div>
          <div class="human-panel__toggle-sub" id="panelToggleSub">Showing all companies with scores</div>
        </div>
        <label class="human-panel__switch">
          <input type="checkbox" id="panelMasterToggle" checked>
          <span class="human-panel__switch-slider"></span>
        </label>
      </div>
    </div>

    <div class="human-panel__equalizer" id="panelEqualizer">
      <div class="human-panel__eq-header">
        <span class="human-panel__section-title">Dimension Thresholds</span>
        <button class="human-panel__eq-mode" id="panelFilterMode">Soft</button>
      </div>
      ${HumanEngine.DIMENSIONS.map(d => {
        const info = DIM_DESCRIPTIONS[d];
        return `
          <div class="human-panel__eq-slider">
            <span class="human-panel__eq-icon">${info.icon}</span>
            <span class="human-panel__eq-label">${d.toUpperCase()}</span>
            <input type="range" class="human-panel__eq-input" id="panelSlider_${d}" min="0" max="100" value="0">
            <span class="human-panel__eq-value" id="panelValue_${d}">0</span>
          </div>
        `;
      }).join('')}
    </div>

    <div class="human-panel__search-section">
      <div class="human-panel__section-title">Search Companies</div>
      <input type="text" class="human-panel__search" id="panelSearch" placeholder="Search companies...">
      <div class="human-panel__results" id="panelResults"></div>
    </div>

    <div class="human-panel__connection" id="panelConnection">
      <span class="human-panel__connection-dot" id="panelConnDot">●</span>
      <span id="panelConnText">Checking connection...</span>
    </div>

    <div class="human-panel__footer">
      <div>Think human intelligence.</div>
      <div class="human-panel__footer-sub">thehibalance.org · The HI Balance</div>
    </div>

    <div class="human-panel__disclaimer">
      Gold HI Grade threshold is adaptive — recalculated quarterly as mean + 2 standard deviations. As companies improve, the bar rises. 3 gates: Score, Balance, Honesty. Scores are estimated from public data. Not financial or legal advice.
    </div>
  `;

  document.body.appendChild(panel);

  // ═══ CONNECTION STATUS ═══
  (async () => {
    const dot = document.getElementById('panelConnDot');
    const text = document.getElementById('panelConnText');
    if (!dot || !text) return;

    try {
      const resp = await new Promise((resolve) => {
        chrome.runtime.sendMessage({ type: 'CHECK_CONNECTION' }, (r) => resolve(r));
      });

      if (resp && resp.connected) {
        dot.style.color = '#1a7a3a';
        text.textContent = `Connected · ${resp.companies||0} companies · API live`;
      } else {
        dot.style.color = '#D97706';
        text.textContent = 'Offline · Using local database (206 companies)';
      }
    } catch (e) {
      dot.style.color = '#D97706';
      text.textContent = 'Offline · Using local database (206 companies)';
    }
  })();

  // Event listeners
  document.getElementById('panelClose').addEventListener('click', () => panel.remove());
  document.getElementById('panelBack').addEventListener('click', () => panel.remove());

  // ═══ MASTER TOGGLE ═══
  const panelToggle = document.getElementById('panelMasterToggle');
  const panelToggleLabel = document.getElementById('panelToggleLabel');
  const panelToggleSub = document.getElementById('panelToggleSub');
  const panelEqualizer = document.getElementById('panelEqualizer');

  // Load current prefs
  loadPreferences().then(currentPrefs => {
    panelToggle.checked = currentPrefs.masterToggle;
    updatePanelToggleUI(currentPrefs.masterToggle);
    updatePanelEqualizerState(currentPrefs.masterToggle);

    // Set current filter mode
    const modeBtn = document.getElementById('panelFilterMode');
    modeBtn.textContent = currentPrefs.filterMode === 'strict' ? 'Strict' : 'Soft';
    if (currentPrefs.filterMode === 'strict') modeBtn.classList.add('human-panel__eq-mode--strict');

    // Set current slider values
    HumanEngine.DIMENSIONS.forEach(d => {
      const slider = document.getElementById(`panelSlider_${d}`);
      const valueEl = document.getElementById(`panelValue_${d}`);
      if (slider && valueEl) {
        slider.value = currentPrefs.thresholds[d] || 0;
        valueEl.textContent = slider.value;
      }
    });

    // Toggle handler
    panelToggle.addEventListener('change', async () => {
      currentPrefs.masterToggle = panelToggle.checked;
      updatePanelToggleUI(currentPrefs.masterToggle);
      updatePanelEqualizerState(currentPrefs.masterToggle);
      await savePanelPrefs(currentPrefs);
    });

    // Filter mode handler
    modeBtn.addEventListener('click', async () => {
      currentPrefs.filterMode = currentPrefs.filterMode === 'soft' ? 'strict' : 'soft';
      modeBtn.textContent = currentPrefs.filterMode === 'strict' ? 'Strict' : 'Soft';
      modeBtn.classList.toggle('human-panel__eq-mode--strict');
      await savePanelPrefs(currentPrefs);
    });

    // Slider handlers
    HumanEngine.DIMENSIONS.forEach(d => {
      const slider = document.getElementById(`panelSlider_${d}`);
      const valueEl = document.getElementById(`panelValue_${d}`);
      if (slider) {
        slider.addEventListener('input', async () => {
          valueEl.textContent = slider.value;
          currentPrefs.thresholds[d] = parseInt(slider.value);
          await savePanelPrefs(currentPrefs);
        });
      }
    });
  });

  // Click other dimension rows to switch
  panel.querySelectorAll('[data-panel-dim]').forEach(row => {
    row.addEventListener('click', () => {
      panel.remove();
      openDetailPanel(profile, row.dataset.panelDim);
    });
  });

  // Search
  const searchInput = document.getElementById('panelSearch');
  const searchResults = document.getElementById('panelResults');

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim();
    if (q.length < 2) { searchResults.innerHTML = ''; return; }

    const results = HumanDB.searchByName(q);
    searchResults.innerHTML = results.slice(0, 6).map(c => {
      const p = HumanEngine.getProfile(c);
      const col = HumanEngine.getScoreColor(p.composite, p.balancedThreshold);
      return `
        <div class="human-panel__result">
          <span class="human-panel__result-score" style="color: ${col}">${p.composite}</span>
          <span class="human-panel__result-name">${p.name}</span>
          <span class="human-panel__result-grade" style="color: ${p.tier.color}">${p.grade}</span>
        </div>
      `;
    }).join('') || '<div class="human-panel__result"><span class="human-panel__result-name" style="color:#aaa">No results</span></div>';
  });

  // Click outside to close
  panel.addEventListener('click', (e) => {
    if (e.target === panel) panel.remove();
  });
}

/**
 * Attach dimension click handlers to the badge.
 */
function attachDimClickHandlers(badge, profile) {
  badge.querySelectorAll('.human-badge__dim--clickable').forEach(el => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      openDetailPanel(profile, el.dataset.dim);
    });
  });
}

/**
 * Panel toggle UI helpers.
 */
function updatePanelToggleUI(isFullView) {
  const label = document.getElementById('panelToggleLabel');
  const sub = document.getElementById('panelToggleSub');
  if (!label || !sub) return;
  if (isFullView) {
    label.textContent = 'Full View';
    sub.textContent = 'Showing all companies with scores';
  } else {
    label.textContent = 'AI Filter Active';
    sub.textContent = 'Filtering by your thresholds';
  }
}

function updatePanelEqualizerState(isFullView) {
  const eq = document.getElementById('panelEqualizer');
  if (!eq) return;
  if (isFullView) {
    eq.classList.add('human-panel__equalizer--disabled');
  } else {
    eq.classList.remove('human-panel__equalizer--disabled');
  }
}

async function savePanelPrefs(prefs) {
  try {
    if (typeof chrome !== 'undefined' && chrome.storage) {
      await chrome.storage.local.set({ userPrefs: prefs });
    }
  } catch (e) {}
}
