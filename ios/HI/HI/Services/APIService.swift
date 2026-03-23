import Foundation

class APIService: ObservableObject {
    static let shared = APIService()
    private let base = "https://api.thehibalance.org/api/v1"
    private let cache = CacheManager.shared
    
    @Published var stats: APIStats?
    @Published var isLoading = false
    @Published var isOffline = false
    
    var goldThreshold: Double { stats?.gold_threshold ?? stats?.hi_balanced_threshold ?? 72 }
    
    // MARK: - Generic fetch with cache
    private func fetch<T: Codable>(_ path: String, cacheKey: String? = nil) async throws -> T {
        // Try cache first
        if let key = cacheKey, let cached: T = cache.load(T.self, key: key) {
            return cached
        }
        
        guard let url = URL(string: base + path) else { throw URLError(.badURL) }
        let (data, _) = try await URLSession.shared.data(from: url)
        let result = try JSONDecoder().decode(T.self, from: data)
        
        // Save to cache
        if let key = cacheKey { cache.save(result, key: key) }
        
        await MainActor.run { isOffline = false }
        return result
    }
    
    // Fetch with offline fallback
    private func fetchCached<T: Codable>(_ path: String, cacheKey: String) async -> T? {
        do {
            return try await fetch(path, cacheKey: cacheKey)
        } catch {
            await MainActor.run { isOffline = true }
            // Return stale cache if network fails
            return cache.load(T.self, key: cacheKey)
        }
    }
    
    // MARK: - Stats
    func loadStats() async {
        if let s: APIStats = await fetchCached("/stats", cacheKey: "stats") {
            await MainActor.run { self.stats = s }
        }
    }
    
    // MARK: - Search (no cache — always live)
    func search(_ query: String) async -> [Company] {
        guard !query.isEmpty else { return [] }
        let q = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        do {
            let r: SearchResponse = try await fetch("/search?q=\(q)&limit=20")
            return r.results ?? []
        } catch { return [] }
    }
    
    // MARK: - Score by ticker
    func score(ticker: String) async -> Company? {
        do { return try await fetch("/score/ticker/\(ticker)", cacheKey: "score_\(ticker)") }
        catch { return cache.load(Company.self, key: "score_\(ticker)") }
    }
    
    // MARK: - Score by domain
    func score(domain: String) async -> Company? {
        do { return try await fetch("/score/\(domain)", cacheKey: "score_\(domain)") }
        catch { return cache.load(Company.self, key: "score_\(domain)") }
    }
    
    // MARK: - Top companies
    func top(limit: Int = 100) async -> [Company] {
        if let r: TopBottomResponse = await fetchCached("/grades/top?limit=\(limit)", cacheKey: "top_\(limit)") {
            return r.results ?? []
        }
        return []
    }
    
    // MARK: - Bottom companies
    func bottom(limit: Int = 50) async -> [Company] {
        if let r: TopBottomResponse = await fetchCached("/grades/bottom?limit=\(limit)", cacheKey: "bottom_\(limit)") {
            return r.results ?? []
        }
        return []
    }
    
    // MARK: - Heartbeat
    func heartbeatPulse() async -> HeartbeatPulse? {
        return await fetchCached("/heartbeat/pulse", cacheKey: "hb_pulse")
    }
    
    func heartbeatAlerts(limit: Int = 40) async -> [HeartbeatAlert] {
        if let r: HeartbeatAlertsResponse = await fetchCached("/heartbeat/alerts?limit=\(limit)", cacheKey: "hb_alerts") {
            return r.results ?? []
        }
        return []
    }
    
    // MARK: - HUMAN 100
    func human100() async -> [Human100Entry] {
        if let r: Human100Response = await fetchCached("/human100", cacheKey: "human100") {
            return r.constituents ?? r.results ?? []
        }
        return []
    }
    
    // MARK: - Shield / Moat
    func moat(limit: Int = 900) async -> MoatResponse? {
        return await fetchCached("/moat?limit=\(limit)", cacheKey: "moat")
    }
    
    // MARK: - Lens / Arbitrage
    func arbitrage(limit: Int = 200) async -> ArbitrageResponse? {
        return await fetchCached("/arbitrage?limit=\(limit)", cacheKey: "arbitrage")
    }
    
    // MARK: - Contagion
    func contagion() async -> [ContagionEntry] {
        if let r: ContagionResponse = await fetchCached("/contagion", cacheKey: "contagion") {
            return r.results ?? []
        }
        return []
    }
    
    // MARK: - Cache info
    func cacheAge(_ key: String) -> String? { cache.age(key: key) }
    func clearCache() { cache.clearAll() }
    
    // MARK: - Color helpers
    static func scoreColor(_ score: Double) -> String {
        if score >= 70 { return "green" }
        if score >= 42 { return "orange" }
        return "red"
    }
}
