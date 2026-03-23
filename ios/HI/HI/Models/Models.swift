import Foundation

// MARK: - Company Score
struct Company: Codable, Identifiable, Hashable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?
    let ticker: String?
    let composite: Double?
    let industry: String?
    let sic_description: String?
    let hi_balanced: Bool?
    let hi_grade: String?
    
    // HUMAN dimensions
    let D_H: Double?
    let D_U: Double?
    let D_M: Double?
    let D_A: Double?
    let D_N: Double?
    
    // Decay
    let decay_index: Double?
    let decay_level: String?
    
    // Shield
    let shield_score: Double?
    let shield_tier: String?
    
    // Genome
    let genome: [String: GenomeDimension]?
    
    // Algo harm
    let algo_harm: AlgoHarm?
    
    // Humanwashing
    let humanwashing_flags: [String]?
    
    // Gates
    let domains: [String]?
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
    static func == (lhs: Company, rhs: Company) -> Bool { lhs.id == rhs.id }
}

struct GenomeDimension: Codable {
    let scores: [String: Double]?
    let avg: Double?
}

struct AlgoHarm: Codable {
    let has_harm: Bool?
    let algo_harm_score: Double?
    let flags: [String]?
    let penalties: [String: Double]?
}

// MARK: - Stats
struct APIStats: Codable {
    let total_companies: Int?
    let tickers_indexed: Int?
    let data_sources: Int?
    let hi_balanced_count: Int?
    let hi_balanced_threshold: Double?
    let gold_threshold: Double?
}

// MARK: - Search
struct SearchResponse: Codable {
    let results: [Company]?
    let count: Int?
}

// MARK: - Heartbeat
struct HeartbeatPulse: Codable {
    let pulse: String?
    let average_decay: Double?
    let alerts_count: Int?
    let companies_analyzed: Int?
}

struct HeartbeatAlert: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?
    let ticker: String?
    let decay_index: Double?
    let decay_level: String?
    let current_grade: String?
    let factors: [String]?
}

struct HeartbeatAlertsResponse: Codable {
    let results: [HeartbeatAlert]?
}

// MARK: - HUMAN 100
struct Human100Response: Codable {
    let constituents: [Human100Entry]?
    let results: [Human100Entry]?
    let metadata: Human100Meta?
}

struct Human100Entry: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?
    let ticker: String?
    let composite: Double?
    let rank: Int?
    let hi_balanced: Bool?
}

struct Human100Meta: Codable {
    let average: Double?
    let median: Double?
}

// MARK: - Moat / Shield
struct MoatResponse: Codable {
    let results: [MoatEntry]?
    let metadata: MoatMeta?
    let total: Int?
}

struct MoatEntry: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?
    let ticker: String?
    let moat_score: Double?
    let moat_level: String?
    let moat_label: String?
    let composite: Double?
    let hi_balanced: Bool?
    let components: [String: Double]?
    let reasons: [String]?
}

struct MoatMeta: Codable {
    let distribution: [String: Int]?
}

// MARK: - Arbitrage / Lens
struct ArbitrageResponse: Codable {
    let results: [ArbitrageEntry]?
    let metadata: ArbitrageMeta?
}

struct ArbitrageEntry: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?
    let ticker: String?
    let arbitrage_type: String?
    let arbitrage_label: String?
    let hi_composite: Double?
    let esg_composite: Double?
    let gap: Double?
    let gap_reasons: [String]?
}

struct ArbitrageMeta: Codable {
    let arbitrage_distribution: [String: Int]?
}

// MARK: - Contagion
struct ContagionResponse: Codable {
    let results: [ContagionEntry]?
}

struct ContagionEntry: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?
    let ticker: String?
    let contagion_score: Double?
    let contagion_type: String?
    let industry: String?
    let composite: Double?
}

// MARK: - Top/Bottom
struct TopBottomResponse: Codable {
    let results: [Company]?
    let count: Int?
}
