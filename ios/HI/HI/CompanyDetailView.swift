import SwiftUI

struct CompanyDetailView: View {
    @Environment(APIService.self) var api
    @Environment(FavoritesManager.self) var favorites
    let company: Company
    @State private var fullData: Company?

    private var c: Company { fullData ?? company }
    private var score: Double { c.composite ?? 0 }
    private var isGold: Bool { c.hi_balanced == true }

    // Pre-compute dimension rows to avoid SwiftUI type-check timeout
    private var dimensionRows: [(String, String, String, Double)] {
        [
            ("H", "Human Consciousness", "brain.head.profile", c.D_H ?? 0),
            ("U", "Understanding & Empathy", "heart.fill", c.D_U ?? 0),
            ("M", "Moral & Ethical Conduct", "scale.3d", c.D_M ?? 0),
            ("A", "Alive & Environmental", "leaf.fill", c.D_A ?? 0),
            ("N", "Natural Transparency", "eye.fill", c.D_N ?? 0),
        ]
    }

    // Pre-compute gate checks — 3 gates, not 10
    private var gateChecks: [(String, Bool)] {
        let threshold = api.goldThreshold
        return [
            ("Composite ≥ \(Int(threshold))", score >= threshold),
            ("All dimensions ≥ 42", (c.D_H ?? 0) >= 42 && (c.D_U ?? 0) >= 42 && (c.D_M ?? 0) >= 42 && (c.D_A ?? 0) >= 42 && (c.D_N ?? 0) >= 42),
            ("No Humanwashing™ & AHI < 30", (c.humanwashing_flags ?? []).isEmpty && (c.algo_harm?.algo_harm_score ?? 0) < 30),
        ]
    }

    private var passedGates: Int { gateChecks.filter { $0.1 }.count }

    private var hasDimensionData: Bool {
        (c.D_H ?? 0) > 0 || (c.D_U ?? 0) > 0 || (c.D_M ?? 0) > 0 || (c.D_A ?? 0) > 0 || (c.D_N ?? 0) > 0
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                headerSection
                if hasDimensionData {
                    dimensionsSection
                    gatesSection
                } else {
                    limitedDataSection
                }
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
            if let ticker = company.ticker, !ticker.isEmpty {
                if let fetched = await api.score(ticker: ticker) {
                    if (fetched.D_H ?? 0) > 0 || (fetched.D_U ?? 0) > 0 {
                        fullData = fetched
                    }
                }
            }
            favorites.addRecent(c)
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: 12) {
            scoreCircle
            Text(c.company ?? "Unknown")
                .font(HIFont.title(24))
                .foregroundColor(.hiNavy)
                .multilineTextAlignment(.center)
            Text("HI Grade™")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(isGold ? .hiGold : .hiScore(score))
            if isGold {
                goldBadge
            }
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
            if isGold {
                VStack(spacing: 2) {
                    Image("hi-gold")
                        .resizable()
                        .scaledToFit()
                        .frame(height: 32)
                        .clipShape(Circle())
                    Text("\(Int(score))")
                        .font(.system(size: 22, weight: .heavy, design: .rounded))
                }
                .foregroundColor(.white)
            } else {
                Text("\(Int(score))")
                    .font(.system(size: 28, weight: .heavy, design: .rounded))
                    .foregroundColor(.white)
            }
        }
    }

    private var goldBadge: some View {
        HStack(spacing: 4) {
            Image(systemName: "star.fill")
                .font(.system(size: 10))
            Text("All 3 gates passed · Gold HI Grade")
        }
        .font(.system(size: 12, weight: .semibold))
        .foregroundColor(.hiGold)
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.hiGold.opacity(0.1))
        .cornerRadius(8)
    }

    // MARK: - Dimensions

    private var dimensionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("HUMAN Dimensions")
                .font(.system(size: 13, weight: .bold))
                .tracking(0.5)
                .foregroundColor(.hiNavy)
            ForEach(dimensionRows, id: \.0) { dim in
                dimensionRow(letter: dim.0, name: dim.1, icon: dim.2, value: dim.3)
            }
        }
        .padding()
        .background(Color.hiSystemBg)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }

    private func dimensionRow(letter: String, name: String, icon: String, value: Double) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon).font(.system(size: 16)).foregroundColor(.hiGold).frame(width: 28)
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(letter)
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.hiNavy)
                    Text(name)
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                    Spacer()
                    Text("\(Int(value))")
                        .font(.system(size: 15, weight: .heavy, design: .rounded))
                        .foregroundColor(.hiScore(value))
                }
                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 3)
                            .fill(Color.hiGray6)
                            .frame(height: 6)
                        RoundedRectangle(cornerRadius: 3)
                            .fill(Color.hiScore(value))
                            .frame(width: max(0, geo.size.width * value / 100), height: 6)
                    }
                }.frame(height: 6)
            }
        }
    }

    // MARK: - Gates (3 gates)

    private var gatesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("\(passedGates)/3 Gates")
                    .font(.system(size: 13, weight: .bold))
                    .tracking(0.5)
                    .foregroundColor(.hiNavy)
                Spacer()
                if isGold {
                    Image(systemName: "star.fill")
                        .foregroundColor(.hiGold)
                }
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(Color.hiGray6)
                        .frame(height: 6)
                    RoundedRectangle(cornerRadius: 3)
                        .fill(isGold ? Color.hiGold : .hiNavy)
                        .frame(width: geo.size.width * CGFloat(passedGates) / 3.0, height: 6)
                }
            }.frame(height: 6)

            ForEach(Array(gateChecks.enumerated()), id: \.offset) { idx, gate in
                gateRow(name: gate.0, passed: gate.1)
            }
        }
        .padding()
        .background(Color.hiSystemBg)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.04), radius: 8, y: 2)
    }

    private func gateRow(name: String, passed: Bool) -> some View {
        HStack(spacing: 8) {
            Image(systemName: passed ? "checkmark.circle.fill" : "xmark.circle")
                .foregroundColor(passed ? .hiGreen : .hiRed)
                .font(.system(size: 14))
            Text(name)
                .font(.system(size: 13))
                .foregroundColor(passed ? .primary : .hiRed)
        }
    }

    // MARK: - Limited Data

    private var limitedDataSection: some View {
        VStack(spacing: 12) {
            Image(systemName: "chart.bar.xaxis")
                .font(.system(size: 32))
                .foregroundColor(.secondary.opacity(0.5))
            Text("Limited Data Available")
                .font(.system(size: 15, weight: .semibold))
                .foregroundColor(.hiNavy)
            Text("This company's composite score is \(Int(score)), but detailed dimension breakdowns aren't available yet. As more data sources are integrated, this profile will sharpen.")
                .font(.system(size: 13))
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(24)
        .background(Color.hiSystemBg)
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
                ForEach(flags, id: \.self) { f in
                    HStack(alignment: .top, spacing: 6) {
                        Text("›").foregroundColor(.hiRed)
                        Text(f).font(.system(size: 12)).foregroundColor(.secondary)
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
            Text("⚠ Humanwashing™ Detected")
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.hiOrange)
            ForEach(flags, id: \.self) { f in
                HStack(alignment: .top, spacing: 6) {
                    Text("›").foregroundColor(.hiOrange)
                    Text(f).font(.system(size: 12)).foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color.hiOrange.opacity(0.05))
        .cornerRadius(16)
    }
}
