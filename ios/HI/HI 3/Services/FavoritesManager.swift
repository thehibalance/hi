import Foundation
import Observation

@Observable
class FavoritesManager {
    static let shared = FavoritesManager()
    private let key = "hi_favorites"
    private let recentsKey = "hi_recents"
    
    var favorites: [FavoriteCompany] = []
    var recents: [FavoriteCompany] = []
    
    struct FavoriteCompany: Codable, Identifiable, Equatable {
        var id: String { ticker ?? company }
        let company: String
        let ticker: String?
        let composite: Double
        let isGold: Bool
        let addedAt: Date
    }
    
    init() { load() }
    
    func isFavorite(_ ticker: String?) -> Bool {
        guard let t = ticker else { return false }
        return favorites.contains { $0.ticker == t }
    }
    
    func toggle(_ company: Company) {
        let ticker = company.ticker ?? ""
        if let idx = favorites.firstIndex(where: { $0.ticker == ticker }) {
            favorites.remove(at: idx)
        } else {
            let fav = FavoriteCompany(company: company.company ?? "Unknown", ticker: company.ticker, composite: company.composite ?? 0, isGold: company.hi_balanced == true, addedAt: Date())
            favorites.insert(fav, at: 0)
        }
        save()
    }
    
    func addRecent(_ company: Company) {
        let entry = FavoriteCompany(company: company.company ?? "Unknown", ticker: company.ticker, composite: company.composite ?? 0, isGold: company.hi_balanced == true, addedAt: Date())
        recents.removeAll { $0.id == entry.id }
        recents.insert(entry, at: 0)
        if recents.count > 20 { recents = Array(recents.prefix(20)) }
        if let data = try? JSONEncoder().encode(recents) { UserDefaults.standard.set(data, forKey: recentsKey) }
    }
    
    func clearRecents() { recents = []; UserDefaults.standard.removeObject(forKey: recentsKey) }
    
    private func save() {
        if let data = try? JSONEncoder().encode(favorites) { UserDefaults.standard.set(data, forKey: key) }
    }
    
    private func load() {
        if let data = UserDefaults.standard.data(forKey: key), let f = try? JSONDecoder().decode([FavoriteCompany].self, from: data) { favorites = f }
        if let data = UserDefaults.standard.data(forKey: recentsKey), let r = try? JSONDecoder().decode([FavoriteCompany].self, from: data) { recents = r }
    }
}
