/**
 * HI. Background Service Worker
 * Handles API communication for the content script.
 * Zero tracking. Zero analytics. Just score lookups.
 */

const API_BASE = 'https://api.thehibalance.org';

// Cache for score lookups (in-memory, cleared on service worker restart)
const scoreCache = new Map();
const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'CLOUD_LOOKUP') {
    handleCloudLookup(message.domain).then(sendResponse).catch(() => sendResponse(null));
    return true; // async
  }

  if (message.type === 'PULSE_LOOKUP') {
    handlePulseLookup().then(sendResponse).catch(() => sendResponse(null));
    return true;
  }

  if (message.type === 'QUEUE_LOOKUP') {
    // Fire-and-forget: queue domain for future scoring
    // For now, just log it
    console.log('HI. Queue lookup:', message.domain);
    sendResponse({ queued: true });
    return false;
  }

  if (message.type === 'CHECK_CONNECTION') {
    handleConnectionCheck().then(sendResponse).catch(() => sendResponse({ connected: false }));
    return true;
  }

  return false;
});

async function handleCloudLookup(domain) {
  if (!domain) return null;

  // Check cache
  const cached = scoreCache.get(domain);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return { data: cached.data };
  }

  try {
    const response = await fetch(`${API_BASE}/api/v1/score/domain/${encodeURIComponent(domain)}`, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000)
    });

    if (!response.ok) return null;

    const data = await response.json();
    if (data && data.company && !data.error) {
      scoreCache.set(domain, { data, timestamp: Date.now() });
      return { data };
    }
    return null;
  } catch (e) {
    console.log('HI. Cloud lookup failed:', domain, e.message);
    return null;
  }
}

async function handlePulseLookup() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/heartbeat/pulse`, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000)
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (e) {
    return null;
  }
}

async function handleConnectionCheck() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/stats`, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3000)
    });
    return { connected: response.ok };
  } catch (e) {
    return { connected: false };
  }
}

// Clean old cache entries periodically
setInterval(() => {
  const now = Date.now();
  for (const [key, val] of scoreCache.entries()) {
    if (now - val.timestamp > CACHE_TTL) scoreCache.delete(key);
  }
}, 5 * 60 * 1000);
