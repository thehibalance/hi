import SwiftUI

struct AboutView: View {
    @Environment(APIService.self) var api
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    VStack(spacing: 8) {
                        Text("HI.").font(.system(size: 56, weight: .black, design: .serif)).foregroundColor(.hiNavy)
                        Text("Think human intelligence.").font(.system(size: 16, weight: .medium)).foregroundColor(.hiGold)
                    }.padding(.top, 20)
                    
                    VStack(spacing: 12) {
                        Text("We're not anti-AI. We're pro-balance.").font(.system(size: 17, weight: .bold)).foregroundColor(.hiNavy).multilineTextAlignment(.center)
                        Text("Brands that empower humans score well. Brands that replace, divide, or addict them score poorly.").font(.system(size: 14)).foregroundColor(.secondary).multilineTextAlignment(.center)
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    VStack(alignment: .leading, spacing: 10) {
                        Text("The HUMAN Framework").font(.system(size: 15, weight: .bold)).foregroundColor(.hiNavy)
                        ForEach([("🧠", "H — Human Consciousness"), ("💙", "U — Understanding & Empathy"), ("⚖️", "M — Moral & Ethical Conduct"), ("🌍", "A — Alive & Environmental"), ("🔍", "N — Natural Transparency")], id: \.1) { icon, text in
                            HStack(spacing: 10) { Text(icon).font(.system(size: 18)); Text(text).font(.system(size: 13, weight: .medium)).foregroundColor(.hiNavy) }
                        }
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    if let stats = api.stats {
                        HStack(spacing: 0) {
                            statBox("\(stats.total_companies ?? 0)", "Brands")
                            statBox("\(stats.data_sources ?? 0)", "Sources")
                            statBox("32", "Endpoints")
                            statBox("24", "Signals")
                        }.background(Color.hiSystemBg).cornerRadius(16)
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("How Scoring Works").font(.system(size: 15, weight: .bold)).foregroundColor(.hiNavy)
                        Text("Every company is scored 0-100 across five dimensions using 34 free public data sources. No AI in the scoring. No surveys. No pay-to-play. Companies that pass all 10 gates earn Gold HI Grade.").font(.system(size: 13)).foregroundColor(.secondary)
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    VStack(spacing: 8) {
                        Link("thehibalance.org", destination: URL(string: "https://thehibalance.org")!).font(.system(size: 14, weight: .semibold))
                        Text("The HI Balance · Patent Pending · HI Grade\u{2122}").font(.system(size: 11)).foregroundColor(.secondary)
                        Text("Morf Innovations LLC").font(.system(size: 11)).foregroundColor(.secondary)
                    }.padding(.vertical)
                    
                    Spacer(minLength: 40)
                }.padding(.horizontal)
            }
            .background(Color.hiBackground).navigationTitle("About HI.").navigationBarTitleDisplayMode(.inline)
        }
    }
    
    private func statBox(_ value: String, _ label: String) -> some View {
        VStack(spacing: 4) {
            Text(value).font(.system(size: 22, weight: .heavy, design: .rounded)).foregroundColor(.hiNavy)
            Text(label).font(.system(size: 10, weight: .medium)).foregroundColor(.secondary)
        }.frame(maxWidth: .infinity).padding(.vertical, 12)
    }
}
