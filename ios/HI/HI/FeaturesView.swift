import SwiftUI

struct FeaturesView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("PHONE EXTENSION") {
                    NavigationLink { PhoneExtensionView() } label: {
                        FeatureRow(icon: "apps.iphone", title: "Phone Extension", desc: "Score any app when you open it")
                    }
                }
                Section("HUMAN FEATURES") {
                    NavigationLink { ShieldView() } label: { FeatureRow(icon: "shield.fill", title: "HUMAN Shield", desc: "Ethical moat depth") }
                    NavigationLink { LensView() } label: { FeatureRow(icon: "eye.fill", title: "HUMAN Lens", desc: "ESG vs HI gaps") }
                    NavigationLink { HeartbeatView() } label: { FeatureRow(icon: "heart.fill", title: "Heartbeat", desc: "Score decay monitoring") }
                    NavigationLink { ContagionView() } label: { FeatureRow(icon: "waveform.path.ecg", title: "Contagion", desc: "Industry-wide effects") }
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
            Image(systemName: icon).font(.system(size: 20)).foregroundColor(.hiNavy).frame(width: 28)
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
                List {
                    ForEach(Array(filtered.enumerated()), id: \.offset) { _, entry in
                        HStack(spacing: 12) {
                            Text("\(Int(entry.moat_score ?? 0))").font(HIFont.score(20)).foregroundColor(.hiScore(entry.moat_score ?? 0)).frame(width: 40)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(NameNormalizer.display(entry.company ?? "")).font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy)
                                Text(entry.moat_label ?? "").font(.system(size: 11)).foregroundColor(.hiScore(entry.moat_score ?? 0))
                            }
                            Spacer()
                            Text("\(Int(entry.composite ?? 0))").font(.system(size: 14, weight: .bold)).foregroundColor(.secondary)
                        }
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
                        let labels: [String: String] = ["all": "All", "esg_washing": "ESG Washing", "hidden_gem": "Hidden Gems", "aligned": "Aligned"]
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
                        let icons: [String: String] = ["esg_washing": "exclamationmark.triangle.fill", "hidden_gem": "diamond.fill", "aligned": "checkmark.seal.fill", "double_risk": "exclamationmark.2"]
                        Image(systemName: icons[entry.arbitrage_type ?? ""] ?? "circle").font(.system(size: 14))
                            .foregroundColor(entry.arbitrage_type == "esg_washing" ? .hiRed : entry.arbitrage_type == "hidden_gem" ? .hiGold : .hiGreen)
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
            else if entries.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "waveform.path.ecg")
                        .font(.system(size: 32))
                        .foregroundColor(.secondary.opacity(0.5))
                    Text("No contagion data available")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(.hiNavy)
                    Text("Contagion scores track how one company's ethical failures spread across its industry.")
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                }
            } else {
                List(entries) { entry in
                    HStack(spacing: 12) {
                        Image(systemName: "circle.fill")
                            .font(.system(size: 8))
                            .foregroundColor(.hiScore(abs(entry.gap_from_industry ?? 0)))
                            .frame(width: 20)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(entry.company ?? "")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.hiNavy)
                            if let i = entry.industry {
                                Text(i).font(.system(size: 11)).foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                        Text("\(Int(abs(entry.gap_from_industry ?? 0)))%")
                            .font(.system(size: 15, weight: .heavy, design: .rounded))
                            .foregroundColor(.hiScore(abs(entry.gap_from_industry ?? 0)))
                    }
                }.listStyle(.plain)
            }
        }
        .navigationTitle("Contagion").navigationBarTitleDisplayMode(.inline)
        .task {
            let raw = await api.contagion()
            var seen = Set<String>()
            entries = raw.filter { e in
                let key = e.ticker ?? e.company ?? UUID().uuidString
                guard !seen.contains(key) else { return false }
                seen.insert(key)
                return true
            }
            isLoading = false
        }
    }
}
