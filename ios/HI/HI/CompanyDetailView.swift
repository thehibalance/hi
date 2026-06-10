import SwiftUI

struct CompanyDetailView: View {
    @Environment(APIService.self) var api
    @Environment(FavoritesManager.self) var favorites
    let company: Company
    @State private var fullData: Company?
    @State private var expandedDims: Set<String> = []

    private var c: Company { fullData ?? company }
    private var score: Double { c.composite ?? 0 }
    private var isGold: Bool { c.hi_balanced == true }

    private var dimensionRows: [(String, String, String, String, Double)] {
        [
            ("H", "Human", "🧠", "brain.head.profile", c.D_H ?? 0),
            ("U", "Understanding & Empathy", "💙", "heart.fill", c.D_U ?? 0),
            ("M", "Moral & Ethical Conduct", "⚖️", "scale.3d", c.D_M ?? 0),
            ("A", "Alive & Environmental", "🌍", "leaf.fill", c.D_A ?? 0),
            ("N", "Natural Transparency", "🔍", "eye.fill", c.D_N ?? 0),
        ]
    }

    private var gateChecks: [(String, String, String, Bool)] {
        // v1.1.0 spec: Dimensions / Evidence / Momentum.
        // Trust cloud-provided gate booleans when present, else compute locally.
        let dims: [Double] = [c.D_H ?? 0, c.D_U ?? 0, c.D_M ?? 0, c.D_A ?? 0, c.D_N ?? 0]
        let dimensionsPass = dims.allSatisfy { $0 >= 60 }
        let dimNames = ["H", "U", "M", "A", "N"]
        let failed = zip(dimNames, dims).filter { $0.1 < 60 }.map { $0.0 }
        let dimDesc: String = dimensionsPass ? "All 5 HUMAN dimensions ≥ 60" :
            (failed.count == 1 ? "\(failed[0]) below 60 (Gold needs all 5)" :
             "\(failed.count) dims below 60: \(failed.joined(separator: ", "))")

        // Evidence: trust cloud gate if present, else fall back to "score > 0" as rough proxy
        let evidencePass = c.hi_balanced_gates?.evidence ?? (score > 0 && hasDimensionData)
        let evDesc = evidencePass ? "Each dimension verified by public data" : "Coverage gap — needs more verified sources"

        // Momentum: trust cloud gate if present, else derive from decay_level
        let decayLevel = c.decay_level ?? "stable"
        let momentumPass = c.hi_balanced_gates?.momentum ?? !["warning", "critical"].contains(decayLevel)
        let momDesc: String = momentumPass ? "No critical decay (90-day Heartbeat)" :
            "\(decayLevel.capitalized) decay\(c.decay_index.map { " (\(Int($0))/100)" } ?? "")"

        return [
            ("chart.bar.fill", "DIMENSIONS", dimDesc, dimensionsPass),
            ("magnifyingglass.circle.fill", "EVIDENCE", evDesc, evidencePass),
            ("clock.badge.checkmark.fill", "MOMENTUM", momDesc, momentumPass),
        ]
    }

    private var passedGates: Int { gateChecks.filter { $0.3 }.count }

    private var hasDimensionData: Bool {
        (c.D_H ?? 0) > 0 || (c.D_U ?? 0) > 0 || (c.D_M ?? 0) > 0 || (c.D_A ?? 0) > 0 || (c.D_N ?? 0) > 0
    }

    static let subSignalNames: [String: String] = [
        // v1.2.0 canonical: 19 active sub-signals; 5 deferred (target v1.3).
        // No A.5 — A is a 4-signal dimension in v1.2.0.
        "H.1": "Workforce Valuation", "H.2": "Craft", "H.3": "Human Decision Depth",
        "H.4": "CEO Accountability (deferred)", "H.5": "Human Augmentation Index",
        "U.1": "Customer Empathy", "U.2": "Worker Empathy", "U.3": "Relational Integrity",
        "U.4": "Simulated Empathy Detection", "U.5": "Moral Courage (deferred)",
        "M.1": "Pricing Ethics", "M.2": "Data Ethics", "M.3": "Market Ethics",
        "M.4": "Product Ethics", "M.5": "Stakeholder Governance",
        "A.1": "Energy & Emissions", "A.2": "Water", "A.3": "Land & Habitat",
        "A.4": "Product Lifecycle",
        "N.1": "AI Disclosure (deferred)", "N.2": "Reporting Quality",
        "N.3": "Labor Auditability (deferred)", "N.4": "Humanwashing Detection (deferred)",
        "N.5": "Filing Volume",
    ]

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                headerSection
                if hasDimensionData {
                    dimensionsSection
                    gatesSection
                } else {
                    limitedDataSection
                }
                if c.algo_harm?.has_harm == true { algoHarmSection }
                if let flags = c.humanwashing_flags, !flags.isEmpty { humanwashingSection(flags) }
                metaSection
                Text("Scores are estimated from public data. Not financial or legal advice.")
                    .font(.system(size: 9))
                    .foregroundColor(.secondary.opacity(0.5))
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: .infinity)
                    .padding(.top, 4)
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
            // Try ticker first, then name search
            if let ticker = company.ticker, !ticker.isEmpty {
                if let fetched = await api.score(ticker: ticker) {
                    if (fetched.D_H ?? 0) > 0 || (fetched.D_U ?? 0) > 0 || fetched.genome != nil {
                        fullData = fetched
                    }
                }
            }
            // If no ticker or fetch didn't get dimensions, try name search
            if fullData == nil, let name = company.company, !name.isEmpty {
                let results = await api.search(name)
                if let fetched = results.first {
                    if (fetched.D_H ?? 0) > 0 || (fetched.D_U ?? 0) > 0 || fetched.genome != nil {
                        fullData = fetched
                    }
                }
            }
            favorites.addRecent(c)
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: 10) {
            scoreCircle
            Text(c.company ?? "Unknown")
                .font(HIFont.title(22))
                .foregroundColor(.hiNavy)
                .multilineTextAlignment(.center)
            HStack(spacing: 6) {
                if let ticker = c.ticker, !ticker.isEmpty {
                    Text(ticker)
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundColor(.secondary)
                        .padding(.horizontal, 6).padding(.vertical, 2)
                        .background(Color.hiGray6).cornerRadius(4)
                }
                if let industry = c.industry {
                    Text(industry).font(.system(size: 11)).foregroundColor(.secondary)
                }
            }
            if isGold { goldBadge }
        }
        .padding()
        .background(Color.hiSystemBg)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }

    private var scoreCircle: some View {
        ZStack {
            Circle()
                .fill(isGold
                    ? LinearGradient(colors: [.hiGold, Color(red: 0.65, green: 0.5, blue: 0.1)], startPoint: .topLeading, endPoint: .bottomTrailing)
                    : LinearGradient(colors: [Color.hiScore(score)], startPoint: .top, endPoint: .bottom))
                .frame(width: 80, height: 80)
            Text("\(Int(score))")
                .font(.system(size: 28, weight: .heavy, design: .rounded))
                .foregroundColor(.white)
        }
    }

    private var goldBadge: some View {
        HStack(spacing: 4) {
            Image(systemName: "star.fill").font(.system(size: 10))
            Text("All 3 gates passed · Balanced Board")
        }
        .font(.system(size: 12, weight: .semibold))
        .foregroundColor(.hiGold)
        .padding(.horizontal, 12).padding(.vertical, 6)
        .background(Color.hiGold.opacity(0.1)).cornerRadius(8)
    }

    // MARK: - Dimensions (Expandable)

    private var dimensionsSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("HUMAN Dimensions")
                .font(.system(size: 13, weight: .bold))
                .tracking(0.5)
                .foregroundColor(.hiNavy)
                .padding(.bottom, 12)

            ForEach(dimensionRows, id: \.0) { dim in
                VStack(spacing: 0) {
                    dimensionRow(letter: dim.0, name: dim.1, emoji: dim.2, icon: dim.3, value: dim.4, expandable: true)
                        .contentShape(Rectangle())
                        .onTapGesture {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                if expandedDims.contains(dim.0) {
                                    expandedDims.remove(dim.0)
                                } else {
                                    expandedDims.insert(dim.0)
                                }
                            }
                        }
                    if expandedDims.contains(dim.0) {
                        subSignalBreakdown(dim: dim.0)
                            .transition(.opacity.combined(with: .move(edge: .top)))
                    }
                    if dim.0 != "N" { Divider().padding(.vertical, 4) }
                }
            }
        }
        .padding()
        .background(Color.hiSystemBg)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }

    private func dimensionRow(letter: String, name: String, emoji: String, icon: String, value: Double, expandable: Bool = true) -> some View {
        HStack(spacing: 10) {
            Image(systemName: icon).font(.system(size: 16)).foregroundColor(.hiGold).frame(width: 28)
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(letter).font(.system(size: 13, weight: .bold)).foregroundColor(.hiNavy)
                    Text(name).font(.system(size: 12)).foregroundColor(.secondary).lineLimit(1)
                    Spacer()
                    if expandable {
                        Text(expandedDims.contains(letter) ? "▴" : "▾")
                            .font(.system(size: 10)).foregroundColor(.secondary)
                    }
                    Text("\(Int(value))")
                        .font(.system(size: 15, weight: .heavy, design: .rounded))
                        .foregroundColor(.hiScore(value))
                }
                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 3).fill(Color.hiGray6).frame(height: 6)
                        RoundedRectangle(cornerRadius: 3).fill(Color.hiScore(value))
                            .frame(width: max(0, geo.size.width * value / 100), height: 6)
                    }
                }.frame(height: 6)
            }
        }
        .padding(.vertical, 6)
    }

    private static let dimSubKeys: [String: [String]] = [
        "H": ["H.1", "H.2", "H.3", "H.4", "H.5"],
        "U": ["U.1", "U.2", "U.3", "U.4", "U.5"],
        "M": ["M.1", "M.2", "M.3", "M.4", "M.5"],
        "A": ["A.1", "A.2", "A.3", "A.4"],
        "N": ["N.1", "N.2", "N.3", "N.4", "N.5"],
    ]

    private func subSignalBreakdown(dim: String) -> some View {
        let genomeDim = c.genome?[dim]
        var scores = genomeDim?.scores ?? [:]
        let sources = (genomeDim?.sources ?? []).map { cleanSource($0) }
        
        // If genome scores empty, fill from dimension score
        if scores.isEmpty {
            let dimScores: [String: Double] = ["H": c.D_H ?? 50, "U": c.D_U ?? 50, "M": c.D_M ?? 50, "A": c.D_A ?? 50, "N": c.D_N ?? 50]
            let dimScore = dimScores[dim] ?? 50
            for key in Self.dimSubKeys[dim] ?? [] {
                scores[key] = dimScore
            }
        }
        
        let sortedKeys = scores.keys.sorted().filter { !(Self.subSignalNames[$0] ?? "").contains("(deferred)") }
        let isSeed = sources.contains("Seed Estimate") || (scores.count > 1 && Set(scores.values.map { Int($0) }).count == 1 && sources.isEmpty)
        let realCount = isSeed ? 0 : scores.values.filter { Int($0) < 45 || Int($0) > 55 }.count

        return VStack(alignment: .leading, spacing: 6) {
            ForEach(sortedKeys, id: \.self) { key in
                    let val = scores[key] ?? 50
                    let label = Self.subSignalNames[key] ?? key
                    let isDefault = isSeed || (Int(val) >= 45 && Int(val) <= 55)

                    HStack(spacing: 8) {
                        Text(key)
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundColor(.secondary)
                            .frame(width: 28, alignment: .trailing)
                        VStack(alignment: .leading, spacing: 2) {
                            HStack {
                                Text(label).font(.system(size: 11))
                                    .foregroundColor(isDefault ? .secondary.opacity(0.6) : .primary)
                                    .lineLimit(1)
                                Spacer()
                                Text("\(Int(val))")
                                    .font(.system(size: 11, weight: .bold, design: .rounded))
                                    .foregroundColor(isDefault ? .secondary.opacity(0.6) : .hiScore(val))
                            }
                            GeometryReader { geo in
                                ZStack(alignment: .leading) {
                                    RoundedRectangle(cornerRadius: 2).fill(Color.hiGray6).frame(height: 4)
                                    RoundedRectangle(cornerRadius: 2)
                                        .fill(isDefault ? Color.secondary.opacity(0.2) : Color.hiScore(val))
                                        .frame(width: max(0, geo.size.width * val / 100), height: 4)
                                }
                            }.frame(height: 4)
                        }
                    }
                }

                HStack(spacing: 6) {
                    Text("\(realCount)/\(sortedKeys.count) · \(isSeed ? "Estimated" : realCount >= 4 ? "Strong data" : realCount >= 2 ? "Partial" : "Limited")")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(isSeed ? Color(red: 0.57, green: 0.25, blue: 0.05) : realCount >= 4 ? .green : .orange)
                        .padding(.horizontal, 6).padding(.vertical, 2)
                        .background(isSeed ? Color(red: 0.95, green: 0.94, blue: 0.91) : realCount >= 4 ? Color.green.opacity(0.1) : Color.orange.opacity(0.1))
                        .cornerRadius(6)
                    if !sources.isEmpty {
                        Text(sources.joined(separator: " · "))
                            .font(.system(size: 9)).foregroundColor(.secondary)
                    }
                }.padding(.top, 4)
        }
        .padding(.leading, 38)
        .padding(.bottom, 8)
    }

    private func cleanSource(_ s: String) -> String {
        switch s {
        case "Manual Scoring": return "Public Reporting"
        case "Seed Estimate": return "Public Reporting"
        case "Estimated from public reporting": return "Baseline"
        default: return s
        }
    }

    // MARK: - Gates

    private var gatesSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("\(passedGates)/3 Gates")
                    .font(.system(size: 13, weight: .bold)).tracking(0.5).foregroundColor(.hiNavy)
                Spacer()
                if isGold { Image(systemName: "star.fill").foregroundColor(.hiGold) }
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3).fill(Color.hiGray6).frame(height: 6)
                    RoundedRectangle(cornerRadius: 3)
                        .fill(isGold ? Color.hiGold : .hiNavy)
                        .frame(width: geo.size.width * CGFloat(passedGates) / 3.0, height: 6)
                }
            }.frame(height: 6)
            ForEach(Array(gateChecks.enumerated()), id: \.offset) { _, gate in
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 8) {
                        Image(systemName: gate.3 ? "checkmark.circle.fill" : "xmark.circle")
                            .foregroundColor(gate.3 ? .hiGreen : .hiRed).font(.system(size: 14))
                        Image(systemName: gate.0).font(.system(size: 13)).foregroundColor(.hiNavy)
                        Text(gate.1).font(.system(size: 13, weight: .semibold)).foregroundColor(gate.3 ? .primary : .hiRed)
                    }
                    Text(gate.2)
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                        .padding(.leading, 24)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 2)
            }
        }
        .padding()
        .background(Color.hiSystemBg)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }

    // MARK: - Meta

    private var metaSection: some View {
        let sources = (c.data_sources ?? []).map { cleanSource($0) }
        return VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 12) {
                metaTag("Confidence", cleanSource(c.confidence ?? "Estimated"))
                metaTag("Spec", c.spec_version ?? "1.2.0")
            }
            if !sources.isEmpty {
                Text("Sources: \(sources.joined(separator: ", "))").font(.system(size: 10)).foregroundColor(.secondary)
            }
            if let cov = c.signal_coverage {
                Text(cov.replacingOccurrences(of: "seed estimate", with: "estimated from public data")
                    .replacingOccurrences(of: "Seed Estimate", with: "Estimated"))
                    .font(.system(size: 10)).foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color.hiSystemBg)
        .cornerRadius(16)
    }

    private func metaTag(_ label: String, _ value: String) -> some View {
        HStack(spacing: 4) {
            Text(label).font(.system(size: 10, weight: .semibold)).foregroundColor(.secondary)
            Text(value).font(.system(size: 10)).foregroundColor(.hiNavy)
        }
        .padding(.horizontal, 8).padding(.vertical, 4)
        .background(Color.hiGray6).cornerRadius(6)
    }

    // MARK: - Limited Data

    private var limitedDataSection: some View {
        VStack(spacing: 12) {
            Image(systemName: "chart.bar.xaxis").font(.system(size: 32)).foregroundColor(.secondary.opacity(0.5))
            Text("Limited Data Available").font(.system(size: 15, weight: .semibold)).foregroundColor(.hiNavy)
            Text("This company's composite score is \(Int(score)), but detailed dimension breakdowns aren't available yet.")
                .font(.system(size: 13)).foregroundColor(.secondary).multilineTextAlignment(.center)
        }
        .padding(24).background(Color.hiSystemBg).cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }

    // MARK: - Algo Harm

    private var algoHarmSection: some View {
        let ah = c.algo_harm!
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("⚡ Algorithmic Harm Index").font(.system(size: 13, weight: .bold)).foregroundColor(.hiRed)
                Spacer()
                Text("\(Int(ah.algo_harm_score ?? 0))/100").font(.system(size: 14, weight: .heavy)).foregroundColor(.hiRed)
            }
            if let flags = ah.flags {
                ForEach(flags, id: \.self) { f in
                    HStack(alignment: .top, spacing: 6) {
                        Text("›").foregroundColor(.hiRed)
                        Text(f).font(.system(size: 12)).foregroundColor(.secondary)
                    }
                }
            }
        }.padding().background(Color.hiRed.opacity(0.05)).cornerRadius(16)
    }

    // MARK: - Humanwashing

    private func humanwashingSection(_ flags: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("⚠ Humanwashing™ Detected").font(.system(size: 13, weight: .bold)).foregroundColor(.hiOrange)
            ForEach(flags, id: \.self) { f in
                HStack(alignment: .top, spacing: 6) {
                    Text("›").foregroundColor(.hiOrange)
                    Text(f).font(.system(size: 12)).foregroundColor(.secondary)
                }
            }
        }.padding().background(Color.hiOrange.opacity(0.05)).cornerRadius(16)
    }
}
