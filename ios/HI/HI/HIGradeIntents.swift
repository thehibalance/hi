import AppIntents
import Foundation

// MARK: - Get HI Grade Intent (Entity-based — enables "HI Grade Starbucks" directly)

struct GetHIGradeIntent: AppIntent {
    static var title: LocalizedStringResource = "Get HI Grade"
    static var description = IntentDescription(
        "Look up a company's Human Intelligence score",
        categoryName: "HI Grade™"
    )
    static var openAppWhenRun: Bool = false
    
    static var parameterSummary: some ParameterSummary {
        Summary("Get HI Grade for \(\.$company)")
    }
    
    @Parameter(title: "Company", requestValueDialog: "Which company?")
    var company: CompanyEntity
    
    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog {
        let api = APIService.shared
        
        // Fetch full company data
        var fullCompany: Company?
        if !company.ticker.isEmpty {
            fullCompany = await api.score(ticker: company.ticker)
        }
        if fullCompany == nil {
            let results = await api.search(company.name)
            if let ticker = results.first?.ticker {
                fullCompany = await api.score(ticker: ticker)
            }
        }
        
        let c = fullCompany
        let score = c.map { Int($0.composite ?? 0) } ?? company.score
        let name = c?.company ?? company.name
        let isGold = c?.hi_balanced ?? company.isGold
        let sources = c?.data_sources?.count ?? 0
        let confidence = c?.confidence ?? "Estimated"
        
        // Build dimension summary
        var dims: [String] = []
        if let h = c?.D_H { dims.append("H:\(Int(h))") }
        if let u = c?.D_U { dims.append("U:\(Int(u))") }
        if let m = c?.D_M { dims.append("M:\(Int(m))") }
        if let a = c?.D_A { dims.append("A:\(Int(a))") }
        if let n = c?.D_N { dims.append("N:\(Int(n))") }
        let dimString = dims.isEmpty ? "" : "\n" + dims.joined(separator: " · ")
        
        let goldBadge = isGold ? " 🥇 Gold HI Grade" : ""
        let summary = "\(name): \(score)/100\(goldBadge)\(dimString)\n\(confidence) · \(sources) sources"
        
        let dialog = isGold
            ? "\(name) has a Gold HI Grade with a score of \(score) out of 100."
            : "\(name) has a HI Grade of \(score) out of 100."
        
        return .result(value: summary, dialog: IntentDialog(stringLiteral: dialog))
    }
}

// MARK: - Quick Score Intent (Entity-based)

struct QuickHIGradeIntent: AppIntent {
    static var title: LocalizedStringResource = "Quick HI Grade"
    static var description = IntentDescription(
        "Quickly check a company's HI Grade score",
        categoryName: "HI Grade™"
    )
    static var openAppWhenRun: Bool = false
    
    static var parameterSummary: some ParameterSummary {
        Summary("Quick score for \(\.$company)")
    }
    
    @Parameter(title: "Company", requestValueDialog: "Company name or ticker?")
    var company: CompanyEntity
    
    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let api = APIService.shared
        
        var fullCompany: Company?
        if !company.ticker.isEmpty {
            fullCompany = await api.score(ticker: company.ticker)
        }
        if fullCompany == nil {
            let results = await api.search(company.name)
            if let ticker = results.first?.ticker {
                fullCompany = await api.score(ticker: ticker)
            }
        }
        
        let score = fullCompany.map { Int($0.composite ?? 0) } ?? company.score
        let name = fullCompany?.company ?? company.name
        let isGold = fullCompany?.hi_balanced ?? company.isGold
        
        if isGold {
            return .result(dialog: "\(name): \(score). Gold HI Grade.")
        } else if score >= 55 {
            return .result(dialog: "\(name): \(score) out of 100.")
        } else if score >= 42 {
            return .result(dialog: "\(name): \(score). Below average on human intelligence.")
        } else {
            return .result(dialog: "\(name): \(score). Significant concerns.")
        }
    }
}

// MARK: - Get HI Grade for App Intent (Bundle ID resolver for automations)

struct GetHIGradeForAppIntent: AppIntent {
    static var title: LocalizedStringResource = "Get HI Grade for App"
    static var description = IntentDescription(
        "Get the HI Grade for the company behind an app",
        categoryName: "HI Grade™"
    )
    static var openAppWhenRun: Bool = false
    
    static var parameterSummary: some ParameterSummary {
        Summary("Get HI Grade for app \(\.$bundleID)")
    }
    
    @Parameter(title: "App Bundle ID", description: "The bundle identifier of the app", requestValueDialog: "Which app's bundle ID?")
    var bundleID: String
    
    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog {
        guard let ticker = BundleMapping.ticker(for: bundleID) else {
            let appName = BundleMapping.appName(for: bundleID) ?? bundleID
            return .result(
                value: "Unknown",
                dialog: "I don't have a HI Grade mapping for \(appName) yet."
            )
        }
        
        let api = APIService.shared
        guard let company = await api.score(ticker: ticker) else {
            return .result(
                value: "Not found",
                dialog: "Couldn't load HI Grade for ticker \(ticker)."
            )
        }
        
        let score = Int(company.composite ?? 0)
        let name = company.company ?? ticker
        let isGold = company.hi_balanced == true
        let appName = BundleMapping.appName(for: bundleID) ?? name
        
        let goldBadge = isGold ? " 🥇 Gold" : ""
        let summary = "\(appName) (\(name)): \(score)/100\(goldBadge)"
        
        let dialog = isGold
            ? "\(appName) by \(name) has a Gold HI Grade of \(score)."
            : "\(appName) by \(name) has a HI Grade of \(score) out of 100."
        
        return .result(value: summary, dialog: IntentDialog(stringLiteral: dialog))
    }
}

// MARK: - Search HI Grade (Text-based fallback for Shortcuts)

struct SearchHIGradeIntent: AppIntent {
    static var title: LocalizedStringResource = "Search HI Grade"
    static var description = IntentDescription(
        "Search for a company by name or ticker",
        categoryName: "HI Grade™"
    )
    static var openAppWhenRun: Bool = false
    
    static var parameterSummary: some ParameterSummary {
        Summary("Search HI Grade for \(\.$query)")
    }
    
    @Parameter(title: "Search", requestValueDialog: "Company name or ticker?")
    var query: String
    
    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog {
        let api = APIService.shared
        let input = query.trimmingCharacters(in: .whitespacesAndNewlines)
        
        var company: Company?
        if input.count <= 5 && input == input.uppercased() {
            company = await api.score(ticker: input)
        }
        if company == nil {
            let results = await api.search(input)
            if let ticker = results.first?.ticker {
                company = await api.score(ticker: ticker) ?? results.first
            } else {
                company = results.first
            }
        }
        
        guard let c = company else {
            return .result(value: "Not found", dialog: "No HI Grade found for \(query).")
        }
        
        let score = Int(c.composite ?? 0)
        let name = c.company ?? query
        let isGold = c.hi_balanced == true
        let goldBadge = isGold ? " 🥇 Gold" : ""
        
        return .result(
            value: "\(name): \(score)/100\(goldBadge)",
            dialog: IntentDialog(stringLiteral: "\(name) has a HI Grade of \(score) out of 100.")
        )
    }
}
