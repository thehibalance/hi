import SwiftUI

struct FeaturesView: View {
    var body: some View {
        NavigationStack {
            List {
                Section {
                    NavigationLink { ShieldView() } label: {
                        FeatureRow(icon: "🏰", title: "HUMAN Shield", desc: "Ethical moat depth")
                    }
                    NavigationLink { LensView() } label: {
                        FeatureRow(icon: "🔎", title: "HUMAN Lens", desc: "ESG vs HI gaps")
                    }
                    NavigationLink { HeartbeatView() } label: {
                        FeatureRow(icon: "💓", title: "Heartbeat", desc: "Score decay monitoring")
                    }
                    NavigationLink { ContagionView() } label: {
                        FeatureRow(icon: "🦠", title: "Contagion", desc: "Industry-wide effects")
                    }
                    NavigationLink { IndustryView() } label: {
                        FeatureRow(icon: "📊", title: "Industry Benchmarks", desc: "Consciousness by sector")
                    }
                } header: {
                    Text("HUMAN FEATURES")
                }
            }
            .listStyle(.insetGrouped)
            .navigationTitle("Features")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let desc: String
    
    var body: some View {
        HStack(spacing: 12) {
            Text(icon).font(.system(size: 24))
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 15, weight: .semibold)).foregroundColor(.hiNavy)
                Text(desc).font(.system(size: 12)).foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Shield View
struct ShieldView: View {
    @EnvironmentObject var api: APIService
    @State private var entries: [MoatEntry] = []
    @State private var dist: [String: Int] = [:]
    @State private var filter = "all"
    @State private var isLoading = true
    
    let tiers = ["all", "fortress", "strong", "developing", "vulnerable"]
    let icons: [String: String] = ["fortress": "🏰", "strong": "🛡", "developing": "⚔", "vulnerable": "📄"]
    
    var filtered: [MoatEntry] {
        if filter == "all" { return entries }
        return entries.filter { m in
            let ml = m.moat_level ?? ""
            return ml == filter || (filter == "developing" && ml == "moderate") || (filter == "vulnerable" && ml == "thin")
        }
    }
    
    var body: some View {
        VStack(spacing: 0) {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(tiers, id: \.self) { tier in
                        Button {
                            filter = tier
                        } label: {
                            VStack(spacing: 2) {
                                Text(icons[tier] ?? "📋").font(.system(size: 18))
                                Text("\(dist[tier] ?? (tier == "all" ? entries.count : 0))")
                                    .font(.system(size: 16, weight: .heavy))
                                Text(tier.capitalized).font(.system(size: 10, weight: .medium))
                            }
                            .padding(.horizontal, 14)
                            .padding(.vertical, 8)
                            .background(filter == tier ? Color.hiNavy : Color(.systemGray6))
                            .foregroundColor(filter == tier ? .white : .primary)
                            .cornerRadius(10)
                        }
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
            }
            
            if isLoading {
                ProgressView().frame(maxHeight: .infinity)
            } else {
                List(filtered) { entry in
                    HStack(spacing: 12) {
                        Text("\(Int(entry.moat_score ?? 0))")
                            .font(HIFont.score(20))
                            .foregroundColor(.hiScore(entry.moat_score ?? 0))
                            .frame(width: 40)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(entry.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy)
                            Text(entry.moat_label ?? "").font(.system(size: 11)).foregroundColor(.hiScore(entry.moat_score ?? 0))
                            if let r = entry.reasons?.first { Text(r).font(.system(size: 10)).foregroundColor(.secondary).lineLimit(1) }
                        }
                        Spacer()
                        Text("\(Int(entry.composite ?? 0))").font(.system(size: 14, weight: .bold)).foregroundColor(.secondary)
                    }
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("HUMAN Shield")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if let r = await api.moat() {
                entries = r.results ?? []
                dist = r.metadata?.distribution ?? [:]
                dist["all"] = entries.count
            }
            isLoading = false
        }
    }
}

// MARK: - Lens View
struct LensView: View {
    @EnvironmentObject var api: APIService
    @State private var entries: [ArbitrageEntry] = []
    @State private var filter = "all"
    @State private var isLoading = true
    
    let types = ["all", "esg_washing", "hidden_gem", "aligned"]
    let labels: [String: String] = ["all": "All", "esg_washing": "🔴 ESG Washing", "hidden_gem": "💎 Hidden Gems", "aligned": "✅ Aligned"]
    
    var filtered: [ArbitrageEntry] {
        if filter == "all" { return entries }
        return entries.filter { $0.arbitrage_type == filter }
    }
    
    var body: some View {
        VStack(spacing: 0) {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(types, id: \.self) { t in
                        Button { filter = t } label: {
                            Text(labels[t] ?? t)
                                .font(.system(size: 12, weight: .semibold))
                                .padding(.horizontal, 14)
                                .padding(.vertical, 8)
                                .background(filter == t ? Color.hiNavy : Color(.systemGray6))
                                .foregroundColor(filter == t ? .white : .primary)
                                .cornerRadius(16)
                        }
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
            }
            
            if isLoading {
                ProgressView().frame(maxHeight: .infinity)
            } else {
                List(filtered) { entry in
                    HStack(spacing: 10) {
                        let icons: [String: String] = ["esg_washing": "🔴", "hidden_gem": "💎", "aligned": "✅", "double_risk": "⚠"]
                        Text(icons[entry.arbitrage_type ?? ""] ?? "·").font(.system(size: 16))
                        VStack(alignment: .leading, spacing: 2) {
                            Text(entry.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy).lineLimit(1)
                            Text(entry.arbitrage_label ?? "").font(.system(size: 11)).foregroundColor(.secondary)
                            if let r = entry.gap_reasons?.first { Text(r).font(.system(size: 10)).foregroundColor(.secondary).lineLimit(1) }
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 2) {
                            Text("ESG: \(Int(entry.esg_composite ?? 0))").font(.system(size: 11)).foregroundColor(.secondary)
                            Text("HI: \(Int(entry.hi_composite ?? 0))").font(.system(size: 11, weight: .bold)).foregroundColor(.hiNavy)
                        }
                    }
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("HUMAN Lens")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if let r = await api.arbitrage() { entries = r.results ?? [] }
            isLoading = false
        }
    }
}

// MARK: - Heartbeat View
struct HeartbeatView: View {
    @EnvironmentObject var api: APIService
    @State private var pulse: HeartbeatPulse?
    @State private var alerts: [HeartbeatAlert] = []
    @State private var isLoading = true
    
    var body: some View {
        VStack(spacing: 0) {
            // Pulse header
            if let p = pulse {
                HStack(spacing: 20) {
                    VStack {
                        Text((p.pulse ?? "unknown").uppercased())
                            .font(.system(size: 16, weight: .heavy))
                            .foregroundColor(p.pulse == "healthy" ? .hiGreen : p.pulse == "elevated" ? .hiOrange : .hiRed)
                        Text("Ecosystem").font(.system(size: 10)).foregroundColor(.secondary)
                    }
                    VStack {
                        Text("\(Int(p.average_decay ?? 0))")
                            .font(.system(size: 20, weight: .heavy, design: .rounded))
                            .foregroundColor(.hiNavy)
                        Text("Avg Decay").font(.system(size: 10)).foregroundColor(.secondary)
                    }
                    VStack {
                        Text("\(p.alerts_count ?? 0)")
                            .font(.system(size: 20, weight: .heavy, design: .rounded))
                            .foregroundColor(.hiOrange)
                        Text("Alerts").font(.system(size: 10)).foregroundColor(.secondary)
                    }
                    VStack {
                        Text("\(p.companies_analyzed ?? 0)")
                            .font(.system(size: 20, weight: .heavy, design: .rounded))
                            .foregroundColor(.hiNavy)
                        Text("Tracked").font(.system(size: 10)).foregroundColor(.secondary)
                    }
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color(.systemBackground))
            }
            
            if isLoading {
                ProgressView().frame(maxHeight: .infinity)
            } else {
                List(alerts) { alert in
                    HStack(spacing: 12) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 8)
                                .fill((alert.decay_level == "critical" ? Color.hiRed : Color.hiOrange).opacity(0.15))
                                .frame(width: 44, height: 44)
                            Text("\(Int(alert.decay_index ?? 0))")
                                .font(.system(size: 16, weight: .heavy, design: .rounded))
                                .foregroundColor(alert.decay_level == "critical" ? .hiRed : .hiOrange)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text(alert.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy)
                            Text("\(alert.current_grade ?? "") · \((alert.decay_level ?? "watch").capitalized)")
                                .font(.system(size: 11)).foregroundColor(.secondary)
                            if let f = alert.factors?.first { Text(f).font(.system(size: 10)).foregroundColor(.secondary).lineLimit(1) }
                        }
                    }
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("Heartbeat")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            async let p = api.heartbeatPulse()
            async let a = api.heartbeatAlerts()
            pulse = await p
            alerts = await a
            isLoading = false
        }
    }
}

// MARK: - Contagion View
struct ContagionView: View {
    @EnvironmentObject var api: APIService
    @State private var entries: [ContagionEntry] = []
    @State private var isLoading = true
    
    var body: some View {
        Group {
            if isLoading {
                ProgressView().frame(maxHeight: .infinity)
            } else {
                List(entries) { entry in
                    HStack(spacing: 12) {
                        Text("\(Int(entry.contagion_score ?? 0))")
                            .font(HIFont.score(18))
                            .foregroundColor(.hiScore(entry.contagion_score ?? 0))
                            .frame(width: 36)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(entry.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy)
                            HStack(spacing: 4) {
                                Text(entry.contagion_type ?? "").font(.system(size: 11, weight: .medium))
                                if let i = entry.industry { Text("· \(i)").font(.system(size: 11)).foregroundColor(.secondary) }
                            }
                        }
                        Spacer()
                        Text("\(Int(entry.composite ?? 0))").font(.system(size: 13, weight: .bold)).foregroundColor(.secondary)
                    }
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("Contagion")
        .navigationBarTitleDisplayMode(.inline)
        .task { entries = await api.contagion(); isLoading = false }
    }
}

// MARK: - Industry Benchmarks View
struct IndustryView: View {
    @EnvironmentObject var api: APIService
    @State private var industries: [(name: String, avg: Int, count: Int, companies: [Company])] = []
    @State private var isLoading = true
    
    var body: some View {
        Group {
            if isLoading {
                ProgressView().frame(maxHeight: .infinity)
            } else {
                List(industries, id: \.name) { ind in
                    DisclosureGroup {
                        ForEach(ind.companies) { c in
                            HStack {
                                Text(c.company ?? "").font(.system(size: 13)).lineLimit(1)
                                Spacer()
                                Text("\(Int(c.composite ?? 0))")
                                    .font(.system(size: 13, weight: .heavy))
                                    .foregroundColor(c.hi_balanced == true ? .hiGold : .hiScore(c.composite ?? 0))
                            }
                        }
                    } label: {
                        HStack(spacing: 12) {
                            Text("\(ind.avg)")
                                .font(HIFont.score(22))
                                .foregroundColor(.hiScore(Double(ind.avg)))
                                .frame(width: 40)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(ind.name).font(.system(size: 14, weight: .bold)).foregroundColor(.hiNavy)
                                Text("\(ind.count) companies · avg \(ind.avg)").font(.system(size: 11)).foregroundColor(.secondary)
                            }
                        }
                    }
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("Industry Benchmarks")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            let all = await api.top(limit: 900)
            let norm: [String: String] = [
                "beverage": "Food & Beverage", "food": "Food & Beverage", "beverages": "Food & Beverage",
                "snacks": "Food & Beverage", "restaurants": "Food & Beverage", "retail": "Retail",
                "tech": "Technology", "technology": "Technology", "software": "Technology",
                "semiconductor": "Technology", "hardware": "Technology",
                "financial": "Financial Services", "finance": "Financial Services", "banking": "Financial Services",
                "insurance": "Financial Services", "healthcare": "Healthcare", "pharma": "Healthcare",
                "biotech": "Healthcare", "energy": "Energy", "oil": "Energy", "utilities": "Energy",
                "auto": "Automotive", "automotive": "Automotive",
                "media": "Media & Entertainment", "entertainment": "Media & Entertainment",
                "telecom": "Telecommunications", "telecommunications": "Telecommunications"
            ]
            var groups: [String: [Company]] = [:]
            for c in all {
                let raw = c.industry ?? "Other"
                let ind = norm[raw.lowercased()] ?? raw.capitalized
                groups[ind, default: []].append(c)
            }
            industries = groups.map { name, companies in
                let total = companies.reduce(0.0) { $0 + ($1.composite ?? 0) }
                let avg = companies.isEmpty ? 0 : Int(total / Double(companies.count))
                let top = companies.sorted { ($0.composite ?? 0) > ($1.composite ?? 0) }.prefix(10)
                return (name: name, avg: avg, count: companies.count, companies: Array(top))
            }.sorted { $0.avg > $1.avg }
            isLoading = false
        }
    }
}
