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
                        let comp = makeCompany(from: entry)
                        NavigationLink(value: comp) {
                            HStack(spacing: 12) {
                                Text("#\(idx + 1)").font(.system(size: 13, weight: .bold, design: .rounded)).foregroundColor(.secondary).frame(width: 36, alignment: .leading)
                                let isGold = entry.hi_balanced == true
                                let score = entry.composite ?? 0
                                Circle().fill(isGold ? Color.hiGold : Color.hiScore(score)).frame(width: 36, height: 36)
                                    .overlay(isGold ? AnyView(Text("✦").font(.system(size: 14)).foregroundColor(.white)) : AnyView(Text("\(Int(score))").font(.system(size: 13, weight: .heavy, design: .rounded)).foregroundColor(.white)))
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(entry.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy).lineLimit(1)
                                    if let t = entry.ticker { Text(t).font(.system(size: 11)).foregroundColor(.secondary) }
                                }
                                Spacer()
                                Text("\(Int(score))").font(HIFont.score(18)).foregroundColor(isGold ? .hiGold : .hiScore(score))
                            }
                        }
                    }.listStyle(.plain)
                }
            }
            .navigationTitle("HUMAN 100")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.large)
            #endif
            .navigationDestination(for: Company.self) { CompanyDetailView(company: $0) }
        }
        .task { entries = await api.human100(); isLoading = false }
    }
    
    private func makeCompany(from entry: Human100Entry) -> Company {
        .stub(company: entry.company, ticker: entry.ticker, composite: entry.composite, hi_balanced: entry.hi_balanced)
    }
}
