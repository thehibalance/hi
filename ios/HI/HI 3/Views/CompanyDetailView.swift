import SwiftUI

struct CompanyDetailView: View {
    @Environment(APIService.self) var api
    @Environment(FavoritesManager.self) var favorites
    let company: Company
    @State private var fullData: Company?
    
    private var c: Company { fullData ?? company }
    private var score: Double { c.composite ?? 0 }
    private var isGold: Bool { c.hi_balanced == true }
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                headerSection
                dimensionsSection
                gatesSection
                if c.algo_harm?.has_harm == true { algoHarmSection }
                if let flags = c.humanwashing_flags, !flags.isEmpty { humanwashingSection(flags) }
                Spacer(minLength: 40)
            }.padding()
        }
        .background(Color.hiBackground)
        
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button { favorites.toggle(c) } label: {
                    Image(systemName: favorites.isFavorite(c.ticker) ? "star.fill" : "star")
                        .foregroundColor(favorites.isFavorite(c.ticker) ? .hiGold : .secondary)
                }
            }
        }
        .task {
            if let ticker = company.ticker, !ticker.isEmpty { fullData = await api.score(ticker: ticker) }
            favorites.addRecent(c)
        }
    }
    
    private var headerSection: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle().fill(isGold ? LinearGradient(colors: [.hiGold, Color(red: 0.65, green: 0.5, blue: 0.1)], startPoint: .topLeading, endPoint: .bottomTrailing) : LinearGradient(colors: [Color.hiScore(score)], startPoint: .top, endPoint: .bottom)).frame(width: 80, height: 80)
                if isGold {
                    VStack(spacing: 0) { Text("✦").font(.system(size: 14)); Text("\(Int(score))").font(.system(size: 24, weight: .heavy, design: .rounded)) }.foregroundColor(.white)
                } else { Text("\(Int(score))").font(.system(size: 28, weight: .heavy, design: .rounded)).foregroundColor(.white) }
            }
            Text(c.company ?? "Unknown").font(HIFont.title(24)).foregroundColor(.hiNavy).multilineTextAlignment(.center)
            Text("HI Grade™").font(.system(size: 14, weight: .semibold)).foregroundColor(isGold ? .hiGold : .hiScore(score))
            if isGold {
                HStack(spacing: 4) { Text("✦"); Text("All 10 gates passed · Gold HI Grade") }
                    .font(.system(size: 12, weight: .semibold)).foregroundColor(.hiGold)
                    .padding(.horizontal, 12).padding(.vertical, 6).background(Color.hiGold.opacity(0.1)).cornerRadius(8)
            }
        }.padding().background(Color.hiSystemBg).cornerRadius(16).shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }
    
    private var dimensionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("HUMAN Dimensions").font(.system(size: 13, weight: .bold)).tracking(0.5).foregroundColor(.hiNavy)
            ForEach([("H", "Human Consciousness", "🧠", c.D_H ?? 0), ("U", "Understanding & Empathy", "💙", c.D_U ?? 0), ("M", "Moral & Ethical Conduct", "⚖️", c.D_M ?? 0), ("A", "Alive & Environmental", "🌍", c.D_A ?? 0), ("N", "Natural Transparency", "🔍", c.D_N ?? 0)], id: \.0) { dim in
                HStack(spacing: 12) {
                    Text(dim.2).font(.system(size: 18)).frame(width: 28)
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(dim.0).font(.system(size: 13, weight: .bold)).foregroundColor(.hiNavy)
                            Text(dim.1).font(.system(size: 12)).foregroundColor(.secondary).lineLimit(1)
                            Spacer()
                            Text("\(Int(dim.3))").font(.system(size: 15, weight: .heavy, design: .rounded)).foregroundColor(.hiScore(dim.3))
                        }
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                RoundedRectangle(cornerRadius: 3).fill(Color.hiGray6).frame(height: 6)
                                RoundedRectangle(cornerRadius: 3).fill(Color.hiScore(dim.3)).frame(width: max(0, geo.size.width * dim.3 / 100), height: 6)
                            }
                        }.frame(height: 6)
                    }
                }
            }
        }.padding().background(Color.hiSystemBg).cornerRadius(16).shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }
    
    private var gatesSection: some View {
        let threshold = api.goldThreshold
        let checks: [(String, Bool)] = [
            ("Composite ≥ \(Int(threshold))", score >= threshold),
            ("All dimensions ≥ 42", (c.D_H ?? 0) >= 42 && (c.D_U ?? 0) >= 42 && (c.D_M ?? 0) >= 42 && (c.D_A ?? 0) >= 42 && (c.D_N ?? 0) >= 42),
            ("No humanwashing flags", (c.humanwashing_flags ?? []).isEmpty),
            ("Decay index < 30", (c.decay_index ?? 0) < 30),
            ("Shield score ≥ 50", (c.shield_score ?? 50) >= 50),
            ("No ESG washing", c.algo_harm?.has_harm != true),
            ("Not negative industry leader", true),
            ("No critical genome gaps", true),
            ("Not under collective pressure", true),
            ("No critical alerts", (c.decay_level ?? "stable") != "critical"),
        ]
        let hasPipelineData = (c.data_sources ?? []).count >= 3
        let grayGates = [false, false, !hasPipelineData, !hasPipelineData, !hasPipelineData, !hasPipelineData, !hasPipelineData, !hasPipelineData, !hasPipelineData, !hasPipelineData]
        let passed = checks.enumerated().filter { !grayGates[$0.offset] && $0.element.1 }.count
        let total = grayGates.filter { !$0 }.count
        
        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("\(passed)/\(total) Gates verified").font(.system(size: 13, weight: .bold)).tracking(0.5).foregroundColor(.hiNavy)
                Spacer()
                if isGold { Text("✦").foregroundColor(.hiGold) }
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3).fill(Color.hiGray6).frame(height: 6)
                    RoundedRectangle(cornerRadius: 3).fill(isGold ? Color.hiGold : .hiNavy).frame(width: total > 0 ? geo.size.width * CGFloat(passed) / CGFloat(total) : 0, height: 6)
                }
            }.frame(height: 6)
            ForEach(Array(checks.enumerated()), id: \.offset) { idx, gate in
                let isGray = grayGates[idx]
                HStack(spacing: 8) {
                    Image(systemName: isGray ? "circle.dashed" : (gate.1 ? "checkmark.circle.fill" : "xmark.circle"))
                        .foregroundColor(isGray ? .secondary.opacity(0.4) : (gate.1 ? .hiGreen : .hiRed)).font(.system(size: 14))
                    Text(isGray ? "\(gate.0) · needs data" : gate.0)
                        .font(.system(size: 13)).foregroundColor(isGray ? .secondary.opacity(0.5) : (gate.1 ? .primary : .hiRed))
                }
            }
            if !hasPipelineData {
                Text("Some gates need more data to verify").font(.system(size: 10)).foregroundColor(.secondary)
            }
        }.padding().background(Color.hiSystemBg).cornerRadius(16).shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }
    
    private var algoHarmSection: some View {
        let ah = c.algo_harm!
        return VStack(alignment: .leading, spacing: 8) {
            HStack { Text("⚡ Algorithmic Harm Index").font(.system(size: 13, weight: .bold)).foregroundColor(.hiRed); Spacer(); Text("\(Int(ah.algo_harm_score ?? 0))/100").font(.system(size: 14, weight: .heavy)).foregroundColor(.hiRed) }
            if let flags = ah.flags { ForEach(flags, id: \.self) { f in HStack(alignment: .top, spacing: 6) { Text("›").foregroundColor(.hiRed); Text(f).font(.system(size: 12)).foregroundColor(.secondary) } } }
        }.padding().background(Color.hiRed.opacity(0.05)).cornerRadius(16)
    }
    
    private func humanwashingSection(_ flags: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("⚠ Humanwashing Detected").font(.system(size: 13, weight: .bold)).foregroundColor(.hiOrange)
            ForEach(flags, id: \.self) { f in HStack(alignment: .top, spacing: 6) { Text("›").foregroundColor(.hiOrange); Text(f).font(.system(size: 12)).foregroundColor(.secondary) } }
        }.padding().background(Color.hiOrange.opacity(0.05)).cornerRadius(16)
    }
}
