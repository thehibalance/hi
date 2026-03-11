/**
 * HI. Grade Popup Controller
 * 
 * Manages the extension popup UI:
 *   - Current site score display
 *   - Master toggle (full view / filtered)
 *   - Dimension equalizer (threshold sliders)
 *   - Company search
 *   - Preferences persistence
 * 
 * NO AI. Pure event handlers and DOM updates.
 */

(async function() {
  'use strict';

  // ═══ INITIALIZE ═══
  await HumanDB.init();
  const prefs = await loadPrefs();

  // ═══ DISPLAY COMPANY COUNT ═══
  const localCount = HumanDB.count();
  const countEl = document.getElementById('companyCount');
  countEl.textContent = `${localCount} local companies · v0.2.0`;

  // Update with cloud count if available
  try {
    const syncResp = await new Promise((resolve) => {
      chrome.runtime.sendMessage({ type: 'GET_SYNC_STATUS' }, resolve);
    });
    if (syncResp && syncResp.serverStats && syncResp.serverStats.companies) {
      countEl.textContent = `${syncResp.serverStats.companies} companies (${localCount} local) · v0.2.0`;
    }
  } catch (e) { /* offline */ }

  // ═══ CURRENT SITE SCORE ═══
  displayCurrentSite();

  // ═══ MASTER TOGGLE ═══
  const toggleEl = document.getElementById('masterToggle');
  toggleEl.checked = prefs.masterToggle;
  updateToggleUI(prefs.masterToggle);

  toggleEl.addEventListener('change', async () => {
    prefs.masterToggle = toggleEl.checked;
    updateToggleUI(prefs.masterToggle);
    updateEqualizerState(prefs);
    await savePrefs(prefs);
  });

  // ═══ FILTER MODE ═══
  const modeBtn = document.getElementById('filterModeBtn');
  updateFilterModeUI(prefs.filterMode);

  modeBtn.addEventListener('click', async () => {
    prefs.filterMode = prefs.filterMode === 'soft' ? 'strict' : 'soft';
    updateFilterModeUI(prefs.filterMode);
    await savePrefs(prefs);
  });

  // ═══ EQUALIZER SLIDERS ═══
  const dimensions = ['h', 'u', 'm', 'a', 'n'];
  for (const dim of dimensions) {
    const slider = document.getElementById(`slider_${dim}`);
    const valueEl = document.getElementById(`value_${dim}`);

    slider.value = prefs.thresholds[dim] || 0;
    valueEl.textContent = slider.value;

    slider.addEventListener('input', async () => {
      valueEl.textContent = slider.value;
      prefs.thresholds[dim] = parseInt(slider.value);
      await savePrefs(prefs);
    });
  }

  updateEqualizerState(prefs);

  // ═══ SEARCH ═══
  const searchInput = document.getElementById('searchInput');
  const searchResults = document.getElementById('searchResults');

  searchInput.addEventListener('input', async () => {
    const query = searchInput.value.trim();
    if (query.length < 2) {
      searchResults.innerHTML = '';
      return;
    }

    // Search local seed database first
    const results = HumanDB.searchByName(query);
    
    let html = results.slice(0, 8).map(company => {
      const profile = HumanEngine.getProfile(company);
      const color = HumanEngine.getScoreColor(profile.composite);
      return `
        <div class="search-result">
          <div class="search-result__score" style="color: ${color}">${profile.composite}</div>
          <div>
            <div class="search-result__name">${profile.name}</div>
            <div class="search-result__tier" style="color: ${profile.tier.color}">
              HI Grade: ${profile.grade} · ${profile.composite}
            </div>
          </div>
        </div>
      `;
    }).join('');

    // If few local results, also search the cloud API
    if (results.length < 4 && query.length >= 3) {
      try {
        const cloudResp = await new Promise((resolve) => {
          chrome.runtime.sendMessage(
            { type: 'CLOUD_SEARCH', query: query },
            (resp) => resolve(resp)
          );
        });

        if (cloudResp && cloudResp.results && cloudResp.results.length > 0) {
          const localNames = new Set(results.map(r => r.name.toLowerCase()));
          const cloudNew = cloudResp.results.filter(r => !localNames.has(r.company.toLowerCase()));
          
          if (cloudNew.length > 0) {
            html += cloudNew.slice(0, 4).map(c => {
              const color = HumanEngine.getScoreColor(c.composite);
              const grade = c.hi_grade;
              return `
                <div class="search-result">
                  <div class="search-result__score" style="color: ${color}">${c.composite}</div>
                  <div>
                    <div class="search-result__name">${c.company} <span style="font-size:9px;color:#2E5E8E;">☁</span></div>
                    <div class="search-result__tier">
                      HI Grade: ${grade} · ${c.composite}
                    </div>
                  </div>
                </div>
              `;
            }).join('');
          }
        }
      } catch (e) { /* Cloud search unavailable */ }
    }

    searchResults.innerHTML = html || '<div class="search-result"><div class="search-result__name" style="color: #aaa">No companies found</div></div>';
  });

  // ═══ FUNCTIONS ═══

  async function displayCurrentSite() {
    const container = document.getElementById('currentSiteContent');

    try {
      // Get the active tab's URL
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url) {
        container.innerHTML = '<div class="current-site__none">No active page</div>';
        return;
      }

      const url = new URL(tab.url);
      const domain = url.hostname.replace(/^www\./, '');

      // Special pages
      if (url.protocol === 'chrome:' || url.protocol === 'chrome-extension:' || url.protocol === 'about:') {
        container.innerHTML = '<div class="current-site__none">Browser page — no score</div>';
        return;
      }

      const company = HumanDB.getByDomain(domain);

      // ═══ CLOUD FALLBACK ═══
      // If not in seed database, ask background for cloud score
      let companyData = company;
      let fromCloud = false;

      if (!companyData) {
        try {
          const cloudResp = await new Promise((resolve) => {
            chrome.runtime.sendMessage(
              { type: 'CLOUD_LOOKUP', domain: domain },
              (resp) => resolve(resp)
            );
          });

          if (cloudResp && cloudResp.data) {
            const d = cloudResp.data;
            companyData = {
              name: d.company,
              h: d.D_H, u: d.D_U, m: d.D_M, a: d.D_A, n: d.D_N,
              tags: d.tags || [], domains: d.domains || [domain],
              notes: d.notes || '', source: 'cloud',
            };
            fromCloud = true;
          }
        } catch (e) { /* Cloud unavailable */ }
      }

      if (!companyData) {
        container.innerHTML = `<div class="current-site__none">${domain} — not yet scored</div>`;
        return;
      }

      const profile = HumanEngine.getProfile(companyData);
      const scoreColor = HumanEngine.getScoreColor(profile.composite);

      container.innerHTML = `
        <div class="score-card">
          <div class="score-card__number" style="color: ${scoreColor}">${profile.composite}</div>
          <div class="score-card__info">
            <div class="score-card__name">${profile.name}</div>
            <div class="score-card__tier" style="color: ${profile.tier.color}">
              HI Grade: ${profile.grade} · ${profile.composite}
            </div>
            ${profile.confidence === 'estimated' ? '<span class="score-card__confidence">ESTIMATED</span>' : ''}
            ${fromCloud ? '<span class="score-card__confidence" style="background:#e8f4f8;color:#2E5E8E;">☁ LIVE</span>' : ''}
          </div>
        </div>
        <div class="dim-bars">
          ${buildDimBars(profile.dimensions)}
        </div>
      `;
    } catch (e) {
      container.innerHTML = '<div class="current-site__none">Unable to check current page</div>';
    }
  }

  function buildDimBars(dimensions) {
    return ['h', 'u', 'm', 'a', 'n'].map(dim => {
      const score = dimensions[dim] || 0;
      const color = HumanEngine.getScoreColor(score);
      const label = HumanEngine.getDimensionLabel(dim);
      return `
        <div class="dim-bar">
          <span class="dim-bar__label">${dim.toUpperCase()}</span>
          <span class="dim-bar__name">${label}</span>
          <div class="dim-bar__track">
            <div class="dim-bar__fill" style="width: ${score}%; background: ${color}"></div>
          </div>
          <span class="dim-bar__value">${score}</span>
        </div>
      `;
    }).join('');
  }

  function updateToggleUI(isFullView) {
    const label = document.getElementById('toggleLabel');
    const sublabel = document.getElementById('toggleSublabel');
    if (isFullView) {
      label.textContent = 'Full View';
      sublabel.textContent = 'Showing all companies with scores';
    } else {
      label.textContent = 'AI Filter Active';
      sublabel.textContent = 'Filtering by your thresholds';
    }
  }

  function updateFilterModeUI(mode) {
    const btn = document.getElementById('filterModeBtn');
    btn.textContent = mode === 'strict' ? 'Strict' : 'Soft';
    btn.className = 'equalizer__mode' + (mode === 'strict' ? ' equalizer__mode--strict' : '');
  }

  function updateEqualizerState(prefs) {
    const eq = document.getElementById('equalizer');
    if (prefs.masterToggle) {
      eq.classList.add('equalizer--disabled');
    } else {
      eq.classList.remove('equalizer--disabled');
    }
  }

  async function loadPrefs() {
    try {
      if (typeof chrome !== 'undefined' && chrome.storage) {
        const stored = await chrome.storage.local.get('userPrefs');
        if (stored.userPrefs) {
          return { ...HumanEngine.DEFAULT_PREFS, ...stored.userPrefs };
        }
      }
    } catch (e) {}
    return { ...HumanEngine.DEFAULT_PREFS };
  }

  async function savePrefs(prefs) {
    try {
      if (typeof chrome !== 'undefined' && chrome.storage) {
        await chrome.storage.local.set({ userPrefs: prefs });
      }
    } catch (e) {}
  }

  // ═══ SYNC STATUS (Phase 2 Track D) ═══
  async function updateSyncStatus() {
    const el = document.getElementById('sync-status');
    if (!el) return;

    // Ping the API directly — don't rely on the service worker being awake
    const apiUrls = ['http://localhost:8080', 'http://localhost:5000', 'https://api.thehibalance.org'];
    
    for (const url of apiUrls) {
      try {
        const resp = await fetch(`${url}/api/v1/health`, { 
          signal: AbortSignal.timeout(3000),
          headers: { 'Accept': 'application/json' }
        });
        if (resp.ok) {
          const data = await resp.json();
          el.textContent = `☁ Connected · ${data.companies} companies · API live`;
          return;
        }
      } catch (e) { /* try next URL */ }
    }

    el.textContent = '📦 Local database · 206 companies';
  }

  updateSyncStatus();

})();
