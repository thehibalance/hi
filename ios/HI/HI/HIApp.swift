import SwiftUI

@main
struct HIApp: App {
    @StateObject private var api = APIService.shared
    @StateObject private var favorites = FavoritesManager.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(api)
                .environmentObject(favorites)
                .task { await api.loadStats() }
        }
    }
}
