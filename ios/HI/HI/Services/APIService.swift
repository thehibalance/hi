import Foundation

class APIService: ObservableObject {
    static let shared = APIService()
    private let base = "https://api.thehibalance.org/api/v1"
    
    @Published var stats: APIStats?
    @Published var isLoading = false
    
    var goldThreshold: Double { stats?.gold_threshold ?? stats?.hi_balanced_threshold ?? 72 }
    
    // MARK: - Generic fetch
    private func fetch<T: Codable>(_ path: String) async throws -> T {
        guard let url = URL(string: base + path) else { throw URLError(.badURL) }
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(T.self, from: data)
    }
    
    // MARK: - Stats
    func loadStats() async {
        do {
            let s: APIStats = try await fetch("/stats")
            await MainActor.run { self.stats = s }
        } catch { print("Stats error: \(error)") }
    }
    
    // MARK: - Search
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
        do { return try await fetch("/score/ticker/\(ticker)") }
        catch { return nil }
    }
    
    // MARK: - Score by domain
    func score(domain: String) async -> Company? {
        do { return try await fetch("/score/\(domain)") }
        catch { return nil }
    }
    
    // MARK: - Top companies
    func top(limit: Int = 100) async -> [Company] {
        do {
            let r: TopBottomResponse = try await fetch("/grades/top?limit=\(limit)")
            return r.results ?? []
        } catch { return [] }
    }
    
    // MARK: - Bottom companies
    func bottom(limit: Int = 50) async -> [Company] {
        do {
            let r: TopBottomResponse = try await fetch("/grades/bottom?limit=\(limit)")
            return r.results ?? []
        } catch { return [] }
    }
    
    // MARK: - Heartbeat
    func heartbeatPulse() async -> HeartbeatPulse? {
        do { return try await fetch("/heartbeat/pulse") }
        catch { return nil }
    }
    
    func heartbeatAlerts(limit: Int = 40) async -> [HeartbeatAlert] {
        do {
            let r: HeartbeatAlertsResponse = try await fetch("/heartbeat/alerts?limit=\(limit)")
            return r.results ?? []
        } catch { return [] }
    }
    
    // MARK: - HUMAN 100
    func human100() async -> [Human100Entry] {
        do {
            let r: Human100Response = try await fetch("/human100")
            return r.constituents ?? r.results ?? []
        } catch { return [] }
    }
    
    // MARK: - Shield / Moat
    func moat(limit: Int = 900) async -> MoatResponse? {
        do { return try await fetch("/moat?limit=\(limit)") }
        catch { return nil }
    }
    
    // MARK: - Lens / Arbitrage
    func arbitrage(limit: Int = 200) async -> ArbitrageResponse? {
        do { return try await fetch("/arbitrage?limit=\(limit)") }
        catch { return nil }
    }
    
    // MARK: - Contagion
    func contagion() async -> [ContagionEntry] {
        do {
            let r: ContagionResponse = try await fetch("/contagion")
            return r.results ?? []
        } catch { return [] }
    }
    
    // MARK: - Color helpers
    static func scoreColor(_ score: Double) -> String {
        if score >= 70 { return "green" }
        if score >= 42 { return "orange" }
        return "red"
    }
}
