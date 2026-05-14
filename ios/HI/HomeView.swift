import SwiftUI
import Combine

struct HomeView: View {
    @Environment(APIService.self) var api
    @State private var searchText = ""
    @State private var results: [Company] = []
    @State private var topCompanies: [Company] = []
    @FocusState private var isSearchFocused: Bool
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 0) {
                    VStack(spacing: 8) {
                        Image("hi-logo")
                            .resizable()
                            .scaledToFit()
                            .frame(height: 80)
                        
                        Text("Human kind?")
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(.hiGold)
                        Text("The fifth check before every decision.")
                            .font(.system(size: 12, weight: .regular))
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.top, 2)
                        
                        if let stats = api.stats {
                            Text("\(stats.total_companies ?? 0) brands scored · \(stats.data_sources ?? 0) data sources")
                                .font(HIFont.caption()).foregroundColor(.secondary).padding(.top, 2)
                            PipelineCountdown()
                                .padding(.top, 2)
                        }
                    }.padding(.top, 20).padding(.bottom, 16)
                    
                    searchBar
                    
                    if !results.isEmpty {
                        searchResults
                    }
                    
                    if results.isEmpty && !topCompanies.isEmpty {
                        VStack(alignment: .leading, spacing: 0) {
                            Text("TOP HI GRADES")
                                .font(.system(size: 11, weight: .bold))
                                .tracking(1.5)
                                .foregroundColor(.hiNavy)
                                .padding(.horizontal)
                                .padding(.top, 20)
                                .padding(.bottom, 12)
                            
                            LazyVStack(spacing: 0) {
                                ForEach(Array(topCompanies.enumerated()), id: \.element.id) { idx, company in
                                    NavigationLink(value: company) {
                                        TopCompanyRow(rank: idx + 1, company: company, threshold: api.goldThreshold)
                                    }
                                    if idx < topCompanies.count - 1 {
                                        Divider().padding(.leading, 60)
                                    }
                                }
                            }
                            .background(Color.hiSystemBg)
                            .cornerRadius(12)
                            .shadow(color: .black.opacity(0.04), radius: 6, y: 2)
                            .padding(.horizontal)
                        }
                    }
                    
                    Spacer(minLength: 40)
                }
            }
            .scrollDismissesKeyboard(.immediately)
            .background(Color.hiBackground)
            .navigationDestination(for: Company.self) { CompanyDetailView(company: $0) }
        }
        .task {
            let top = await api.top(limit: 100)
            var seen = Set<String>()
            var tops: [Company] = []
            
            for c in top {
                guard (c.composite ?? 0) > 0 else { continue }
                let key = c.ticker ?? c.company ?? UUID().uuidString
                guard !seen.contains(key) else { continue }
                seen.insert(key)
                tops.append(c)
            }
            topCompanies = Array(tops.prefix(10))
        }
    }
    
    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass").foregroundColor(.secondary)
            TextField("Search any company...", text: $searchText)
                .textFieldStyle(.plain).autocorrectionDisabled()
                .focused($isSearchFocused)
                .onSubmit {
                    isSearchFocused = false
                    Task { await doSearch() }
                }
            if !searchText.isEmpty {
                Button { searchText = ""; results = []; isSearchFocused = false } label: {
                    Image(systemName: "xmark.circle.fill").foregroundColor(.secondary)
                }
            }
        }
        .padding(12).background(Color.hiSystemBg).cornerRadius(12)
        .shadow(color: .black.opacity(0.06), radius: 8, y: 2).padding(.horizontal)
        .onChange(of: searchText) { _, _ in
            Task { try? await Task.sleep(nanoseconds: 300_000_000); await doSearch() }
        }
    }
    
    private var searchResults: some View {
        LazyVStack(spacing: 0) {
            ForEach(results) { company in
                NavigationLink(value: company) {
                    CompanyRow(company: company, threshold: api.goldThreshold)
                }
                .simultaneousGesture(TapGesture().onEnded {
                    isSearchFocused = false
                })
                Divider().padding(.leading, 60)
            }
        }
        .background(Color.hiSystemBg).cornerRadius(12)
        .shadow(color: .black.opacity(0.04), radius: 6, y: 2)
        .padding(.horizontal).padding(.top, 8)
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
                if isGold {
                    Image("hi-gold")
                        .resizable()
                        .scaledToFit()
                        .frame(height: 28)
                        .clipShape(Circle())
                } else {
                    Text("\(Int(score))")
                        .font(.system(size: 16, weight: .heavy, design: .rounded))
                        .foregroundColor(.white)
                }
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

struct TopCompanyRow: View {
    let rank: Int
    let company: Company
    let threshold: Double
    
    var score: Double { company.composite ?? 0 }
    var isGold: Bool { company.hi_balanced == true }
    
    var body: some View {
        HStack(spacing: 12) {
            Text("#\(rank)")
                .font(.system(size: 13, weight: .bold, design: .rounded))
                .foregroundColor(.secondary)
                .frame(width: 30, alignment: .leading)
            ZStack {
                Circle()
                    .fill(isGold ? Color.hiGold : Color.hiScore(score))
                    .frame(width: 40, height: 40)
                if isGold {
                    Image("hi-gold")
                        .resizable()
                        .scaledToFit()
                        .frame(height: 24)
                        .clipShape(Circle())
                } else {
                    Text("\(Int(score))")
                        .font(.system(size: 14, weight: .heavy, design: .rounded))
                        .foregroundColor(.white)
                }
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(company.company ?? "Unknown")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.hiNavy)
                    .lineLimit(1)
                HStack(spacing: 6) {
                    if let t = company.ticker, !t.isEmpty {
                        Text(t)
                            .font(HIFont.caption(10))
                            .foregroundColor(.secondary)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.hiGray6)
                            .cornerRadius(4)
                    }
                    if let i = company.industry {
                        Text(i)
                            .font(HIFont.caption(10))
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }
                }
            }
            Spacer()
            Text("\(Int(score))")
                .font(HIFont.score(18))
                .foregroundColor(isGold ? .hiGold : .hiScore(score))
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
    }
}

struct PipelineCountdown: View {
    @State private var now = Date()
    
    let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
    
    private var nextMidnightCST: Date {
        var cal = Calendar.current
        cal.timeZone = TimeZone(identifier: "America/Chicago")!
        let cstNow = now
        var comps = cal.dateComponents([.year, .month, .day], from: cstNow)
        comps.hour = 0
        comps.minute = 0
        comps.second = 0
        guard let todayMidnight = cal.date(from: comps) else { return now }
        let nextMidnight = todayMidnight <= now ? cal.date(byAdding: .day, value: 1, to: todayMidnight)! : todayMidnight
        return nextMidnight
    }
    
    private var countdown: String {
        let diff = nextMidnightCST.timeIntervalSince(now)
        if diff <= 0 { return "Updating now..." }
        let h = Int(diff) / 3600
        let m = (Int(diff) % 3600) / 60
        let s = Int(diff) % 60
        return String(format: "%02d:%02d:%02d", h, m, s)
    }
    
    var body: some View {
        HStack(spacing: 4) {
            Circle().fill(Color.green).frame(width: 6, height: 6)
            Text("Connected · API live · Next update: \(countdown)")
                .font(.system(size: 10, weight: .medium, design: .monospaced))
                .foregroundColor(.secondary)
        }
        .onReceive(timer) { _ in now = Date() }
    }
}
