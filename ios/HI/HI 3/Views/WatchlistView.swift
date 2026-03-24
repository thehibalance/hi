import SwiftUI

struct WatchlistView: View {
    @Environment(FavoritesManager.self) var favorites
    
    var body: some View {
        NavigationStack {
            List {
                if !favorites.favorites.isEmpty {
                    Section("WATCHLIST") {
                        ForEach(favorites.favorites) { fav in
                            NavigationLink(value: companyFrom(fav)) { favRow(fav) }
                        }
                    }
                }
                if !favorites.recents.isEmpty {
                    Section {
                        ForEach(favorites.recents) { rec in
                            NavigationLink(value: companyFrom(rec)) { favRow(rec) }
                        }
                    } header: { HStack { Text("RECENTLY VIEWED"); Spacer(); Button("Clear") { favorites.clearRecents() }.font(.system(size: 12)) } }
                }
                if favorites.favorites.isEmpty && favorites.recents.isEmpty {
                    Section {
                        VStack(spacing: 12) {
                            Text("⭐").font(.system(size: 40))
                            Text("No companies saved yet").font(.system(size: 16, weight: .semibold)).foregroundColor(.hiNavy)
                            Text("Search for a company and tap the star to add it.").font(.system(size: 13)).foregroundColor(.secondary).multilineTextAlignment(.center)
                        }.frame(maxWidth: .infinity).padding(.vertical, 40)
                    }
                }
            }
            .listStyle(.inset).navigationTitle("Watchlist")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.large)
            #endif
            .navigationDestination(for: Company.self) { CompanyDetailView(company: $0) }
        }
    }
    
    private func favRow(_ fav: FavoritesManager.FavoriteCompany) -> some View {
        HStack(spacing: 12) {
            ZStack {
                Circle().fill(fav.isGold ? Color.hiGold : Color.hiScore(fav.composite)).frame(width: 38, height: 38)
                if fav.isGold { Text("✦").font(.system(size: 14)).foregroundColor(.white) }
                else { Text("\(Int(fav.composite))").font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundColor(.white) }
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(fav.company).font(.system(size: 14, weight: .semibold)).foregroundColor(.hiNavy)
                if let t = fav.ticker { Text(t).font(.system(size: 11)).foregroundColor(.secondary) }
            }
            Spacer()
            Text("\(Int(fav.composite))").font(.system(size: 16, weight: .heavy, design: .rounded)).foregroundColor(fav.isGold ? .hiGold : .hiScore(fav.composite))
        }
    }
    
    private func companyFrom(_ fav: FavoritesManager.FavoriteCompany) -> Company {
        .stub(company: fav.company, ticker: fav.ticker, composite: fav.composite, hi_balanced: fav.isGold)
    }
}
