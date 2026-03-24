import SwiftUI

struct HomeView: View {
    @Environment(APIService.self) var api
    @State private var searchText = ""
    @State private var results: [Company] = []
    @State private var goldCompanies: [Company] = []
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 0) {
                    VStack(spacing: 8) {
                        Text("HI.").font(.system(size: 48, weight: .black, design: .serif)).foregroundColor(.hiNavy)
                        Text("Think human intelligence.").font(.system(size: 15, weight: .medium)).foregroundColor(.hiGold)
                        if let stats = api.stats {
                            Text("\(stats.total_companies ?? 0) brands scored · \(stats.data_sources ?? 0) data sources")
                                .font(HIFont.caption()).foregroundColor(.secondary).padding(.top, 2)
                        }
                    }.padding(.top, 20).padding(.bottom, 16)
                    
                    HStack {
                        Image(systemName: "magnifyingglass").foregroundColor(.secondary)
                        TextField("Search any company...", text: $searchText)
                            .textFieldStyle(.plain).autocorrectionDisabled()
                            .onSubmit { Task { await doSearch() } }
                        if !searchText.isEmpty {
                            Button { searchText = ""; results = [] } label: {
                                Image(systemName: "xmark.circle.fill").foregroundColor(.secondary)
                            }
                        }
                    }
                    .padding(12).background(Color.hiSystemBg).cornerRadius(12)
                    .shadow(color: .black.opacity(0.06), radius: 8, y: 2).padding(.horizontal)
                    .onChange(of: searchText) { _, _ in
                        Task { try? await Task.sleep(nanoseconds: 300_000_000); await doSearch() }
                    }
                    
                    if !results.isEmpty {
                        LazyVStack(spacing: 0) {
                            ForEach(results) { company in
                                NavigationLink(value: company) {
                                    CompanyRow(company: company, threshold: api.goldThreshold)
                                }
                                Divider().padding(.leading, 60)
                            }
                        }
                        .background(Color.hiSystemBg).cornerRadius(12)
                        .shadow(color: .black.opacity(0.04), radius: 6, y: 2)
                        .padding(.horizontal).padding(.top, 8)
                    }
                    
                    if results.isEmpty && !goldCompanies.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Text("✦").foregroundColor(.hiGold)
                                Text("GOLD HI GRADE").font(.system(size: 11, weight: .bold)).tracking(1.5).foregroundColor(.hiGold)
                            }.padding(.horizontal).padding(.top, 24)
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 12) {
                                    ForEach(goldCompanies) { c in
                                        NavigationLink(value: c) { GoldCard(company: c) }
                                    }
                                }.padding(.horizontal)
                            }
                        }
                    }
                    Spacer(minLength: 40)
                }
            }
            .background(Color.hiBackground)
            .navigationDestination(for: Company.self) { CompanyDetailView(company: $0) }
        }
        .task { let top = await api.top(limit: 100); goldCompanies = top.filter { $0.hi_balanced == true } }
    }
    
    private func doSearch() async {
        guard !searchText.isEmpty else { results = []; return }
        results = await api.search(searchText)
    }
}

struct CompanyRow: View {
    let company: Company; let threshold: Double
    var score: Double { company.composite ?? 0 }
    var isGold: Bool { company.hi_balanced == true }
    
    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle().fill(isGold ? Color.hiGold : Color.hiScore(score)).frame(width: 44, height: 44)
                if isGold { Text("✦").font(.system(size: 18)).foregroundColor(.white) }
                else { Text("\(Int(score))").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundColor(.white) }
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(company.company ?? "Unknown").font(.system(size: 15, weight: .semibold)).foregroundColor(.hiNavy).lineLimit(1)
                HStack(spacing: 6) {
                    if let t = company.ticker, !t.isEmpty {
                        Text(t).font(HIFont.caption(10)).foregroundColor(.secondary).padding(.horizontal, 6).padding(.vertical, 2).background(Color.hiGray6).cornerRadius(4)
                    }
                    if let i = company.industry { Text(i).font(HIFont.caption(10)).foregroundColor(.secondary).lineLimit(1) }
                }
            }
            Spacer()
            Text("\(Int(score))").font(HIFont.score(20)).foregroundColor(isGold ? .hiGold : .hiScore(score))
            Image(systemName: "chevron.right").font(.caption).foregroundColor(.secondary)
        }.padding(.horizontal, 16).padding(.vertical, 10)
    }
}

struct GoldCard: View {
    let company: Company
    var body: some View {
        VStack(spacing: 6) {
            Text("✦").font(.system(size: 20)).foregroundColor(.white)
            Text(company.company ?? "").font(.system(size: 12, weight: .bold)).foregroundColor(.white).lineLimit(1)
            Text("\(Int(company.composite ?? 0))").font(.system(size: 18, weight: .heavy, design: .rounded)).foregroundColor(.white)
        }
        .frame(width: 110, height: 100)
        .background(LinearGradient(colors: [.hiGold, Color(red: 0.65, green: 0.5, blue: 0.1)], startPoint: .topLeading, endPoint: .bottomTrailing))
        .cornerRadius(12)
    }
}
