import Foundation

class CacheManager {
    static let shared = CacheManager()
    private let defaults = UserDefaults.standard
    private let maxAge: TimeInterval = 24 * 60 * 60
    
    private struct CacheEntry: Codable {
        let data: Data
        let timestamp: Date
    }
    
    func save<T: Encodable>(_ value: T, key: String) {
        guard let data = try? JSONEncoder().encode(value) else { return }
        let entry = CacheEntry(data: data, timestamp: Date())
        guard let entryData = try? JSONEncoder().encode(entry) else { return }
        defaults.set(entryData, forKey: "cache_\(key)")
    }
    
    func load<T: Decodable>(_ type: T.Type, key: String) -> T? {
        guard let entryData = defaults.data(forKey: "cache_\(key)"),
              let entry = try? JSONDecoder().decode(CacheEntry.self, from: entryData) else { return nil }
        if Date().timeIntervalSince(entry.timestamp) > maxAge { return nil }
        return try? JSONDecoder().decode(T.self, from: entry.data)
    }
    
    func isFresh(key: String) -> Bool {
        guard let entryData = defaults.data(forKey: "cache_\(key)"),
              let entry = try? JSONDecoder().decode(CacheEntry.self, from: entryData) else { return false }
        return Date().timeIntervalSince(entry.timestamp) <= maxAge
    }
    
    func clear(key: String) { defaults.removeObject(forKey: "cache_\(key)") }
    
    func clearAll() {
        defaults.dictionaryRepresentation().keys.filter { $0.hasPrefix("cache_") }.forEach { defaults.removeObject(forKey: $0) }
    }
    
    func age(key: String) -> String? {
        guard let entryData = defaults.data(forKey: "cache_\(key)"),
              let entry = try? JSONDecoder().decode(CacheEntry.self, from: entryData) else { return nil }
        let mins = Int(Date().timeIntervalSince(entry.timestamp) / 60)
        if mins < 60 { return "\(mins)m ago" }
        return "\(mins / 60)h ago"
    }
}
