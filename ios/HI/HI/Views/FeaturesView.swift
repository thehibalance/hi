import SwiftUI

struct FeaturesView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("HUMAN FEATURES") {
                    NavigationLink { ShieldView() } label: { FeatureRow(icon: "🏰", title: "HUMAN Shield", desc: "Ethical moat depth") }
                    NavigationLink { LensView() } label: { FeatureRow(icon: "🔎", title: "HUMAN Lens", desc: "ESG vs HI gaps") }
                    NavigationLink { HeartbeatView() } label: { FeatureRow(icon: "💓", title: "Heartbeat", desc: "Score decay monitoring") }
                    NavigationLink { ContagionView() } label: { FeatureRow(icon: "🦠", title: "Contagion", desc: "Industry-wide effects") }
                }
            }
            .listStyle(.insetGrouped).navigationTitle("Features").navigationBarTitleDisplayMode(.large)
        }
    }
}

struct FeatureRow: View {
    let icon: String; let title: String; let desc: String
    var body: some View {
        HStack(spacing: 12) {
            Text(icon).font(.system(size: 24))
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 15, weight: .semibold)).foregroundColor(.hiNavy)
                Text(desc).font(.system(size: 12)).foregroundColor(.secondary)
            }
        }.padding(.vertical, 4)
    }
}

struct ShieldView: View {
    @Environment(APIService.self) var api
    @State private var entries: [MoatEntry] = []
    @State private var filter = "all"
    @State private var isLoading = true
    
    var filtered: [MoatEntry] {
        if filter == "all" { return entries }
        return entries.filter { m in let ml = m.moat_level ?? ""; return ml == filter || (filter == "developing" && ml == "moderate") || (filter == "vulnerable" && ml == "thin") }
    }
    
    var body: some View {
        VStack(spacing: 0) {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(["all", "fortress", "strong", "developing", "vulnerable"], id: \.self) { t in
                        Button { filter = t } label: {
                            Text(t.capitalized).font(.system(size: 12, weight: .semibold))
                                .padding(.horizontal, 14).padding(.vertical, 8)
                                .background(filter == t ? Color.hiNavy : Color.hiGray6)
                                .foregroundColor(filter == t ? .white : .primary).cornerRadius(16)
                        }
                    }
                }.padding(.horizontal).padding(.vertical, 8)
            }
            if isLoading { ProgressView().frame(maxHeight: .infinity) }
            else {
                List(filtered) { entry in
                    HStack(spacing: 12) {
                        Text("\(Int(entry.moat_score ?? 0))").font(HIFont.score(20)).foregroundColor(.hiScore(entry.moat_score ?? 0)).frame(width: 40)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(entry.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy)
                            Text(entry.moat_label ?? "").font(.system(size: 11)).foregroundColor(.hiScore(entry.moat_score ?? 0))
                        }
                        Spacer()
                        Text("\(Int(entry.composite ?? 0))").font(.system(size: 14, weight: .bold)).foregroundColor(.secondary)
                    }
                }.listStyle(.plain)
            }
        }
        .navigationTitle("HUMAN Shield").navigationBarTitleDisplayMode(.inline)
        .task { if let r = await api.moat() { entries = r.results ?? [] }; isLoading = false }
    }
}

struct LensView: View {
    @Environment(APIService.self) var api
    @State private var entries: [ArbitrageEntry] = []
    @State private var filter = "all"
    @State private var isLoading = true
    
    var filtered: [ArbitrageEntry] {
        if filter == "all" { return entries }
        return entries.filter { $0.arbitrage_type == filter }
    }
    
    var body: some View {
        VStack(spacing: 0) {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(["all", "esg_washing", "hidden_gem", "aligned"], id: \.self) { t in
                        let labels: [String: String] = ["all": "All", "esg_washing": "🔴 ESG Washing", "hidden_gem": "💎 Hidden Gems", "aligned": "✅ Aligned"]
                        Button { filter = t } label: {
                            Text(labels[t] ?? t).font(.system(size: 12, weight: .semibold))
                                .padding(.horizontal, 14).padding(.vertical, 8)
                                .background(filter == t ? Color.hiNavy : Color.hiGray6)
                                .foregroundColor(filter == t ? .white : .primary).cornerRadius(16)
                        }
                    }
                }.padding(.horizontal).padding(.vertical, 8)
            }
            if isLoading { ProgressView().frame(maxHeight: .infinity) }
            else {
                List(filtered) { entry in
                    HStack(spacing: 10) {
                        let icons: [String: String] = ["esg_washing": "🔴", "hidden_gem": "💎", "aligned": "✅", "double_risk": "⚠"]
                        Text(icons[entry.arbitrage_type ?? ""] ?? "·").font(.system(size: 16))
                        VStack(alignment: .leading, spacing: 2) {
                            Text(entry.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy).lineLimit(1)
                            Text(entry.arbitrage_label ?? "").font(.system(size: 11)).foregroundColor(.secondary)
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 2) {
                            Text("ESG: \(Int(entry.esg_composite ?? 0))").font(.system(size: 11)).foregroundColor(.secondary)
                            Text("HI: \(Int(entry.hi_composite ?? 0))").font(.system(size: 11, weight: .bold)).foregroundColor(.hiNavy)
                        }
                    }
                }.listStyle(.plain)
            }
        }
        .navigationTitle("HUMAN Lens").navigationBarTitleDisplayMode(.inline)
        .task { if let r = await api.arbitrage() { entries = r.results ?? [] }; isLoading = false }
    }
}

struct HeartbeatView: View {
    @Environment(APIService.self) var api
    @State private var pulse: HeartbeatPulse?
    @State private var alerts: [HeartbeatAlert] = []
    @State private var isLoading = true
    
    var body: some View {
        VStack(spacing: 0) {
            if let p = pulse {
                HStack(spacing: 20) {
                    VStack { Text((p.pulse ?? "unknown").uppercased()).font(.system(size: 16, weight: .heavy)).foregroundColor(p.pulse == "healthy" ? .hiGreen : .hiOrange); Text("Ecosystem").font(.system(size: 10)).foregroundColor(.secondary) }
                    VStack { Text("\(Int(p.average_decay ?? 0))").font(HIFont.score(20)).foregroundColor(.hiNavy); Text("Avg Decay").font(.system(size: 10)).foregroundColor(.secondary) }
                    VStack { Text("\(p.alerts_count ?? 0)").font(HIFont.score(20)).foregroundColor(.hiOrange); Text("Alerts").font(.system(size: 10)).foregroundColor(.secondary) }
                }.padding().frame(maxWidth: .infinity).background(Color.hiSystemBg)
            }
            if isLoading { ProgressView().frame(maxHeight: .infinity) }
            else {
                List(alerts) { alert in
                    HStack(spacing: 12) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 8).fill((alert.decay_level == "critical" ? Color.hiRed : Color.hiOrange).opacity(0.15)).frame(width: 44, height: 44)
                            Text("\(Int(alert.decay_index ?? 0))").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundColor(alert.decay_level == "critical" ? .hiRed : .hiOrange)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text(alert.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy)
                            Text("\(alert.current_grade ?? "") · \((alert.decay_level ?? "watch").capitalized)").font(.system(size: 11)).foregroundColor(.secondary)
                        }
                    }
                }.listStyle(.plain)
            }
        }
        .navigationTitle("Heartbeat").navigationBarTitleDisplayMode(.inline)
        .task { async let p = api.heartbeatPulse(); async let a = api.heartbeatAlerts(); pulse = await p; alerts = await a; isLoading = false }
    }
}

struct ContagionView: View {
    @Environment(APIService.self) var api
    @State private var entries: [ContagionEntry] = []
    @State private var isLoading = true
    
    var body: some View {
        Group {
            if isLoading { ProgressView().frame(maxHeight: .infinity) }
            else {
                List(entries) { entry in
                    HStack(spacing: 12) {
                        Text("\(Int(entry.contagion_score ?? 0))").font(HIFont.score(18)).foregroundColor(.hiScore(entry.contagion_score ?? 0)).frame(width: 36)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(entry.company ?? "").font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy)
                            if let i = entry.industry { Text(i).font(.system(size: 11)).foregroundColor(.secondary) }
                        }
                        Spacer()
                        Text("\(Int(entry.composite ?? 0))").font(.system(size: 13, weight: .bold)).foregroundColor(.secondary)
                    }
                }.listStyle(.plain)
            }
        }
        .navigationTitle("Contagion").navigationBarTitleDisplayMode(.inline)
        .task { entries = await api.contagion(); isLoading = false }
    }
}
