import SwiftUI

struct Human100View: View {
    @Environment(APIService.self) var api
    @State private var entries: [Human100Entry] = []
    @State private var isLoading = true
    
    var body: some View {
        NavigationStack {
            Group {
                if isLoading { ProgressView("Loading HUMAN 100...").frame(maxWidth: .infinity, maxHeight: .infinity) }
                else if entries.isEmpty { Text("No data available.").foregroundColor(.secondary).frame(maxWidth: .infinity, maxHeight: .infinity) }
                else {
                    List(Array(entries.enumerated()), id: \.element.id) { idx, entry in
                        NavigationLink(value: Company(company: entry.company, ticker: entry.ticker, composite: entry.composite, industry: nil, sic_description: nil, hi_balanced: entry.hi_balanced, hi_grade: nil, D_H: nil, D_U: nil, D_M: nil, D_A: nil, D_N: nil, decay_index: nil, decay_level: nil, shield_score: nil, shield_tier: nil, genome: nil, algo_harm: nil, humanwashing_flags: nil, domains: nil, data_sources: nil, confidence: nil, _source: nil)) {
                            HStack(spacing: 12) {
                                Text("#\(idx + 1)").font(.system(size: 13, weight: .bold, design: .rounded)).foregroundColor(.secondary).frame(width: 36, alignment: .leading)
                                Circle().fill(entry.hi_balanced == true ? Color.hiGold : Color.hiScore(entry.composite ?? 0)).frame(width: 36, height: 36)
                                    .overlay(entry.hi_balanced == true ? AnyView(Text("✦").font(.system(size: 14)).foregroundColor(.white)) : AnyView(Text("\(Int(entry.composite ?? 0))").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundColor(.white)))
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(entry.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy).lineLimit(1)
                                    if let t = entry.ticker { Text(t).font(.system(size: 11)).foregroundColor(.secondary) }
                                }
                                Spacer()
                                Text("\(Int(entry.composite ?? 0))").font(HIFont.score(18)).foregroundColor(entry.hi_balanced == true ? .hiGold : .hiScore(entry.composite ?? 0))
                            }
                        }
                    }.listStyle(.plain)
                }
            }
            .navigationTitle("HUMAN 100").navigationBarTitleDisplayMode(.large)
            .navigationDestination(for: Company.self) { CompanyDetailView(company: $0) }
        }
        .task { entries = await api.human100(); isLoading = false }
    }
}
