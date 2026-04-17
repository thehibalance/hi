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
        cloud_hi_balanced_gates: d.hi_balanced_gates || null,
        cloud_hi_balanced_threshold: 60,
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
        <svg width="56" height="70" viewBox="0 -4 68 88" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.2))">
          <path d="M24,0 C30,-3 38,-3 44,0 C52,4 54,12 54,20 C54,30 46,38 34,38 C22,38 14,30 14,20 C14,12 16,4 24,0 Z M4,66 C4,48 16,40 34,40 C52,40 64,48 64,66 L64,72 C64,74 62,76 60,76 L8,76 C6,76 4,74 4,72 Z" fill="white" stroke="#1B3A5C" stroke-width="2"/>
          <text x="34" y="24" text-anchor="middle" fill="#1B3A5C" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="12" font-weight="900">HI.</text>
          <text x="34" y="62" text-anchor="middle" fill="#1B3A5C" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="16" font-weight="700">?</text>
        </svg>
      </div>
    `;
    reqBadge.addEventListener('click', (e) => {
      if (reqBadge._wasDragged) { reqBadge._wasDragged = false; return; }
      window.open('https://thehibalance.org/#request&company=' + encodeURIComponent(domain), '_blank');
    });
    document.body.appendChild(reqBadge);
    makeBadgeDraggable(reqBadge);
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
    profile.scoreColor = '#1B3A5C';
    profile.tier = { color: profile.scoreColor, satire: "" };
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
  
  // Detect pending (seed) companies — show gray
  const SEED_SOURCES = ['Defaults', 'Manual Scoring', 'Seed Estimate', 'Public Reporting'];
  profile.isPending = company.score_status === 'pending' || 
    (profile.data_sources.length === 1 && SEED_SOURCES.includes(profile.data_sources[0])) ||
    (profile.data_sources.length === 0);
  if (profile.isPending) {
    profile.scoreColor = '#999';
    profile.hiBalanced = false;
    profile.isGold = false;
  }

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
 * Make any badge element draggable + persist position to localStorage.
 * Used for both the scored badge and the "unknown company" mini badge.
 */
function makeBadgeDraggable(badge) {
  // Load saved position
  try {
    const saved = localStorage.getItem('hi_badge_pos');
    if (saved) {
      const pos = JSON.parse(saved);
      badge.style.bottom = 'auto';
      badge.style.left = Math.min(pos.x, window.innerWidth - 60) + 'px';
      badge.style.top = Math.min(pos.y, window.innerHeight - 70) + 'px';
    }
  } catch(e) {}

  let dragStartX, dragStartY, badgeStartX, badgeStartY, isDragging = false;

  badge.addEventListener('mousedown', (e) => {
    if (e.target.closest('.human-panel')) return;
    isDragging = false;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    const rect = badge.getBoundingClientRect();
    badgeStartX = rect.left;
    badgeStartY = rect.top;

    const onMove = (e2) => {
      const dx = e2.clientX - dragStartX;
      const dy = e2.clientY - dragStartY;
      if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
        isDragging = true;
        badge.style.bottom = 'auto';
        badge.style.left = Math.max(0, Math.min(badgeStartX + dx, window.innerWidth - 60)) + 'px';
        badge.style.top = Math.max(0, Math.min(badgeStartY + dy, window.innerHeight - 70)) + 'px';
        badge.style.transition = 'none';
      }
    };

    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      badge.style.transition = '';
      if (isDragging) {
        badge._wasDragged = true;
        try {
          localStorage.setItem('hi_badge_pos', JSON.stringify({
            x: parseInt(badge.style.left),
            y: parseInt(badge.style.top)
          }));
        } catch(e) {}
      }
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });
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
    if (badge._wasDragged) { badge._wasDragged = false; return; }
    if (badge.classList.contains('human-badge--mini')) {
      openFullPanel(profile, filterResult, prefs);
    }
  });

  // Dark mode disabled
  // try { chrome.storage.local.get('darkMode', ...); } catch(e) {}

  document.body.appendChild(badge);
  makeBadgeDraggable(badge);

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
  const scoreColor = profile.isPending ? '#999' : '#1B3A5C';
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
  const fillColor = scoreColor;
  
    
  // Unified pill: navy silhouette + score + heart + optional ◈ for Balanced Board
  // Dual drop-shadow: soft glow for dark-mode visibility + subtle depth shadow
  const glowColor = profile.hiBalanced ? 'rgba(196,155,32,0.55)' : fillColor + '70';
  const bbMarker = profile.hiBalanced
    ? '<circle cx="54" cy="14" r="7" fill="#C49B20"/><text x="54" y="18" text-anchor="middle" fill="white" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="9" font-weight="900">\u25C8</text>'
    : '';
  const bbTooltip = profile.hiBalanced ? 'Balanced Board \u2014 all 5 HUMAN dimensions \u2265 60' : '';
  return `
    <div class="human-badge__mini" style="padding:0;background:transparent !important;border:none !important;box-shadow:none !important" title="${bbTooltip}">
      <svg width="56" height="70" viewBox="0 -4 68 88" style="filter:drop-shadow(0 0 10px ${glowColor}) drop-shadow(0 2px 4px rgba(0,0,0,0.25))">
        <path d="${silhouette}" fill="${fillColor}"/>
        <text x="34" y="24" text-anchor="middle" fill="white" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="15" font-weight="900">${profile.composite}</text>
        <g style="animation:${heartAnim};transform-origin:34px 58px">
          <text x="34" y="64" text-anchor="middle" fill="white" font-size="18">\u2665</text>
        </g>
        ${bbMarker}
      </svg>
    </div>
  `;
}

/**
 * Build the badge HTML content.
 */
function buildBadgeHTML(profile, filterResult, prefs, isSoftFiltered) {
  const scoreColor = profile.isPending ? "#999" : "#1B3A5C";
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
      ${(() => { var bc = ['h','u','m','a','n'].filter(d => (profile.dimensions[d] || 0) < 60).length; return bc > 0 ? `<div class="human-badge__decay human-badge__decay--warning">⚖ ${bc} dimension${bc > 1 ? 's' : ''} below 60 — Dimensions gate fails.</div>` : ''; })()}
      ${profile.decay_level !== 'stable' && profile.decay_index > 0 ? `
        <div class="human-badge__decay human-badge__decay--${profile.decay_level}" style="padding:8px 10px">
          <div style="font-weight:700;font-size:12px">♥ Heartbeat: ${profile.decay_level.charAt(0).toUpperCase() + profile.decay_level.slice(1)} · Decay: ${profile.decay_index}/100</div>
          ${profile.decay_factors.map(f => `<div style="font-size:10px;margin-top:4px;padding-left:14px;position:relative"><span style="position:absolute;left:0">›</span>${f}</div>`).join('')}
        </div>` : ''}
      ${filterWarning}
      <div class="human-badge__pulse" id="human-badge-pulse"></div>
      
      <div class="human-badge__disclaimer">Estimated from public data. Not financial or legal advice.</div>
    </div>
  `;
}

/**
 * Build the dimension bar visualizations.
 */

const GENOME_LABELS = {
  'H.1':'Workforce','H.2':'Craft','H.3':'Decision','H.5':'Augmentation (v1.2)',
  'U.1':'Cust. Empathy','U.2':'Worker Empathy','U.3':'Relational','U.4':'Sim. Empathy',
  'U.6_dei':'DEI','U.7_hrc':'HRC',
  'M.1':'Pricing','M.2':'Data','M.3':'Market','M.4':'Product','M.5':'Stakeholder',
  'M.6_dei':'DEI','M.7_hrc':'HRC',
  'A.1':'Energy','A.2':'Water','A.3':'Land','A.4':'Lifecycle',
  'N.2':'Reporting','N.5':'Filings'
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
    what: "How invested is the company in its own people? Workforce valuation, craft depth, human decision authority, and the AI-augmentation balance — not replacement.",
    signals: ["Workforce Valuation", "Craft", "Human Decision Depth", "Human Augmentation Index"],
  },
  u: {
    name: "Understanding & Empathy",
    icon: "💙",
    what: "Real care vs simulated care. Customer empathy, worker empathy, relational integrity, and detection of AI-generated empathy theater.",
    signals: ["Customer Empathy", "Worker Empathy", "Relational Integrity", "Simulated Empathy Detection"],
  },
  m: {
    name: "Moral & Ethical Conduct",
    icon: "⚖️",
    what: "Principled action across pricing, data, market behavior, product safety, and stakeholder governance. Deducted for documented harm and concealment.",
    signals: ["Pricing Ethics", "Data Ethics", "Market Ethics", "Product Ethics", "Stakeholder Governance"],
  },
  a: {
    name: "Alive & Environmental",
    icon: "🌍",
    what: "True environmental cost across energy, water, land, and product lifecycle — including the hidden footprint of AI infrastructure.",
    signals: ["Energy & Emissions", "Water", "Land & Habitat", "Product Lifecycle"],
  },
  n: {
    name: "Natural Transparency",
    icon: "🔍",
    what: "Reporting quality and filing volume. Is this company genuinely open, or hiding what it doesn't want measured?",
    signals: ["Reporting Quality", "Filing Volume"],
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
  panel.style.maxHeight = 'calc(100vh - 40px)';
  panel.style.overflowY = 'auto';

  const scoreColor = profile.isPending ? "#999" : "#1B3A5C";
  const pulseColors = {'critical':'#DC2626','warning':'#DC2626','watch':'#D97706','stable':'#16A34A'};
  const pulseColor = pulseColors[profile.decay_level] || '#16A34A';
  const pulseDotHTML = profile.decay_index > 0 
    ? `<span style="font-size:12px;font-weight:700;color:${pulseColor};margin-left:8px${profile.decay_level==='critical'||profile.decay_level==='warning'?';animation:blink 2s infinite':''}">♥${profile.decay_index}</span>`
    : `<span style="font-size:12px;color:#16A34A;margin-left:8px">♥</span>`;

  // Sub-signal labels matching website/app
  const SUB_LABELS = {
    'H.1':'Workforce Valuation','H.2':'Craft','H.3':'Human Decision Depth','H.4':'CEO Accountability (v1.2)','H.5':'Human Augmentation Index (v1.2)',
    'U.1':'Customer Empathy','U.2':'Worker Empathy','U.3':'Relational Integrity','U.4':'Simulated Empathy Detection','U.5':'Moral Courage (v1.2)',
    'M.1':'Pricing Ethics','M.2':'Data Ethics','M.3':'Market Ethics','M.4':'Product Ethics','M.5':'Stakeholder Governance',
    'A.1':'Energy & Emissions','A.2':'Water','A.3':'Land & Habitat','A.4':'Product Lifecycle','A.5':'Resource Stewardship (v1.2)',
    'N.1':'AI Disclosure (v1.2)','N.2':'Reporting Quality','N.3':'Labor Auditability (v1.2)','N.4':'Humanwashing Detection (v1.2)','N.5':'Filing Volume'
  };
  const SUB_KEYS = {h:['H.1','H.2','H.3','H.4','H.5'],u:['U.1','U.2','U.3','U.4','U.5'],m:['M.1','M.2','M.3','M.4','M.5'],a:['A.1','A.2','A.3','A.4','A.5'],n:['N.1','N.2','N.3','N.4','N.5']};
  const SEED_SRC = ['Defaults','Manual Scoring','Seed Estimate','Public Reporting'];

  // Build all dimensions with expandable sub-signal bars
  const allDimsHTML = HumanEngine.DIMENSIONS.map(d => {
    const s = profile.dimensions[d] || 0;
    const c = profile.isPending ? '#999' : HumanEngine.getScoreColor(s, profile.balancedThreshold);
    const info = DIM_DESCRIPTIONS[d];
    const genome = profile.genome || {};
    const dd = genome[d.toUpperCase()] || {};
    const dimSources = (dd.sources || []);
    let subScores = dd.scores || {};
    
    // Fill from dimension score if genome empty
    if (!Object.keys(subScores).length) {
      (SUB_KEYS[d] || []).forEach(k => { subScores[k] = s; });
    }
    
    const isSeed = profile.isPending || dimSources.some(s => SEED_SRC.includes(s)) || 
      (Object.values(subScores).length > 1 && new Set(Object.values(subScores).map(Math.round)).size === 1 && !dimSources.length);
    
    let realCount = 0;
    if (!isSeed) {
      Object.values(subScores).forEach(v => { if (Math.round(v) < 45 || Math.round(v) > 55) realCount++; });
    }
    
    const subBarsHTML = (SUB_KEYS[d] || []).filter(k => !(SUB_LABELS[k] || '').includes('(v1.2)')).map(k => {
      const v = Math.round(subScores[k] || 50);
      const lbl = SUB_LABELS[k] || k;
      const isDef = isSeed || (v >= 45 && v <= 55 && !dimSources.length);
      const barCol = isDef ? '#ccc' : HumanEngine.getScoreColor(v, profile.balancedThreshold || 62);
      const txtCol = isDef ? '#999' : barCol;
      return `<div style="display:flex;align-items:center;gap:6px;padding:2px 0">
        <span style="font-size:9px;font-weight:700;font-family:monospace;color:#999;width:24px;text-align:right">${k}</span>
        <div style="flex:1">
          <div style="display:flex;justify-content:space-between"><span style="font-size:10px;color:${isDef?'#999':'#333'}">${lbl}</span><span style="font-size:10px;font-weight:700;color:${txtCol}">${v}</span></div>
          <div style="height:3px;background:#EEF1F5;border-radius:2px;margin-top:1px"><div style="height:100%;width:${v}%;background:${barCol};border-radius:2px"></div></div>
        </div>
      </div>`;
    }).join('');
    
    const covLabel = isSeed ? 'Estimated' : realCount >= 4 ? 'Strong data' : realCount >= 2 ? 'Partial' : realCount > 0 ? 'Limited' : 'Needs data';
    const covColor = isSeed ? '#92400E' : realCount >= 4 ? '#16A34A' : '#D97706';
    const covBg = isSeed ? '#F3F0E8' : realCount >= 4 ? '#DCF5E7' : '#FFF3E0';
    const activeKeys = (SUB_KEYS[d] || []).filter(k => !(SUB_LABELS[k] || '').includes('(v1.2)'));
    const covHTML = `<div style="display:flex;align-items:center;gap:6px;margin-top:4px"><span style="font-size:8px;font-weight:600;color:${covColor};padding:2px 6px;border-radius:4px;background:${covBg}">${realCount}/${activeKeys.length} · ${covLabel}</span>${dimSources.length ? `<span style="font-size:8px;color:#999">${dimSources.join(' · ')}</span>` : ''}</div>`;

    return `
      <div style="margin-bottom:8px">
        <div class="human-panel__dim-row human-dim-toggle" style="cursor:pointer" data-dim="${d}">
          <span class="human-panel__row-icon">${info.icon}</span>
          <span class="human-panel__row-label">${d.toUpperCase()}</span>
          <div class="human-panel__row-bar">
            <div class="human-panel__row-fill" style="width: ${s}%; background: ${c}"></div>
          </div>
          <span class="human-panel__row-score" style="color: ${c}">${s}</span>
          <span class="human-dim-arrow" style="font-size:10px;color:#999;margin-left:4px">▾</span>
        </div>
        <div class="human-dim-detail" style="display:none;padding:8px 12px;background:#f8f9fa;border-radius:0 0 8px 8px;margin-top:-2px">
          ${subBarsHTML}
          ${covHTML}
        </div>
      </div>`;
  }).join('');

  // Heartbeat/decay section
  let decayHTML = '';
  if (profile.decay_level !== 'stable' && profile.decay_index > 0) {
    const decayColors = {'critical':'#DC2626','warning':'#DC2626','watch':'#D97706','stable':'#16A34A'};
    const dc = decayColors[profile.decay_level] || '#6B7280';
    decayHTML = `
      <div style="background:${dc}10;border:1px solid ${dc}30;border-radius:8px;padding:10px 12px;margin-top:8px">
        <div style="font-weight:700;font-size:11px;color:${dc};letter-spacing:0.5px;text-transform:uppercase;margin-bottom:6px">♥ What the Heartbeat caught</div>
        ${profile.decay_factors.map(f => `<div style="font-size:11px;margin-top:3px;padding-left:14px;position:relative;color:#444"><span style="position:absolute;left:0;color:${dc}">›</span>${f}</div>`).join('')}
      </div>`;
  }

  // Balance floor
  let floorHTML = '';
  if (profile.balance_floor) {
    const _bc60 = ['h','u','m','a','n'].filter(d => (profile.dimensions[d]||0) < 60).length;
    floorHTML = _bc60 > 0 ? `<div style="background:#FFF7ED;border:1px solid #FDBA74;border-radius:8px;padding:8px 12px;margin-top:8px;font-size:11px;color:#9A3412">⚖ ${_bc60} dimension${_bc60 > 1 ? 's' : ''} below 60 — Dimensions gate fails.</div>` : '';
  }

  // Pulse
  const badge = document.getElementById('human-score-badge');
  const pulse = badge ? badge._pulse : null;
  let pulseHTML = '';
  if (pulse && pulse.pulse) {
    const pc = { healthy: '#16A34A', elevated: '#D97706', stressed: '#DC2626', critical: '#DC2626' };
    const pColor = pc[pulse.pulse] || '#6B7280';
    pulseHTML = `<div style="font-size:10px;color:${pColor};margin-top:6px;text-align:center;opacity:0.8">Market pulse: <strong>${pulse.pulse}</strong> · ${pulse.alerts_count || 0} active alerts</div>`;
  }

  panel.innerHTML = `
    <div class="human-panel__header" style="background:#1B3A5C !important;border-bottom:none">
      <div class="human-panel__back" id="panelBack" style="visibility:hidden;color:white">←</div>
      <div class="human-panel__title"><img src="${chrome.runtime.getURL('icons/icon-128.png')}" style="height:40px;width:auto;border-radius:6px;filter:brightness(0) invert(1)" alt="HI."></div>
      <div class="human-panel__close" id="panelClose" style="color:white">✕</div>
    </div>

    <div class="human-panel__company" style="background:white">
      <div class="human-panel__grade" style="color:${scoreColor};font-size:36px">${profile.composite}</div>
      <div style="flex:1;min-width:0">
        <div class="human-panel__name">${profile.name}</div>${profile.hiBalanced ? '<div style="font-size:10px;font-weight:700;color:#C49B20;letter-spacing:1.5px;margin-top:2px">\u25C8 BALANCED BOARD</div>' : ''}
        <div class="human-panel__tier" style="color: ${scoreColor};font-weight:600">${profile.isPending ? "Pending Verification" : profile.hiBalanced ? "Gold HI Grade™" : "HI Grade™"} · ${profile.composite}/100</div>
        ${(profile.decay_level && profile.decay_level !== 'stable' && profile.decay_index > 0) ? `<div style="font-size:11px;color:${pulseColor};margin-top:3px;font-weight:600">♥ ${profile.decay_level.charAt(0).toUpperCase()+profile.decay_level.slice(1)} decay · ${profile.decay_index}/100</div>` : (profile.decay_level === 'stable' ? '<div style="font-size:11px;color:#16A34A;margin-top:3px;font-weight:600">♥ Stable</div>' : '')}
      </div>
    </div>
    


    <div style="background:white;padding:8px 16px">
      <div style="font-size:11px;font-weight:700;color:#1B3A5C;letter-spacing:0.5px;margin-bottom:8px">HUMAN DIMENSIONS</div>
      ${allDimsHTML}
    </div>

    ${floorHTML ? `<div style="background:white;padding:4px 16px">${floorHTML}</div>` : ''}
    ${decayHTML ? `<div style="background:white;padding:4px 16px">${decayHTML}</div>` : ''}

    ${pulseHTML ? `<div style="background:white;padding:4px 16px">${pulseHTML}</div>` : ''}

    <div class="human-panel__toggle-section" style="background:white">
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

    <div style="background:#1B3A5C;padding:14px 16px;border-radius:0 0 14px 14px;margin-top:8px">
      <div style="display:flex;justify-content:center;align-items:center;gap:14px;margin-bottom:10px;flex-wrap:wrap">
        <a href="https://thehibalance.org" target="_blank" style="font-size:11px;font-weight:600;color:#E8E2D0;text-decoration:none">🌐 thehibalance.org</a>
        <a href="https://apps.apple.com/app/hi/id6761270596" target="_blank" style="font-size:11px;font-weight:600;color:#E8E2D0;text-decoration:none">🍎 iOS App</a>
      </div>
      <div style="display:flex;align-items:center;justify-content:center;gap:5px;margin-bottom:8px">
        <span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:#16A34A"></span>
        <span id="hiPipelineCountdown" style="font-size:9px;font-family:'DM Mono',monospace;color:#5A7A9A;letter-spacing:0.3px">Connected · API live</span>
      </div>
      <div style="font-size:8px;color:#5A7A9A;line-height:1.4;text-align:center">Spec v1.1.0 · 19 active sub-signals · 42 data sources · Estimated from public data. Not financial or legal advice.</div>
    </div>
  `;

  document.body.appendChild(panel);

  // Close panel
  document.getElementById('panelClose').addEventListener('click', () => panel.remove());

  // Dimension expand/collapse toggles (CSP-safe, no inline onclick)
  panel.querySelectorAll('.human-dim-toggle').forEach(row => {
    row.addEventListener('click', () => {
      const detail = row.nextElementSibling;
      const arrow = row.querySelector('.human-dim-arrow');
      if (detail) {
        const isOpen = detail.style.display === 'block';
        detail.style.display = isOpen ? 'none' : 'block';
        if (arrow) arrow.textContent = isOpen ? '▾' : '▴';
      }
    });
  });

  // Pipeline countdown timer — counts to midnight CST
  const countdownEl = document.getElementById('hiPipelineCountdown');
  if (countdownEl) {
    const updateCountdown = () => {
      const now = new Date();
      const cst = new Date(now.toLocaleString('en-US', { timeZone: 'America/Chicago' }));
      const tomorrow = new Date(cst);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 0, 0, 0);
      const diff = Math.max(0, Math.floor((tomorrow - cst) / 1000));
      const h = String(Math.floor(diff / 3600)).padStart(2, '0');
      const m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
      const s = String(diff % 60).padStart(2, '0');
      countdownEl.textContent = diff > 0 ? `Connected · API live · Next update: ${h}:${m}:${s}` : 'Connected · Updating now...';
    };
    updateCountdown();
    setInterval(updateCountdown, 1000);
  }

  // Master toggle
  const panelToggle = document.getElementById('panelMasterToggle');
  const panelToggleLabel = document.getElementById('panelToggleLabel');
  const panelToggleSub = document.getElementById('panelToggleSub');

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
    <div class="human-panel__header" style="background:#1B3A5C !important;border-bottom:none">
      <div class="human-panel__back" id="panelBack" style="color:white">← Back</div>
      <div class="human-panel__title"><img src="${chrome.runtime.getURL('icons/icon-128.png')}" style="height:40px;width:auto;border-radius:6px;filter:brightness(0) invert(1)" alt="HI."></div>
      <div class="human-panel__close" id="panelClose" style="color:white">✕</div>
    </div>

    <div class="human-panel__company">
      <div class="human-panel__grade" style="color:${scoreColor};font-size:36px">${profile.composite}</div>
      <div>
        <div class="human-panel__name">${profile.name}</div>
        <div class="human-panel__tier" style="color: ${scoreColor}">${profile.isPending ? "Pending Verification" : "HI Grade™"}${pulseDotHTML}</div>
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

    <div style="background:#1B3A5C;padding:14px 16px;border-radius:0 0 14px 14px">
      <div style="font-size:13px;font-weight:700;color:#E8E2D0;letter-spacing:0.5px;text-align:center">Think human intelligence.</div>
      <div style="font-size:11px;color:white;margin-top:4px;opacity:0.8;text-align:center">thehibalance.org · The HI Balance</div>
      <div style="font-size:8px;color:#5A7A9A;margin-top:8px;line-height:1.4;text-align:center">HI Grade Spec v1.1.0 · 19 active sub-signals · 42 data sources · Estimated from public data. Not financial or legal advice.</div>
    </div>
  `;

  document.body.appendChild(panel);

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
      const SEED = ['Defaults', 'Manual Scoring', 'Seed Estimate', 'Public Reporting'];
      const ds = c.data_sources || [];
      const pend = c.score_status === 'pending' || (ds.length === 1 && SEED.includes(ds[0])) || ds.length === 0;
      const col = pend ? '#999' : '#1B3A5C';
      return `
        <div class="human-panel__result"${pend ? ' style="opacity:0.6"' : ''}>
          <span class="human-panel__result-score" style="color: ${col}">${p.composite}</span>
          <span class="human-panel__result-name">${p.name}${pend ? ' <span style="font-size:9px;color:#999">· pending</span>' : ''}</span>
          <span class="human-panel__result-grade" style="color: ${col}">${pend ? 'Pending' : p.grade}</span>
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
