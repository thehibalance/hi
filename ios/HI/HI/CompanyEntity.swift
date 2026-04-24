import AppIntents
import Foundation

// MARK: - Company Entity

struct CompanyEntity: AppEntity {
    static var typeDisplayRepresentation = TypeDisplayRepresentation(name: "Company")
    static var defaultQuery = CompanyEntityQuery()
    
    var id: String
    
    @Property(title: "Company Name")
    var name: String
    
    @Property(title: "Ticker")
    var ticker: String
    
    @Property(title: "Score")
    var score: Int
    
    @Property(title: "Is Gold")
    var isGold: Bool
    
    var displayRepresentation: DisplayRepresentation {
        let subtitle = isGold ? "🥇 Gold · \(score)/100" : "\(score)/100"
        return DisplayRepresentation(
            title: "\(name)",
            subtitle: "\(subtitle)"
        )
    }
    
    init(id: String, name: String, ticker: String, score: Int, isGold: Bool) {
        self.id = id
        self.name = name
        self.ticker = ticker
        self.score = score
        self.isGold = isGold
    }
    
    init(from company: Company) {
        self.id = company.ticker ?? company.company ?? UUID().uuidString
        self.name = company.company ?? "Unknown"
        self.ticker = company.ticker ?? ""
        self.score = Int(company.composite ?? 0)
        self.isGold = company.hi_balanced == true
    }
}

// MARK: - Lightweight API helper (non-MainActor, safe for entity queries)

private enum HIFetch {
    static let base = "https://api.thehibalance.org/api/v1"
    
    static func score(ticker: String) async -> Company? {
        guard let url = URL(string: "\(base)/score/ticker/\(ticker)") else { return nil }
        guard let (data, _) = try? await URLSession.shared.data(from: url) else { return nil }
        return try? JSONDecoder().decode(Company.self, from: data)
    }
    
    static func search(_ query: String) async -> [Company] {
        let q = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        guard let url = URL(string: "\(base)/search?q=\(q)&limit=10") else { return [] }
        guard let (data, _) = try? await URLSession.shared.data(from: url) else { return [] }
        let response = try? JSONDecoder().decode(SearchResponse.self, from: data)
        return response?.results ?? []
    }
    
    static func top(limit: Int = 20) async -> [Company] {
        guard let url = URL(string: "\(base)/grades/top?limit=\(limit)") else { return [] }
        guard let (data, _) = try? await URLSession.shared.data(from: url) else { return [] }
        let response = try? JSONDecoder().decode(TopBottomResponse.self, from: data)
        return response?.results ?? []
    }
}

// MARK: - Entity Query

struct CompanyEntityQuery: EntityQuery {
    
    func entities(for identifiers: [String]) async throws -> [CompanyEntity] {
        var results: [CompanyEntity] = []
        
        for id in identifiers {
            if let company = await HIFetch.score(ticker: id.uppercased()) {
                results.append(CompanyEntity(from: company))
            } else {
                let search = await HIFetch.search(id)
                if let first = search.first {
                    if let ticker = first.ticker, let full = await HIFetch.score(ticker: ticker) {
                        results.append(CompanyEntity(from: full))
                    } else {
                        results.append(CompanyEntity(from: first))
                    }
                }
            }
        }
        return results
    }
    
    func suggestedEntities() async throws -> [CompanyEntity] {
        let top = await HIFetch.top(limit: 20)
        return top.compactMap { c in
            guard (c.composite ?? 0) > 0 else { return nil }
            return CompanyEntity(from: c)
        }
    }
}

// MARK: - String Search Extension

extension CompanyEntityQuery: EntityStringQuery {
    
    func entities(matching string: String) async throws -> [CompanyEntity] {
        let input = string.trimmingCharacters(in: .whitespacesAndNewlines)
        
        if input.count <= 5 && input == input.uppercased() {
            if let company = await HIFetch.score(ticker: input) {
                return [CompanyEntity(from: company)]
            }
        }
        
        let results = await HIFetch.search(input)
        return results.prefix(8).map { CompanyEntity(from: $0) }
    }
}
