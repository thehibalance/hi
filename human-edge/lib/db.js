/**
 * HI. Local Database
 * Minimal stub — cloud API is the primary data source.
 * This provides domain matching and search fallback.
 */

const HumanDB = {
  _companies: [],
  _domainIndex: {},
  _ready: false,

  async init() {
    // Load seed data from storage if available
    try {
      const stored = await chrome.storage.local.get('seed_companies');
      if (stored.seed_companies) {
        this._companies = stored.seed_companies;
        this._buildIndex();
      }
    } catch (e) {
      // Storage unavailable — continue without local data
    }
    this._ready = true;
  },

  _buildIndex() {
    this._domainIndex = {};
    for (const c of this._companies) {
      for (const d of (c.domains || [])) {
        this._domainIndex[d.toLowerCase()] = c;
      }
    }
  },

  getCurrentDomain() {
    try {
      const host = window.location.hostname.replace(/^www\./, '');
      return host;
    } catch (e) {
      return '';
    }
  },

  getByDomain(domain) {
    if (!domain) return null;
    const clean = domain.toLowerCase().replace(/^www\./, '');
    return this._domainIndex[clean] || null;
  },

  searchByName(query) {
    if (!query || query.length < 2) return [];
    const q = query.toLowerCase();
    return this._companies
      .filter(c => c.name && c.name.toLowerCase().includes(q))
      .slice(0, 10);
  }
};
