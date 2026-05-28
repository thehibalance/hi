import SwiftUI

struct AboutView: View {
    @Environment(APIService.self) var api
    
    private var frameworkRows: [(icon: String, title: String, subtitle: String)] {
        [
            ("brain.head.profile", "H — Human Consciousness",   "Creative agency, craft, accountability vs. AI automation"),
            ("heart.fill",         "U — Understanding & Empathy", "Genuine care vs. simulated empathy"),
            ("scale.3d",           "M — Moral & Ethical Conduct", "Principled action vs. optimization-at-all-costs"),
            ("leaf.fill",          "A — Alive & Environmental",  "True ecological cost including AI infrastructure"),
            ("eye.fill",           "N — Natural Transparency",   "Honest disclosure vs. humanwashing"),
        ]
    }
    
    private var beforeYouRows: [(icon: String, title: String, desc: String)] {
        [
            ("cart.fill",           "Before you buy",      "Scan or search a brand. Know if the humans behind the product are being invested in or replaced."),
            ("briefcase.fill",      "Before you work",     "Look up the company before the interview. HI Grade tells you what Glassdoor can't."),
            ("chart.line.uptrend.xyaxis", "Before you invest", "Know what you're funding. HI Grade reveals the human cost of every portfolio."),
            ("person.2.fill",       "Before you recommend", "Don't vouch for a brand you haven't checked. Ask Human kind? before your reputation is on it."),
        ]
    }
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    
                    // Hero
                    VStack(spacing: 8) {
                        Image("hi-logo")
                            .resizable()
                            .scaledToFit()
                            .frame(height: 80)
                        Text("Human kind?")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.hiGold)
                    }.padding(.top, 20)
                    
                    // SECTION 1 — The First Check (NEW)
                    VStack(alignment: .leading, spacing: 10) {
                        HStack(spacing: 6) {
                            Text("💡").font(.system(size: 18))
                            Text("The First Check")
                                .font(.system(size: 17, weight: .bold, design: .serif))
                                .foregroundColor(.hiNavy)
                        }
                        Text("For centuries, we've made decisions through four filters: cost, time, convenience, risk. HI Grade asks what should come first — verified human impact.")
                            .font(.system(size: 14))
                            .foregroundColor(.secondary)
                            .lineSpacing(3)
                        Text("Human kind? Now you can find out.")
                            .font(.system(size: 14, weight: .semibold, design: .serif))
                            .italic()
                            .foregroundColor(.hiNavy)
                            .padding(.top, 4)
                    }.padding().frame(maxWidth: .infinity, alignment: .leading)
                     .background(Color.hiSystemBg).cornerRadius(16)
                    
                    // SECTION 2 — We're not anti-AI
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
                    
                    // SECTION 3 — The HUMAN Framework
                    VStack(alignment: .leading, spacing: 14) {
                        Text("The HUMAN Framework")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        Text("Five dimensions — the things AI can't be: conscious, empathetic, ethical, alive, and transparent.")
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                            .padding(.bottom, 4)
                        ForEach(frameworkRows, id: \.title) { row in
                            HStack(alignment: .top, spacing: 10) {
                                Image(systemName: row.icon)
                                    .font(.system(size: 16))
                                    .foregroundColor(.hiGold)
                                    .frame(width: 24)
                                    .padding(.top, 2)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(row.title)
                                        .font(.system(size: 13, weight: .semibold))
                                        .foregroundColor(.hiNavy)
                                    Text(row.subtitle)
                                        .font(.system(size: 11))
                                        .foregroundColor(.secondary)
                                        .fixedSize(horizontal: false, vertical: true)
                                }
                            }
                        }
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // SECTION 4 — Stats (UPDATED numbers)
                    if let stats = api.stats {
                        HStack(spacing: 0) {
                            statBox("\(stats.total_companies ?? 0)", "Brands")
                            statBox("\(stats.data_sources ?? 0)", "Sources")
                            statBox("5", "Dimensions")
                            statBox("3", "Gates")
                        }.background(Color.hiSystemBg).cornerRadius(16)
                    }
                    
                    // SECTION 5 — What HI Grade does for you (NEW)
                    VStack(alignment: .leading, spacing: 16) {
                        Text("What HI Grade does for you")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        ForEach(beforeYouRows, id: \.title) { row in
                            HStack(alignment: .top, spacing: 12) {
                                Image(systemName: row.icon)
                                    .font(.system(size: 16))
                                    .foregroundColor(.hiGold)
                                    .frame(width: 24)
                                    .padding(.top, 2)
                                VStack(alignment: .leading, spacing: 3) {
                                    Text(row.title)
                                        .font(.system(size: 13, weight: .semibold))
                                        .foregroundColor(.hiNavy)
                                    Text(row.desc)
                                        .font(.system(size: 11))
                                        .foregroundColor(.secondary)
                                        .fixedSize(horizontal: false, vertical: true)
                                }
                            }
                        }
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // SECTION 6 — How Scoring Works
                    VStack(alignment: .leading, spacing: 8) {
                        Text("How Scoring Works")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        Text("Every company is scored 0–100 across five dimensions using 42 free public data sources. No AI in the scoring. No surveys. No pay-to-play. Pass all 3 gates — Dimensions, Evidence, and Momentum — and you're Gold HI Grade™.")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                        Text("Floor rule: if any HUMAN dimension scores below 30, the composite is capped at 50. One severely failing dimension can't be averaged away.")
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                            .padding(.top, 4)
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // SECTION 7 — The Founder (NEW)
                    VStack(alignment: .leading, spacing: 10) {
                        Text("The Founder")
                            .font(.system(size: 17, weight: .bold, design: .serif))
                            .foregroundColor(.hiNavy)
                        Text("HI Grade started on Earth Day 2025 with a simple question: **if AI is changing everything, who's measuring what we're losing?**")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                            .lineSpacing(3)
                        Text("I'd spent years in technology — enough to know what AI could do, and enough to worry about what it was replacing. Not just jobs. **The craft behind the work. The empathy in the service. The humans in the loop.**")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                            .lineSpacing(3)
                        Text("I couldn't find a tool that measured any of that. So I built one. The methodology is open source because **a transparency framework that hides its own math would be hypocritical.**")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                            .lineSpacing(3)
                        Text("Don't panic.")
                            .font(.system(size: 16, weight: .bold, design: .serif))
                            .foregroundColor(.hiNavy)
                            .padding(.top, 6)
                        Text("Every journey starts somewhere. The data will get better. The gates will get stricter. The companies will adapt. That's the point.")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                            .lineSpacing(3)
                    }.padding().frame(maxWidth: .infinity, alignment: .leading)
                     .background(Color.hiSystemBg).cornerRadius(16)
                    
                    // SECTION 8 — Data Sources
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Data Sources (42)")
                            .font(.system(size: 18, weight: .bold, design: .serif))
                            .foregroundColor(.hiNavy)
                        Text("SEC EDGAR (10-K, 8-K, DEF 14A, Form 4), EPA ECHO, BLS, CDP, Glassdoor, Disability:IN DEI Index, HRC Corporate Equality Index, Yahoo Finance, FMP, Alpha Vantage, Finnhub, FRED, NewsAPI, Layoffs.fyi, WARN Act, CEO monitoring, CFPB, FEC, CPSC, Have I Been Pwned, iFixit, OSHA, FTC, EEOC, USPTO, FDA, DOL, BBB, GRI, SBTi, IRS 990, B Corp Directory, Fair Trade, USDA Organic, Climate Neutral, 1% for the Planet, NHTSA, and industry deforestation risk data.")
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                            .lineSpacing(3)
                        Text("All scores are estimated from public data. Gold HI Grade status is earned algorithmically, not purchased.")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.hiNavy)
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // SECTION 9 — Coming Soon (UPDATED)
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Coming Soon")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        Text("On the roadmap. Not yet built.")
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                            .padding(.bottom, 2)
                        comingSoonRow(icon: "barcode.viewfinder", title: "Barcode Scanner", desc: "Scan any product in-store")
                        comingSoonRow(icon: "doc.text.viewfinder", title: "Document Scanner", desc: "Know what you're signing")
                        comingSoonRow(icon: "square.and.arrow.up", title: "Share Cards", desc: "Spread the balance")
                        comingSoonRow(icon: "bell.fill", title: "Heartbeat Alerts", desc: "Push when companies decay")
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // SECTION 10 — Get in Touch
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
                        Link(destination: URL(string: "https://github.com/thehibalance/hi")!) {
                            HStack(spacing: 8) {
                                Image(systemName: "chevron.left.forwardslash.chevron.right").foregroundColor(.hiGold)
                                Text("github.com/thehibalance/hi").font(.system(size: 14, weight: .medium))
                            }
                        }
                    }.padding().background(Color.hiSystemBg).cornerRadius(16)
                    
                    // Footer
                    VStack(spacing: 8) {
                        Text("The HI Balance · Patent Pending · HI Grade™")
                            .font(.system(size: 11)).foregroundColor(.secondary)
                        Text("Humanwashing™ · Algorithmic Harm Index™")
                            .font(.system(size: 11)).foregroundColor(.secondary)
                        Text("Morf Innovations LLC")
                            .font(.system(size: 11)).foregroundColor(.secondary)
                        Text("Gold HI Grade requires all 5 HUMAN dimensions ≥ 60, each verified by public data, and no critical decay (90-day Heartbeat). Spec v1.2.0. Scores are estimated from public data. Not financial or legal advice.")
                            .font(.system(size: 9))
                            .foregroundColor(.secondary.opacity(0.7))
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 16)
                            .padding(.top, 4)
                    }.padding(.vertical)
                    
                    Spacer(minLength: 40)
                }.padding(.horizontal)
            }
            .background(Color.hiBackground)
            .navigationTitle("About")
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
