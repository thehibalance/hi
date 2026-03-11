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

  // ═══ CLOUD FALLBACK (Phase 2 Track D) ═══
  // If not in local seed database, ask the background service worker
  // to check the cloud API
  if (!company) {
    try {
      const response = await new Promise((resolve) => {
        chrome.runtime.sendMessage(
          { type: 'CLOUD_LOOKUP', domain: domain },
          (resp) => resolve(resp)
        );
      });

      if (response && response.data) {
        // Convert API response to seed-data format for the engine
        const d = response.data;
        company = {
          name: d.company,
          h: d.D_H, u: d.D_U, m: d.D_M, a: d.D_A, n: d.D_N,
          tags: d.tags || [],
          domains: d.domains || [domain],
          notes: d.notes || '',
          source: 'cloud', // Flag that this came from the API
        };
      }
    } catch (e) {
      // Cloud unavailable — queue for later
      try {
        chrome.runtime.sendMessage({ type: 'QUEUE_LOOKUP', domain: domain });
      } catch (qe) { /* extension context may be invalidated */ }
    }
  }

  if (!company) return; // Not in local DB or cloud

  // Load user preferences
  const prefs = await loadPreferences();

  // Compute score profile
  const profile = HumanEngine.getProfile(company);

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
  badge.className = 'human-badge';

  // Determine badge state
  const isFiltered = !prefs.masterToggle && !filterResult.passes;
  const isSoftFiltered = isFiltered && prefs.filterMode === 'soft';
  const isHardFiltered = isFiltered && prefs.filterMode === 'strict';

  badge.innerHTML = buildBadgeHTML(profile, filterResult, prefs, isSoftFiltered);

  // Add interaction
  badge.addEventListener('click', () => toggleExpanded(badge, profile, filterResult, prefs));

  document.body.appendChild(badge);

  // Auto-collapse after 8 seconds
  setTimeout(() => {
    if (badge.classList.contains('human-badge--expanded')) return;
    badge.classList.add('human-badge--compact');
  }, 8000);
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
      ${filterWarning}
      <div class="human-badge__tagline">Find the HI balance.</div>
      ${profile.source === 'cloud' ? '<div class="human-badge__source">☁ Live score from thehibalance.org</div>' : '<div class="human-badge__source">📦 Local database</div>'}
    </div>
  `;
}

/**
 * Build the dimension bar visualizations.
 */
function buildDimensionBars(dimensions) {
  return HumanEngine.DIMENSIONS.map(dim => {
    const score = dimensions[dim] || 0;
    const color = HumanEngine.getScoreColor(score);
    const label = dim.toUpperCase();
    const fullLabel = HumanEngine.getDimensionLabel(dim);
    return `
      <div class="human-badge__dim" title="${fullLabel}: ${score}">
        <span class="human-badge__dim-label">${label}</span>
        <div class="human-badge__dim-bar">
          <div class="human-badge__dim-fill" style="width: ${score}%; background: ${color}"></div>
        </div>
        <span class="human-badge__dim-score">${score}</span>
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
