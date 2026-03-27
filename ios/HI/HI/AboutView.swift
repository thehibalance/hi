import SwiftUI

struct AboutView: View {
    @Environment(APIService.self) var api
    
    private var frameworkRows: [(String, String)] {
        [
            ("brain.head.profile", "H — Human Consciousness"),
            ("heart.fill", "U — Understanding & Empathy"),
            ("scale.3d", "M — Moral & Ethical Conduct"),
            ("leaf.fill", "A — Alive & Environmental"),
            ("eye.fill", "N — Natural Transparency"),
        ]
    }
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    VStack(spacing: 8) {
                        Image("hi-logo")
                            .resizable()
                            .scaledToFit()
                            .frame(height: 80)
                        Text("Think human intelligence.")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.hiGold)
                    }.padding(.top, 20)
                    
                    VStack(spacing: 12) {
                        Text("We're not anti-AI. We're pro-balance.")
                            .font(.system(size: 17, weight: .bold))
                            .foregroundColor(.hiNavy)
                            .multilineTextAlignment(.center)
                        Text("Brands that empower humans score well. Brands that replace, divide, or addict them score poorly.")
                            .font(.system(size: 14))
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                        Text("We reward companies that use AI to empower their people.")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.hiNavy)
                            .multilineTextAlignment(.center)
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    VStack(alignment: .leading, spacing: 10) {
                        Text("The HUMAN Framework")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        ForEach(frameworkRows, id: \.1) { icon, text in
                            HStack(spacing: 10) {
                                Image(systemName: icon).font(.system(size: 16)).foregroundColor(.hiGold).frame(width: 24)
                                Text(text).font(.system(size: 13, weight: .medium)).foregroundColor(.hiNavy)
                            }
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
                        Text("How Scoring Works")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        Text("Every company is scored 0\u{2013}100 across five dimensions using 40 free public data sources. No AI in the scoring. No surveys. No pay-to-play. Companies that pass all 3 gates earn Gold HI Grade\u{2122}.")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // Coming Soon
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Coming Soon")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        comingSoonRow(icon: "barcode.viewfinder", title: "Product Scanner", desc: "Scan any barcode to see the company's HI Grade")
                        comingSoonRow(icon: "doc.text.viewfinder", title: "Document Scanner", desc: "Analyze contracts and reports for ethical signals")
                        comingSoonRow(icon: "safari", title: "Chrome Extension", desc: "See HI Grades on any website while you browse")
                        comingSoonRow(icon: "chart.line.uptrend.xyaxis", title: "HUMAN 100 Backtest", desc: "Does being human pay? Live market data coming Q3 2026")
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // Contact
                    VStack(spacing: 12) {
                        Text("Get in Touch")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        Link(destination: URL(string: "mailto:hi@thehibalance.org")!) {
                            HStack(spacing: 8) {
                                Image(systemName: "envelope.fill").foregroundColor(.hiGold)
                                Text("hi@thehibalance.org").font(.system(size: 14, weight: .medium))
                            }
                        }
                        Link(destination: URL(string: "https://thehibalance.org")!) {
                            HStack(spacing: 8) {
                                Image(systemName: "globe").foregroundColor(.hiGold)
                                Text("thehibalance.org").font(.system(size: 14, weight: .medium))
                            }
                        }
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // Don't Panic
                    VStack(spacing: 12) {
                        Text("Don't panic.")
                            .font(.system(size: 20, weight: .bold, design: .serif))
                            .foregroundColor(.hiNavy)
                        Text("Every journey starts somewhere. The data will get better. The gates will get harder. The companies will adapt. That's the point.")
                            .font(.system(size: 14))
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                        Text("Bringing balance to the workforce.")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.hiGold)
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    VStack(spacing: 8) {
                        Text("The HI Balance \u{00B7} Patent Pending \u{00B7} HI Grade\u{2122}")
                            .font(.system(size: 11)).foregroundColor(.secondary)
                        Text("Morf Innovations LLC")
                            .font(.system(size: 11)).foregroundColor(.secondary)
                    }.padding(.vertical)
                    
                    Spacer(minLength: 40)
                }.padding(.horizontal)
            }
            .background(Color.hiBackground)
            .navigationTitle("About HI.")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
    
    private func statBox(_ value: String, _ label: String) -> some View {
        VStack(spacing: 4) {
            Text(value).font(.system(size: 22, weight: .heavy, design: .rounded)).foregroundColor(.hiNavy)
            Text(label).font(.system(size: 10, weight: .medium)).foregroundColor(.secondary)
        }.frame(maxWidth: .infinity).padding(.vertical, 12)
    }
    
    private func comingSoonRow(icon: String, title: String, desc: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 18))
                .foregroundColor(.hiGold)
                .frame(width: 28)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.hiNavy)
                Text(desc)
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }
        }
    }
}
