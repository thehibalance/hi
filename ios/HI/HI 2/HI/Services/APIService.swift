import Foundation
import Observation

@Observable
class APIService {
    static let shared = APIService()
    private let base = "https://api.thehibalance.org/api/v1"
    private let cache = CacheManager.shared
    
    var stats: APIStats?
    var isLoading = false
    var isOffline = false
    
    var goldThreshold: Double { stats?.gold_threshold ?? stats?.hi_balanced_threshold ?? 72 }
    
    private func fetch<T: Codable>(_ path: String, cacheKey: String? = nil) async throws -> T {
        if let key = cacheKey, let cached: T = cache.load(T.self, key: key) { return cached }
        guard let url = URL(string: base + path) else { throw URLError(.badURL) }
        let (data, _) = try await URLSession.shared.data(from: url)
        let result = try JSONDecoder().decode(T.self, from: data)
        if let key = cacheKey { cache.save(result, key: key) }
        return result
    }
    
    private func fetchCached<T: Codable>(_ path: String, cacheKey: String) async -> T? {
        do { return try await fetch(path, cacheKey: cacheKey) }
        catch { return cache.load(T.self, key: cacheKey) }
    }
    
    func loadStats() async {
        if let s: APIStats = await fetchCached("/stats", cacheKey: "stats") {
            self.stats = s
        }
    }
    
    func search(_ query: String) async -> [Company] {
        guard !query.isEmpty else { return [] }
        let q = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        do { let r: SearchResponse = try await fetch("/search?q=\(q)&limit=20"); return r.results ?? [] }
        catch { return [] }
    }
    
    func score(ticker: String) async -> Company? {
        do { return try await fetch("/score/ticker/\(ticker)", cacheKey: "score_\(ticker)") }
        catch { return nil }
    }
    
    func top(limit: Int = 100) async -> [Company] {
        if let r: TopBottomResponse = await fetchCached("/grades/top?limit=\(limit)", cacheKey: "top_\(limit)") { return r.results ?? [] }
        return []
    }
    
    func heartbeatPulse() async -> HeartbeatPulse? { await fetchCached("/heartbeat/pulse", cacheKey: "hb_pulse") }
    
    func heartbeatAlerts(limit: Int = 40) async -> [HeartbeatAlert] {
        if let r: HeartbeatAlertsResponse = await fetchCached("/heartbeat/alerts?limit=\(limit)", cacheKey: "hb_alerts") { return r.results ?? [] }
        return []
    }
    
    func human100() async -> [Human100Entry] {
        if let r: Human100Response = await fetchCached("/human100", cacheKey: "human100") { return r.constituents ?? r.results ?? [] }
        return []
    }
    
    func moat(limit: Int = 900) async -> MoatResponse? { await fetchCached("/moat?limit=\(limit)", cacheKey: "moat") }
    func arbitrage(limit: Int = 200) async -> ArbitrageResponse? { await fetchCached("/arbitrage?limit=\(limit)", cacheKey: "arbitrage") }
    
    func contagion() async -> [ContagionEntry] {
        if let r: ContagionResponse = await fetchCached("/contagion", cacheKey: "contagion") { return r.results ?? [] }
        return []
    }
}
