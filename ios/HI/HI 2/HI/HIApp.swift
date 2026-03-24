import SwiftUI

@main
struct HIApp: App {
    @State private var api = APIService.shared
    @State private var favorites = FavoritesManager.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(api)
                .environment(favorites)
                .task { await api.loadStats() }
        }
    }
}
