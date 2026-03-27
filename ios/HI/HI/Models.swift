import Foundation

struct Company: Codable, Identifiable, Hashable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?
    let ticker: String?
    let composite: Double?
    let industry: String?
    let sic_description: String?
    let hi_balanced: Bool?
    let hi_grade: String?
    let D_H: Double?
    let D_U: Double?
    let D_M: Double?
    let D_A: Double?
    let D_N: Double?
    let decay_index: Double?
    let decay_level: String?
    let shield_score: Double?
    let shield_tier: String?
    let genome: [String: GenomeDimension]?
    let algo_harm: AlgoHarm?
    let humanwashing_flags: [String]?
    let domains: [String]?
    let data_sources: [String]?
    let confidence: String?
    let _source: String?
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
    static func == (lhs: Company, rhs: Company) -> Bool { lhs.id == rhs.id }
    
    enum CodingKeys: String, CodingKey {
        case company, ticker, composite, industry, sic_description, hi_balanced, hi_grade
        case D_H, D_U, D_M, D_A, D_N
        case decay_index, decay_level, shield_score, shield_tier
        case genome, algo_harm, humanwashing_flags, domains, data_sources, confidence
        case _source
    }
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

struct APIStats: Codable {
    let total_companies: Int?
    let tickers_indexed: Int?
    let data_sources: Int?
    let hi_balanced_count: Int?
    let hi_balanced_threshold: Double?
    let gold_threshold: Double?
}

struct SearchResponse: Codable { let results: [Company]?; let count: Int? }
struct TopBottomResponse: Codable { let results: [Company]?; let count: Int? }

struct HeartbeatPulse: Codable {
    let pulse: String?; let average_decay: Double?
    let alerts_count: Int?; let companies_analyzed: Int?
}
struct HeartbeatAlert: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?; let ticker: String?; let decay_index: Double?
    let decay_level: String?; let current_grade: String?; let factors: [String]?
}
struct HeartbeatAlertsResponse: Codable { let results: [HeartbeatAlert]? }

struct Human100Response: Codable {
    let constituents: [Human100Entry]?; let results: [Human100Entry]?; let metadata: Human100Meta?
}
struct Human100Entry: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?; let ticker: String?; let composite: Double?
    let rank: Int?; let hi_balanced: Bool?
}
struct Human100Meta: Codable { let average: Double?; let median: Double? }

struct MoatResponse: Codable { let results: [MoatEntry]?; let metadata: MoatMeta?; let total: Int? }
struct MoatEntry: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?; let ticker: String?; let moat_score: Double?
    let moat_level: String?; let moat_label: String?; let composite: Double?
    let hi_balanced: Bool?; let components: [String: Double]?; let reasons: [String]?
}
struct MoatMeta: Codable { let distribution: [String: Int]? }

struct ArbitrageResponse: Codable { let results: [ArbitrageEntry]?; let metadata: ArbitrageMeta? }
struct ArbitrageEntry: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?; let ticker: String?; let arbitrage_type: String?
    let arbitrage_label: String?; let hi_composite: Double?; let esg_composite: Double?
    let gap: Double?; let gap_reasons: [String]?
}
struct ArbitrageMeta: Codable { let arbitrage_distribution: [String: Int]? }

struct ContagionResponse: Codable { let results: [ContagionEntry]? }
struct ContagionEntry: Codable, Identifiable {
    var id: String { ticker ?? company ?? UUID().uuidString }
    let company: String?
    let ticker: String?
    let composite: Int?
    let contagion_magnitude: Double?
    let gap_from_industry: Double?
    let industry: String?
    let is_negative_leader: Bool?
    let worst_dimension: String?
}
