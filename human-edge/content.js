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

  // Initialize database
  await HumanDB.init();

  // Get current domain and look up company
  const domain = HumanDB.getCurrentDomain();
  if (!domain) return;

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

  if (!company) return; // Not in local DB or cloud

  // Load user preferences
  const prefs = await loadPreferences();

  // Compute score profile
  const profile = HumanEngine.getProfile(company);
  
  // Override with cloud grade/composite when available (cloud is authoritative)
  if (company.source === 'cloud' && company.cloud_grade) {
    profile.grade = company.cloud_grade;
    profile.composite = company.cloud_composite || profile.composite;
    if (company.cloud_satire) profile.satire = company.cloud_satire;
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
  const tierColor = profile.tier.color;
  const hasWarning = profile.decay_level === 'critical' || profile.decay_level === 'warning';
  const hasDecay = profile.decay_level !== 'stable' && profile.decay_index > 0;
  const hasFloor = profile.balance_floor;
  
  let warningDot = '';
  if (hasWarning) {
    warningDot = `<span class="human-badge__mini-dot" style="background:#DC2626"></span>`;
  } else if (hasDecay) {
    warningDot = `<span class="human-badge__mini-dot" style="background:#D97706"></span>`;
  } else if (hasFloor) {
    warningDot = `<span class="human-badge__mini-dot" style="background:#EA580C"></span>`;
  }
  
  return `
    <div class="human-badge__mini">
      <span class="human-badge__mini-grade" style="color:${tierColor}">${profile.letter}</span>
      <span class="human-badge__mini-score" style="color:${tierColor}">${profile.composite}</span>
      ${warningDot}
    </div>
  `;
}

/**
 * Build the badge HTML content.
 */
function buildBadgeHTML(profile, filterResult, prefs, isSoftFiltered) {
  const scoreColor = HumanEngine.getScoreColor(profile.composite);
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
        ${profile.letter}
      </div>
      <div class="human-badge__meta">
        <div class="human-badge__company">${profile.name} ${confidenceBadge}</div>
        <div class="human-badge__tier" style="color: ${tierColor}">
          HI Grade: ${profile.grade} · ${profile.composite}
        </div>
        ${profile.decay_level !== 'stable' && profile.decay_index > 0 ? 
          `<div class="human-badge__header-heartbeat" style="font-size:10px;margin-top:2px;line-height:1.3;color:${{critical:'#DC2626',warning:'#D97706',watch:'#EA580C'}[profile.decay_level]||'#6B7280'}">♥ ${profile.decay_level.charAt(0).toUpperCase()+profile.decay_level.slice(1)} · Decay: ${profile.decay_index}<div style="font-size:9px;opacity:0.8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:200px">${(profile.decay_factors||[]).slice(0,2).join(' · ')}</div></div>` 
          : '<div class="human-badge__header-heartbeat" style="font-size:10px;margin-top:2px;color:#16A34A" id="human-badge-header-pulse">♥ Stable</div>'}
      </div>
      <div class="human-badge__toggle-indicator">▾</div>
    </div>
    <div class="human-badge__details">
      <div class="human-badge__satire">"${profile.tier.satire}"</div>
      <div class="human-badge__dimensions">
        ${buildDimensionBars(profile.dimensions)}
      </div>
      ${profile.tier.cappedFromCertified ? '<div class="human-badge__floor-warning">⚡ Scores 90+ but not HI Certified. Displayed as A.</div>' : ''}
      ${floorWarning}
      ${hwFlags}
      ${profile.balance_floor ? `<div class="human-badge__decay human-badge__decay--warning">⚖ Balance Floor: ${profile.triggering_dimension ? profile.triggering_dimension.toUpperCase() : 'a dimension'} below 42. Grade capped at C.</div>` : ''}
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

  let html = '<div style="margin-top:8px;padding:8px 0;border-top:1px solid #EEF1F5">';
  html += '<div style="font-size:10px;font-weight:700;color:#1B3A5C;letter-spacing:0.5px;margin-bottom:6px">🧬 HUMAN GENOME</div>';

  dims.forEach(d => {
    const dd = genome[d];
    if (!dd || !dd.scores) return;
    const entries = Object.entries(dd.scores).sort((a,b) => a[0].localeCompare(b[0]));
    html += '<div style="display:flex;align-items:center;gap:3px;margin-bottom:3px">';
    html += `<span style="font-size:9px;font-weight:700;color:#1B3A5C;width:10px">${d}</span>`;
    entries.forEach(([key, val]) => {
      val = Math.round(val);
      const bg = val >= 80 ? '#2e8b57' : val >= 60 ? '#4a90d9' : val >= 42 ? '#E07020' : '#6B7280';
      const label = GENOME_LABELS[key] || key;
      html += `<div style="flex:1;height:14px;background:${bg};border-radius:2px;position:relative;min-width:12px;cursor:help" title="${label}: ${val}"><span style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:7px;color:white;font-weight:700">${val}</span></div>`;
    });
    html += '</div>';
  });

  html += '<div style="font-size:8px;color:#999;margin-top:2px">Patent Pending · Sub-signal fingerprint</div>';
  html += '</div>';
  return html;
}

function buildDimensionBars(dimensions) {
  return HumanEngine.DIMENSIONS.map(dim => {
    const score = dimensions[dim] || 0;
    const color = HumanEngine.getScoreColor(score);
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
        <span style="font-weight:700;font-size:12px;color:${HumanEngine.getScoreColor(profile.dimensions[dim] || 50)}">${x.v}</span>
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
  const existing = document.getElementById('human-detail-panel');
  if (existing) existing.remove();

  const panel = document.createElement('div');
  panel.id = 'human-detail-panel';
  panel.className = 'human-panel';

  const tierColor = profile.tier.color;
  const decayColors = { critical: '#DC2626', warning: '#D97706', watch: '#EA580C', stable: '#16A34A' };
  
  // Build all dimensions with inline insights
  const allDimsHTML = HumanEngine.DIMENSIONS.map(d => {
    const s = profile.dimensions[d] || 0;
    const c = HumanEngine.getScoreColor(s);
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
    floorHTML = `<div style="background:#FFF7ED;border:1px solid #FDBA74;border-radius:8px;padding:8px 12px;margin-top:8px;font-size:11px;color:#9A3412">⚖ Balance Floor: ${profile.triggering_dimension ? profile.triggering_dimension.toUpperCase() : 'a dimension'} below 42. Grade capped at C.</div>`;
  }

  // Pulse
  const badge = document.getElementById('human-score-badge');
  const pulse = badge ? badge._pulse : null;
  let pulseHTML = '';
  if (pulse && pulse.pulse) {
    const pc = { healthy: '#16A34A', elevated: '#D97706', stressed: '#EA580C', critical: '#DC2626' };
    const pColor = pc[pulse.pulse] || '#6B7280';
    pulseHTML = `<div style="font-size:11px;color:${pColor};margin-top:8px;text-align:center">♥ Ecosystem: <strong>${pulse.pulse.toUpperCase()}</strong> · ${pulse.alerts_count || 0} alerts</div>`;
  }

  panel.innerHTML = `
    <div class="human-panel__header">
      <div class="human-panel__back" id="panelBack" style="visibility:hidden">←</div>
      <div class="human-panel__title">HI.</div>
      <div class="human-panel__close" id="panelClose">✕</div>
    </div>

    <div class="human-panel__company">
      <div class="human-panel__grade" style="color: ${tierColor}">${profile.letter}</div>
      <div>
        <div class="human-panel__name">${profile.name}</div>
        <div class="human-panel__tier" style="color: ${tierColor}">HI Grade: ${profile.grade} · ${profile.composite}</div>
        <div class="human-panel__brand">Find the HI balance.</div>
      </div>
    </div>
    <div class="human-panel__satire">"${profile.tier.satire}"</div>

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

    <div class="human-panel__connection" id="panelConnection">
      <span class="human-panel__connection-dot" id="panelConnDot">●</span>
      <span id="panelConnText">Checking connection...</span>
    </div>

    <div class="human-panel__footer">
      <div>Find the HI balance.</div>
      <div class="human-panel__footer-sub">thehibalance.org · The Deep Thought Foundation</div>
    </div>

    <div class="human-panel__disclaimer">
      HI Grades are estimated from public data. Not financial or legal advice. Patent pending.
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
        text.textContent = `Connected · ${resp.companies} companies · API live`;
      } else {
        dot.style.color = '#E07020';
        text.textContent = 'Offline · Using local database';
      }
    } catch (e) {
      dot.style.color = '#E07020';
      text.textContent = 'Offline · Using local database';
    }
  })();

  // Close panel
  document.getElementById('panelClose').addEventListener('click', () => panel.remove());

  // Master toggle
  const panelToggle = document.getElementById('panelMasterToggle');
  const panelToggleLabel = document.getElementById('panelToggleLabel');
  const panelToggleSub = document.getElementById('panelToggleSub');

  loadPreferences().then(currentPrefs => {
    panelToggle.checked = currentPrefs.masterToggle;
    panelToggleLabel.textContent = currentPrefs.masterToggle ? 'Full View' : 'AI Filter Active';
    panelToggleSub.textContent = currentPrefs.masterToggle ? 'Showing all companies with scores' : 'Filtering by your thresholds';
  });

  panelToggle.addEventListener('change', async () => {
    const currentPrefs = await loadPreferences();
    currentPrefs.masterToggle = panelToggle.checked;
    panelToggleLabel.textContent = panelToggle.checked ? 'Full View' : 'AI Filter Active';
    panelToggleSub.textContent = panelToggle.checked ? 'Showing all companies with scores' : 'Filtering by your thresholds';
    try { chrome.storage.sync.set(currentPrefs); } catch (e) {}
  });
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
  const dimColor = HumanEngine.getScoreColor(dimScore);
  const tierColor = profile.tier.color;

  panel.innerHTML = `
    <div class="human-panel__header">
      <div class="human-panel__back" id="panelBack">← Back</div>
      <div class="human-panel__title">HI.</div>
      <div class="human-panel__close" id="panelClose">✕</div>
    </div>

    <div class="human-panel__company">
      <div class="human-panel__grade" style="color: ${tierColor}">${profile.letter}</div>
      <div>
        <div class="human-panel__name">${profile.name}</div>
        <div class="human-panel__tier" style="color: ${tierColor}">HI Grade: ${profile.grade} · ${profile.composite}</div>
        <div class="human-panel__brand">Find the HI balance.</div>
      </div>
    </div>
    <div class="human-panel__satire">"${profile.tier.satire}"</div>

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
        const c = HumanEngine.getScoreColor(s);
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
      <div>Find the HI balance.</div>
      <div class="human-panel__footer-sub">thehibalance.org · The Deep Thought Foundation</div>
    </div>

    <div class="human-panel__disclaimer">
      HI Grades are estimated from public data and are not financial, legal, or investment advice. Scores reflect publicly available information and may not capture all aspects of a company's operations. Not affiliated with or endorsed by any scored company. Methodology: HUMAN Grade Spec v1.0 (Apache 2.0). Patent pending.
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
        text.textContent = `Connected · ${resp.companies} companies · API live`;
      } else {
        dot.style.color = '#E07020';
        text.textContent = 'Offline · Using local database (206 companies)';
      }
    } catch (e) {
      dot.style.color = '#E07020';
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
      const col = HumanEngine.getScoreColor(p.composite);
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
