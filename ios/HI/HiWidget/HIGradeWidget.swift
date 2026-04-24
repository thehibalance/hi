import WidgetKit
import SwiftUI

// MARK: - Widget Data

struct HIGradeEntry: TimelineEntry {
    let date: Date
    let companies: [WidgetCompany]
    let balancedCount: Int
}

struct WidgetCompany: Identifiable {
    let id: String
    let name: String
    let ticker: String
    let score: Int
    let isGold: Bool
}

// MARK: - Timeline Provider

struct HIGradeProvider: TimelineProvider {
    
    private let apiBase = "https://api.thehibalance.org/api/v1"
    
    func placeholder(in context: Context) -> HIGradeEntry {
        HIGradeEntry(date: .now, companies: sampleCompanies, balancedCount: 3)
    }
    
    func getSnapshot(in context: Context, completion: @escaping (HIGradeEntry) -> Void) {
        completion(HIGradeEntry(date: .now, companies: sampleCompanies, balancedCount: 3))
    }
    
    func getTimeline(in context: Context, completion: @escaping (Timeline<HIGradeEntry>) -> Void) {
        Task {
            let companies = await fetchTopCompanies()
            let balancedCount = companies.filter(\.isGold).count
            let entry = HIGradeEntry(date: .now, companies: companies, balancedCount: balancedCount)
            
            // Refresh every 6 hours
            let nextUpdate = Calendar.current.date(byAdding: .hour, value: 6, to: .now)!
            let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
            completion(timeline)
        }
    }
    
    private func fetchTopCompanies() async -> [WidgetCompany] {
        guard let url = URL(string: "\(apiBase)/grades/top?limit=6") else { return sampleCompanies }
        guard let (data, _) = try? await URLSession.shared.data(from: url) else { return sampleCompanies }
        
        struct TopResponse: Codable {
            let results: [TopCompany]?
        }
        struct TopCompany: Codable {
            let company: String?
            let ticker: String?
            let composite: Double?
            let hi_balanced: Bool?
        }
        
        guard let response = try? JSONDecoder().decode(TopResponse.self, from: data),
              let results = response.results else { return sampleCompanies }
        
        // Dedup by ticker (fallback to name) so we never show same company twice
        var seen = Set<String>()
        var unique: [TopCompany] = []
        for c in results {
            let key = (c.ticker?.isEmpty == false ? c.ticker! : (c.company ?? ""))
            if !key.isEmpty && !seen.contains(key) {
                seen.insert(key)
                unique.append(c)
                if unique.count >= 6 { break }
            }
        }
        return unique.map { c in
            WidgetCompany(
                id: (c.ticker?.isEmpty == false ? c.ticker! : "") + "|" + (c.company ?? ""),
                name: c.company ?? "Unknown",
                ticker: c.ticker ?? "",
                score: Int(c.composite ?? 0),
                isGold: c.hi_balanced == true
            )
        }
    }
    
    private var sampleCompanies: [WidgetCompany] {
        [
            WidgetCompany(id: "JNJ", name: "Johnson & Johnson", ticker: "JNJ", score: 77, isGold: true),
            WidgetCompany(id: "PEP", name: "PepsiCo", ticker: "PEP", score: 75, isGold: true),
            WidgetCompany(id: "SBUX", name: "Starbucks", ticker: "SBUX", score: 72, isGold: true),
            WidgetCompany(id: "BAC", name: "Bank of America", ticker: "BAC", score: 70, isGold: true),
            WidgetCompany(id: "AAPL", name: "Apple", ticker: "AAPL", score: 49, isGold: false),
            WidgetCompany(id: "META", name: "Meta", ticker: "META", score: 41, isGold: false),
        ]
    }
}

// MARK: - Score Color

private func scoreColor(_ score: Int) -> Color {
    if score >= 70 { return Color(red: 0.086, green: 0.639, blue: 0.247) }
    if score >= 42 { return Color(red: 0.851, green: 0.467, blue: 0.024) }
    return Color(red: 0.863, green: 0.145, blue: 0.145)
}

private let navy = Color(red: 0.106, green: 0.227, blue: 0.361)
private let gold = Color(red: 0.769, green: 0.608, blue: 0.125)

// MARK: - Small Widget

struct HIGradeSmallView: View {
    let entry: HIGradeEntry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("hi.")
                    .font(.system(size: 16, weight: .black, design: .rounded))
                    .foregroundColor(navy)
                Spacer()
                if entry.balancedCount > 0 {
                    Text("◆ \(entry.balancedCount)")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(gold)
                }
            }
            
            ForEach(entry.companies.prefix(4)) { c in
                HStack(spacing: 6) {
                    ZStack {
                        Circle()
                            .fill(c.isGold ? gold : scoreColor(c.score))
                            .frame(width: 22, height: 22)
                        Text("\(c.score)")
                            .font(.system(size: 9, weight: .heavy, design: .rounded))
                            .foregroundColor(.white)
                    }
                    Text(c.ticker)
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(navy)
                        .lineLimit(1)
                    Spacer()
                    Text("\(c.score)")
                        .font(.system(size: 11, weight: .heavy, design: .rounded))
                        .foregroundColor(c.isGold ? gold : scoreColor(c.score))
                }
            }
        }
        .padding(12)
    }
}

// MARK: - Medium Widget

struct HIGradeMediumView: View {
    let entry: HIGradeEntry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("hi.")
                    .font(.system(size: 18, weight: .black, design: .rounded))
                    .foregroundColor(navy)
                Text("Top HI Grades")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.secondary)
                Spacer()
                Text("◆ \(entry.balancedCount) Balanced")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(gold)
            }
            
            HStack(spacing: 12) {
                VStack(spacing: 4) {
                    ForEach(Array(entry.companies.prefix(3).enumerated()), id: \.element.id) { idx, c in
                        companyRow(rank: idx + 1, company: c)
                    }
                }
                VStack(spacing: 4) {
                    ForEach(Array(entry.companies.dropFirst(3).prefix(3).enumerated()), id: \.element.id) { idx, c in
                        companyRow(rank: idx + 4, company: c)
                    }
                }
            }
        }
        .padding(12)
    }
    
    private func companyRow(rank: Int, company: WidgetCompany) -> some View {
        HStack(spacing: 6) {
            Text("#\(rank)")
                .font(.system(size: 9, weight: .bold, design: .rounded))
                .foregroundColor(.secondary)
                .frame(width: 16)
            ZStack {
                Circle()
                    .fill(company.isGold ? gold : scoreColor(company.score))
                    .frame(width: 20, height: 20)
                Text("\(company.score)")
                    .font(.system(size: 8, weight: .heavy, design: .rounded))
                    .foregroundColor(.white)
            }
            Text(company.name)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(navy)
                .lineLimit(1)
            Spacer()
        }
    }
}

// MARK: - Widget Configuration

struct HIGradeWidget: Widget {
    let kind = "HIGradeWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: HIGradeProvider()) { entry in
            if #available(iOS 17.0, *) {
                Group {
                    switch entry.companies.count > 3 {
                    case true: HIGradeMediumView(entry: entry)
                    case false: HIGradeSmallView(entry: entry)
                    }
                }
                .containerBackground(.fill.tertiary, for: .widget)
            } else {
                HIGradeSmallView(entry: entry)
                    .padding()
                    .background()
            }
        }
        .configurationDisplayName("HI Grade")
        .description("Top companies by Human Intelligence score")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

// MARK: - Entry Point

@main
struct HIWidgetBundle: WidgetBundle {
    var body: some Widget {
        HIGradeWidget()
    }
}
