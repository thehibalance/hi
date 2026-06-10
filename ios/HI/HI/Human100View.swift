import SwiftUI

struct Human100View: View {
    @Environment(APIService.self) var api
    @State private var entries: [Human100Entry] = []
    @State private var isLoading = true
    
    var body: some View {
        NavigationStack {
            Group {
                if isLoading {
                    ProgressView("Loading HUMAN 100...").frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if entries.isEmpty {
                    Text("No data available.").foregroundColor(.secondary).frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(Array(entries.enumerated()), id: \.offset) { idx, entry in
                        NavigationLink(value: companyFrom(entry)) {
                            h100Row(rank: idx + 1, entry: entry)
                        }
                    }.listStyle(.plain)
                }
            }
            .navigationTitle("HUMAN 100™").navigationBarTitleDisplayMode(.large)
            .navigationDestination(for: Company.self) { CompanyDetailView(company: $0) }
        }
        .task {
            let raw = await api.human100()
            // Deduplicate by ticker, then sort purely by composite desc
            // (◆ Balanced Board members are marked via badge, not rank-inflated)
            var seen = Set<String>()
            let deduped = raw.filter { e in
                guard let ticker = e.ticker, !ticker.isEmpty else { return false }
                guard !seen.contains(ticker) else { return false }
                seen.insert(ticker)
                return true
            }
            entries = deduped.sorted { ($0.composite ?? 0) > ($1.composite ?? 0) }
            isLoading = false
        }
    }
    
    private func h100Row(rank: Int, entry: Human100Entry) -> some View {
        let score = entry.composite ?? 0
        let isGold = entry.hi_balanced == true
        return HStack(spacing: 12) {
            Text("#\(rank)")
                .font(.system(size: 13, weight: .bold, design: .rounded))
                .foregroundColor(.secondary)
                .frame(width: 36, alignment: .leading)
            ZStack {
                Circle()
                    .fill(Color.hiScore(score))
                    .frame(width: 36, height: 36)
                Text("\(Int(score))")
                    .font(.system(size: 13, weight: .heavy, design: .rounded))
                    .foregroundColor(.white)
            }
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 4) {
                    Text(entry.company ?? "")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.hiNavy)
                        .lineLimit(1)
                    if isGold {
                        Text("◆")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(Color.hiGold)
                    }
                }
                if let t = entry.ticker {
                    Text(t).font(.system(size: 11)).foregroundColor(.secondary)
                }
            }
            Spacer()
            Text("\(Int(score))")
                .font(HIFont.score(18))
                .foregroundColor(isGold ? .hiGold : .hiScore(score))
        }
    }
    
    private func companyFrom(_ entry: Human100Entry) -> Company {
        Company(
            company: entry.company, ticker: entry.ticker, composite: entry.composite,
            industry: nil, sic_description: nil, hi_balanced: entry.hi_balanced,
            hi_balanced_threshold: nil, gold_threshold: nil, hi_balanced_gates: nil,
            hi_grade: nil, D_H: nil, D_U: nil, D_M: nil, D_A: nil, D_N: nil,
            decay_index: nil, decay_level: nil, shield_score: nil, shield_tier: nil,
            genome: nil, algo_harm: nil, humanwashing_flags: nil, domains: nil,
            data_sources: nil, confidence: nil, score_status: nil, spec_version: nil, signal_coverage: nil, _source: nil
        )
    }
}
