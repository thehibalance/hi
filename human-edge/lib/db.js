/**
 * HI. Grade Database Layer
 * 
 * Manages company score storage and retrieval.
 * Uses chrome.storage.local for persistence.
 * Designed for future upgrade to sql.js (SQLite in WASM).
 * 
 * NO AI. NO ML. NO NEURAL NETWORKS.
 * Pure deterministic data storage and retrieval.
 */

const HumanDB = {
  _companies: new Map(),
  _domainIndex: new Map(),
  _initialized: false,

  /**
   * Initialize the database with seed data and any stored overrides.
   */
  async init() {
    if (this._initialized) return;

    // Load seed data into memory
    const seeds = (typeof SEED_COMPANIES !== 'undefined') ? SEED_COMPANIES : [];
    for (const company of seeds) {
      this._companies.set(company.id, company);
      for (const domain of (company.domains || [])) {
        this._domainIndex.set(domain.toLowerCase(), company.id);
      }
    }

    // Load any cloud-synced overrides from storage
    try {
      if (typeof chrome !== 'undefined' && chrome.storage) {
        const stored = await chrome.storage.local.get('scoreOverrides');
        if (stored.scoreOverrides) {
          for (const [id, override] of Object.entries(stored.scoreOverrides)) {
            if (this._companies.has(id)) {
              Object.assign(this._companies.get(id), override);
            } else {
              this._companies.set(id, override);
              for (const domain of (override.domains || [])) {
                this._domainIndex.set(domain.toLowerCase(), id);
              }
            }
          }
        }
      }
    } catch (e) {
      // Running outside extension context (testing) — seed data only
    }

    this._initialized = true;
  },

  /**
   * Look up a company by domain name.
   * Returns the company object or null.
   */
  getByDomain(domain) {
    if (!domain) return null;
    domain = domain.toLowerCase().replace(/^www\./, '');
    const id = this._domainIndex.get(domain);
    return id ? this._companies.get(id) : null;
  },

  /**
   * Look up a company by ID.
   */
  getById(id) {
    return this._companies.get(id) || null;
  },

  /**
   * Search companies by name (case-insensitive substring match).
   */
  searchByName(query) {
    if (!query || query.length < 2) return [];
    const q = query.toLowerCase();
    const results = [];
    for (const company of this._companies.values()) {
      if (company.name.toLowerCase().includes(q)) {
        results.push(company);
      }
    }
    return results;
  },

  /**
   * Get all companies.
   */
  getAll() {
    return Array.from(this._companies.values());
  },

  /**
   * Get total count of scored companies.
   */
  count() {
    return this._companies.size;
  },

  /**
   * Get the current page's domain.
   */
  getCurrentDomain() {
    try {
      return window.location.hostname.replace(/^www\./, '');
    } catch (e) {
      return null;
    }
  }
};
