/**
 * HUMAN Score Background Service Worker
 * 
 * Handles:
 *   - Extension installation and updates
 *   - Message passing between popup and content scripts
 *   - Future: delta sync with cloud backend
 * 
 * NO AI. Event-driven service worker.
 */

// ═══ INSTALLATION ═══

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    // First install — set default preferences
    chrome.storage.local.set({
      userPrefs: {
        masterToggle: true,
        filterMode: "soft",
        thresholds: { h: 0, u: 0, m: 0, a: 0, n: 0 },
        minimumConfidence: "estimated"
      }
    });
    console.log('[HI.] Extension installed. Find the HI balance.');
  }

  if (details.reason === 'update') {
    console.log(`[HI.] Extension updated to v${chrome.runtime.getManifest().version}`);
  }
});

// ═══ CLOUD SYNC — Phase 2 Track D ═══

const API_BASE = 'https://api.thehibalance.org'; // Production
const API_LOCAL = 'http://localhost:8080';        // Local dev
const CACHE_TTL = 24 * 60 * 60 * 1000;           // 24 hours

/**
 * Get the active API URL. Tries production first, falls back to local.
 */
async function getApiUrl() {
  // Check if user has set a custom API URL
  const stored = await chrome.storage.local.get('apiConfig');
  if (stored.apiConfig?.url) return stored.apiConfig.url;
  
  // Try production, fall back to local
  try {
    const resp = await fetch(`${API_BASE}/api/v1/health`, { signal: AbortSignal.timeout(3000) });
    if (resp.ok) return API_BASE;
  } catch (e) { /* production not available */ }
  
  try {
    const resp = await fetch(`${API_LOCAL}/api/v1/health`, { signal: AbortSignal.timeout(2000) });
    if (resp.ok) return API_LOCAL;
  } catch (e) { /* local not available */ }
  
  return null; // No API available — offline mode
}

/**
 * Look up a company by domain from the cloud API.
 * Returns the score record or null if not found / offline.
 */
async function cloudLookup(domain) {
  // Check cache first
  const cacheKey = `cloud_${domain}`;
  const cached = await chrome.storage.local.get(cacheKey);
  if (cached[cacheKey]) {
    const entry = cached[cacheKey];
    if (Date.now() - entry.timestamp < CACHE_TTL) {
      return entry.data;
    }
  }
  
  const apiUrl = await getApiUrl();
  if (!apiUrl) return null;
  
  try {
    const resp = await fetch(`${apiUrl}/api/v1/score/${encodeURIComponent(domain)}`, {
      signal: AbortSignal.timeout(5000),
      headers: { 'Accept': 'application/json' }
    });
    
    if (resp.ok) {
      const data = await resp.json();
      // Cache the result
      await chrome.storage.local.set({
        [cacheKey]: { data, timestamp: Date.now() }
      });
      return data;
    }
    
    if (resp.status === 404) {
      // Cache the miss too (avoid repeated lookups)
      await chrome.storage.local.set({
        [cacheKey]: { data: null, timestamp: Date.now() }
      });
      return null;
    }
  } catch (e) {
    console.log(`[HI.] Cloud lookup failed for ${domain}:`, e.message);
  }
  
  return null;
}

/**
 * Queue a domain for cloud lookup when offline.
 */
async function queueLookup(domain) {
  const stored = await chrome.storage.local.get('lookupQueue');
  const queue = stored.lookupQueue || [];
  if (!queue.includes(domain)) {
    queue.push(domain);
    await chrome.storage.local.set({ lookupQueue: queue });
  }
}

/**
 * Process the offline lookup queue when connectivity returns.
 */
async function processQueue() {
  const stored = await chrome.storage.local.get('lookupQueue');
  const queue = stored.lookupQueue || [];
  if (queue.length === 0) return;
  
  const apiUrl = await getApiUrl();
  if (!apiUrl) return; // Still offline
  
  console.log(`[HI.] Processing ${queue.length} queued lookups`);
  
  const remaining = [];
  for (const domain of queue) {
    const result = await cloudLookup(domain);
    if (result === undefined) {
      remaining.push(domain); // API error, retry later
    }
    // Small delay between requests
    await new Promise(r => setTimeout(r, 200));
  }
  
  await chrome.storage.local.set({ lookupQueue: remaining });
}

/**
 * Delta sync — pull updated scores from the cloud.
 * Runs periodically to keep local cache fresh.
 */
async function deltaSync() {
  const apiUrl = await getApiUrl();
  if (!apiUrl) return;
  
  try {
    const stored = await chrome.storage.local.get('lastSync');
    const lastSync = stored.lastSync || 0;
    
    // Get stats to check if anything changed
    const resp = await fetch(`${apiUrl}/api/v1/health`, {
      signal: AbortSignal.timeout(5000)
    });
    
    if (resp.ok) {
      const health = await resp.json();
      await chrome.storage.local.set({
        lastSync: Date.now(),
        serverStats: {
          companies: health.companies,
          timestamp: health.timestamp,
        }
      });
      console.log(`[HI.] Sync complete. ${health.companies} companies in cloud.`);
    }
  } catch (e) {
    console.log('[HI.] Delta sync failed:', e.message);
  }
}

// ═══ UPDATED MESSAGE HANDLING ═══

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'GET_PREFS':
      chrome.storage.local.get('userPrefs', (result) => {
        sendResponse(result.userPrefs || null);
      });
      return true;

    case 'SET_PREFS':
      chrome.storage.local.set({ userPrefs: message.prefs }, () => {
        sendResponse({ success: true });
      });
      return true;

    case 'GET_SCORE_OVERRIDES':
      chrome.storage.local.get('scoreOverrides', (result) => {
        sendResponse(result.scoreOverrides || {});
      });
      return true;

    case 'CLOUD_LOOKUP':
      // Content script requests a cloud lookup for a domain not in seed data
      cloudLookup(message.domain).then(result => {
        sendResponse({ data: result });
      }).catch(err => {
        sendResponse({ data: null, error: err.message });
      });
      return true;

    case 'CLOUD_SEARCH':
      // Popup requests a cloud search by company name
      (async () => {
        try {
          const apiUrl = await getApiUrl();
          if (!apiUrl) {
            sendResponse({ results: [] });
            return;
          }
          const resp = await fetch(
            `${apiUrl}/api/v1/search?q=${encodeURIComponent(message.query)}&limit=8`,
            { signal: AbortSignal.timeout(5000), headers: { 'Accept': 'application/json' } }
          );
          if (resp.ok) {
            const data = await resp.json();
            sendResponse({ results: data.results || [] });
          } else {
            sendResponse({ results: [] });
          }
        } catch (e) {
          sendResponse({ results: [], error: e.message });
        }
      })();
      return true;

    case 'QUEUE_LOOKUP':
      queueLookup(message.domain).then(() => {
        sendResponse({ queued: true });
      });
      return true;

    case 'GET_SYNC_STATUS':
      chrome.storage.local.get(['lastSync', 'serverStats', 'lookupQueue'], (result) => {
        sendResponse({
          lastSync: result.lastSync || 0,
          serverStats: result.serverStats || null,
          queueLength: (result.lookupQueue || []).length,
        });
      });
      return true;

    default:
      sendResponse({ error: 'Unknown message type' });
  }
});

// ═══ PERIODIC SYNC ═══

// Process queue and sync every 30 minutes
chrome.alarms.create('deltaSync', { periodInMinutes: 30 });
chrome.alarms.create('processQueue', { periodInMinutes: 5 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'deltaSync') deltaSync();
  if (alarm.name === 'processQueue') processQueue();
});
