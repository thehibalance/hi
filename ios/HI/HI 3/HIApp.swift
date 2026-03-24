import SwiftUI

@main
struct HIApp: App {
    var api = APIService.shared
    var favorites = FavoritesManager.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(api)
                .environment(favorites)
                .task { await api.loadStats() }
        }
    }
}
