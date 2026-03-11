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
  badge.className = 'human-badge human-badge--expanded'; // Start expanded

  // Determine badge state
  const isFiltered = !prefs.masterToggle && !filterResult.passes;
  const isSoftFiltered = isFiltered && prefs.filterMode === 'soft';
  const isHardFiltered = isFiltered && prefs.filterMode === 'strict';

  badge.innerHTML = buildBadgeHTML(profile, filterResult, prefs, isSoftFiltered);

  // Click to collapse, click again to expand
  badge.addEventListener('click', () => toggleExpanded(badge, profile, filterResult, prefs));

  // Add a close button so users can dismiss it
  const closeBtn = document.createElement('div');
  closeBtn.className = 'human-badge__close';
  closeBtn.innerHTML = '✕';
  closeBtn.title = 'Minimize';
  closeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    badge.classList.remove('human-badge--expanded');
    badge.classList.add('human-badge--compact');
  });
  badge.querySelector('.human-badge__header').appendChild(closeBtn);

  document.body.appendChild(badge);

  // Attach click handlers for dimension detail panels
  attachDimClickHandlers(badge, profile);
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
    what: "Measures principled action — pricing ethics, data ethics, market behavior, product design, and political activity. Starts at 100, deducted for violations.",
    signals: ["Pricing Ethics", "Data Ethics", "Market Ethics", "Product Ethics", "Political Ethics"],
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
      </div>
    </div>

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
      <div class="human-panel__signals-title">Sub-Signals</div>
      <div class="human-panel__signals">
        ${dimInfo.signals.map((s, i) => `
          <div class="human-panel__signal">
            <span class="human-panel__signal-id">${dim.toUpperCase()}.${i+1}</span>
            <span class="human-panel__signal-name">${s}</span>
          </div>
        `).join('')}
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

    <div class="human-panel__search-section">
      <div class="human-panel__section-title">Search Companies</div>
      <input type="text" class="human-panel__search" id="panelSearch" placeholder="Search companies...">
      <div class="human-panel__results" id="panelResults"></div>
    </div>

    <div class="human-panel__footer">
      <div>Find the HI balance.</div>
      <div class="human-panel__footer-sub">thehibalance.org · The Deep Thought Foundation</div>
    </div>
  `;

  document.body.appendChild(panel);

  // Event listeners
  document.getElementById('panelClose').addEventListener('click', () => panel.remove());
  document.getElementById('panelBack').addEventListener('click', () => panel.remove());

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
