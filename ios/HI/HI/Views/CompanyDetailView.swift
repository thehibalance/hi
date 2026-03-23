import SwiftUI

struct CompanyDetailView: View {
    @EnvironmentObject var api: APIService
    @EnvironmentObject var favorites: FavoritesManager
    let company: Company
    @State private var fullData: Company?
    
    private var c: Company { fullData ?? company }
    private var score: Double { c.composite ?? 0 }
    private var isGold: Bool { c.hi_balanced == true }
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header
                headerSection
                
                // HUMAN Dimensions
                dimensionsSection
                
                // 10 Gates
                gatesSection
                
                // Genome (sub-signals)
                if c.genome != nil { genomeSection }
                
                // Algo Harm
                if c.algo_harm?.has_harm == true { algoHarmSection }
                
                // Humanwashing
                if let flags = c.humanwashing_flags, !flags.isEmpty { humanwashingSection(flags) }
                
                Spacer(minLength: 40)
            }
            .padding()
        }
        .background(Color.hiBackground)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    favorites.toggle(c)
                } label: {
                    Image(systemName: favorites.isFavorite(c.ticker) ? "star.fill" : "star")
                        .foregroundColor(favorites.isFavorite(c.ticker) ? .hiGold : .secondary)
                }
            }
        }
        .task {
            if let ticker = company.ticker, !ticker.isEmpty {
                fullData = await api.score(ticker: ticker)
            }
            favorites.addRecent(c)
        }
    }
    
    // MARK: - Header
    private var headerSection: some View {
        VStack(spacing: 12) {
            // Score circle
            ZStack {
                Circle()
                    .fill(isGold
                        ? LinearGradient(colors: [.hiGold, Color(red: 0.65, green: 0.5, blue: 0.1)], startPoint: .topLeading, endPoint: .bottomTrailing)
                        : LinearGradient(colors: [Color.hiScore(score)], startPoint: .top, endPoint: .bottom))
                    .frame(width: 80, height: 80)
                
                if isGold {
                    VStack(spacing: 0) {
                        Text("✦").font(.system(size: 14))
                        Text("\(Int(score))").font(.system(size: 24, weight: .heavy, design: .rounded))
                    }
                    .foregroundColor(.white)
                } else {
                    Text("\(Int(score))")
                        .font(.system(size: 28, weight: .heavy, design: .rounded))
                        .foregroundColor(.white)
                }
            }
            
            Text(c.company ?? "Unknown")
                .font(HIFont.title(24))
                .foregroundColor(.hiNavy)
                .multilineTextAlignment(.center)
            
            Text("HI Grade™")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(isGold ? .hiGold : .hiScore(score))
            
            // Meta tags
            HStack(spacing: 8) {
                if let t = c.ticker, !t.isEmpty { metaTag(t) }
                if let i = c.industry { metaTag(i) }
                if let s = c.sic_description { metaTag(s) }
            }
            
            // Decay
            if let di = c.decay_index, di > 0, let dl = c.decay_level {
                HStack(spacing: 6) {
                    Circle()
                        .fill(dl == "critical" ? Color.hiRed : dl == "warning" ? Color.hiOrange : .hiGreen)
                        .frame(width: 8, height: 8)
                    Text("Decay: \(Int(di)) · \(dl.capitalized)")
                        .font(HIFont.caption())
                        .foregroundColor(.secondary)
                }
            }
            
            // Gold badge
            if isGold {
                HStack(spacing: 4) {
                    Text("✦")
                    Text("All 10 gates passed · Gold HI Grade")
                }
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(.hiGold)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.hiGold.opacity(0.1))
                .cornerRadius(8)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }
    
    // MARK: - Dimensions
    private var dimensionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("HUMAN Dimensions")
                .font(.system(size: 13, weight: .bold))
                .tracking(0.5)
                .foregroundColor(.hiNavy)
            
            let dims: [(String, String, String, Double)] = [
                ("H", "Human Consciousness", "🧠", c.D_H ?? 0),
                ("U", "Understanding & Empathy", "💙", c.D_U ?? 0),
                ("M", "Moral & Ethical Conduct", "⚖️", c.D_M ?? 0),
                ("A", "Alive & Environmental", "🌍", c.D_A ?? 0),
                ("N", "Natural Transparency", "🔍", c.D_N ?? 0),
            ]
            
            ForEach(dims, id: \.0) { dim in
                HStack(spacing: 12) {
                    Text(dim.2)
                        .font(.system(size: 18))
                        .frame(width: 28)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(dim.0)
                                .font(.system(size: 13, weight: .bold))
                                .foregroundColor(.hiNavy)
                            Text(dim.1)
                                .font(.system(size: 12))
                                .foregroundColor(.secondary)
                                .lineLimit(1)
                            Spacer()
                            Text("\(Int(dim.3))")
                                .font(.system(size: 15, weight: .heavy, design: .rounded))
                                .foregroundColor(.hiScore(dim.3))
                        }
                        
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(Color(.systemGray5))
                                    .frame(height: 6)
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(Color.hiScore(dim.3))
                                    .frame(width: max(0, geo.size.width * dim.3 / 100), height: 6)
                            }
                        }
                        .frame(height: 6)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }
    
    // MARK: - Gates
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
        let passed = checks.filter(\.1).count
        
        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("10 Gates to Gold")
                    .font(.system(size: 13, weight: .bold))
                    .tracking(0.5)
                    .foregroundColor(.hiNavy)
                Spacer()
                Text("\(passed)/10")
                    .font(.system(size: 14, weight: .heavy))
                    .foregroundColor(passed == 10 ? .hiGold : .secondary)
            }
            
            ForEach(checks, id: \.0) { gate in
                HStack(spacing: 8) {
                    Image(systemName: gate.1 ? "checkmark.circle.fill" : "circle")
                        .foregroundColor(gate.1 ? .hiGreen : .secondary.opacity(0.4))
                        .font(.system(size: 14))
                    Text(gate.0)
                        .font(.system(size: 13))
                        .foregroundColor(gate.1 ? .primary : .secondary)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }
    
    // MARK: - Genome
    private var genomeSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("HUMAN Genome")
                .font(.system(size: 13, weight: .bold))
                .tracking(0.5)
                .foregroundColor(.hiNavy)
            
            if let genome = c.genome {
                ForEach(["H", "U", "M", "A", "N"], id: \.self) { dim in
                    if let gd = genome[dim], let scores = gd.scores {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text(dim)
                                    .font(.system(size: 12, weight: .bold))
                                    .foregroundColor(.hiNavy)
                                Spacer()
                                if let avg = gd.avg {
                                    Text("\(Int(avg))")
                                        .font(.system(size: 12, weight: .heavy))
                                        .foregroundColor(.hiScore(avg))
                                }
                            }
                            HStack(spacing: 3) {
                                ForEach(scores.sorted(by: { $0.key < $1.key }), id: \.key) { key, val in
                                    VStack(spacing: 1) {
                                        RoundedRectangle(cornerRadius: 2)
                                            .fill(Color.hiScore(val))
                                            .frame(height: 18)
                                            .overlay(
                                                Text(val > 0 ? "\(Int(val))" : "")
                                                    .font(.system(size: 7, weight: .bold))
                                                    .foregroundColor(.white)
                                            )
                                        Text(key.replacingOccurrences(of: "_", with: " "))
                                            .font(.system(size: 6))
                                            .foregroundColor(.secondary)
                                            .lineLimit(1)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }
    
    // MARK: - Algo Harm
    private var algoHarmSection: some View {
        let ah = c.algo_harm!
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("⚡ Algorithmic Harm Index")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.hiRed)
                Spacer()
                Text("\(Int(ah.algo_harm_score ?? 0))/100")
                    .font(.system(size: 14, weight: .heavy))
                    .foregroundColor(.hiRed)
            }
            
            if let flags = ah.flags {
                ForEach(flags, id: \.self) { flag in
                    HStack(alignment: .top, spacing: 6) {
                        Text("›")
                            .foregroundColor(.hiRed)
                        Text(flag)
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            if let penalties = ah.penalties {
                HStack(spacing: 8) {
                    ForEach(["H", "U", "M", "N"], id: \.self) { dim in
                        if let p = penalties[dim], p < 0 {
                            Text("\(dim): \(Int(p))")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(.hiRed)
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color.hiRed.opacity(0.05))
        .cornerRadius(16)
    }
    
    // MARK: - Humanwashing
    private func humanwashingSection(_ flags: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("⚠ Humanwashing Detected")
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.hiOrange)
            
            ForEach(flags, id: \.self) { flag in
                HStack(alignment: .top, spacing: 6) {
                    Text("›").foregroundColor(.hiOrange)
                    Text(flag).font(.system(size: 12)).foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color.hiOrange.opacity(0.05))
        .cornerRadius(16)
    }
    
    // MARK: - Helpers
    private func metaTag(_ text: String) -> some View {
        Text(text)
            .font(HIFont.caption(10))
            .foregroundColor(.secondary)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(Color(.systemGray6))
            .cornerRadius(6)
    }
}
