import SwiftUI

struct WatchlistView: View {
    @EnvironmentObject var api: APIService
    @EnvironmentObject var favorites: FavoritesManager
    
    var body: some View {
        NavigationStack {
            List {
                if !favorites.favorites.isEmpty {
                    Section {
                        ForEach(favorites.favorites) { fav in
                            NavigationLink(value: companyFrom(fav)) {
                                favRow(fav)
                            }
                        }
                        .onDelete { idx in
                            idx.forEach { favorites.favorites.remove(at: $0) }
                        }
                    } header: {
                        HStack {
                            Text("WATCHLIST")
                            Spacer()
                            Text("\(favorites.favorites.count)")
                                .font(.system(size: 12, weight: .bold, design: .rounded))
                                .foregroundColor(.hiGold)
                        }
                    }
                }
                
                if !favorites.recents.isEmpty {
                    Section {
                        ForEach(favorites.recents) { rec in
                            NavigationLink(value: companyFrom(rec)) {
                                favRow(rec)
                            }
                        }
                    } header: {
                        HStack {
                            Text("RECENTLY VIEWED")
                            Spacer()
                            Button("Clear") { favorites.clearRecents() }
                                .font(.system(size: 12))
                                .foregroundColor(.hiSky)
                        }
                    }
                }
                
                if favorites.favorites.isEmpty && favorites.recents.isEmpty {
                    Section {
                        VStack(spacing: 12) {
                            Text("⭐").font(.system(size: 40))
                            Text("No companies saved yet")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.hiNavy)
                            Text("Search for a company and tap the star to add it to your watchlist.")
                                .font(.system(size: 13))
                                .foregroundColor(.secondary)
                                .multilineTextAlignment(.center)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 40)
                    }
                }
            }
            .listStyle(.insetGrouped)
            .navigationTitle("Watchlist")
            .navigationBarTitleDisplayMode(.large)
            .navigationDestination(for: Company.self) { company in
                CompanyDetailView(company: company)
            }
        }
    }
    
    private func favRow(_ fav: FavoritesManager.FavoriteCompany) -> some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(fav.isGold ? Color.hiGold : Color.hiScore(fav.composite))
                    .frame(width: 38, height: 38)
                if fav.isGold {
                    Text("✦").font(.system(size: 14)).foregroundColor(.white)
                } else {
                    Text("\(Int(fav.composite))")
                        .font(.system(size: 14, weight: .heavy, design: .rounded))
                        .foregroundColor(.white)
                }
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(fav.company)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.hiNavy)
                if let t = fav.ticker {
                    Text(t).font(.system(size: 11)).foregroundColor(.secondary)
                }
            }
            Spacer()
            Text("\(Int(fav.composite))")
                .font(.system(size: 16, weight: .heavy, design: .rounded))
                .foregroundColor(fav.isGold ? .hiGold : .hiScore(fav.composite))
        }
    }
    
    private func companyFrom(_ fav: FavoritesManager.FavoriteCompany) -> Company {
        Company(
            company: fav.company, ticker: fav.ticker, composite: fav.composite,
            industry: nil, sic_description: nil, hi_balanced: fav.isGold, hi_grade: nil,
            D_H: nil, D_U: nil, D_M: nil, D_A: nil, D_N: nil,
            decay_index: nil, decay_level: nil, shield_score: nil, shield_tier: nil,
            genome: nil, algo_harm: nil, humanwashing_flags: nil, domains: nil
        )
    }
}
