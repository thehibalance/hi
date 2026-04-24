import SwiftUI

@main
struct HIApp: App {
    @State private var api = APIService()
    @State private var favorites = FavoritesManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(api)
                .environment(favorites)
                .preferredColorScheme(.light)
                .task { await api.loadStats() }
        }
    }
}
