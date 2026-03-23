import SwiftUI

@main
struct HIApp: App {
    @StateObject private var api = APIService.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(api)
                .task { await api.loadStats() }
        }
    }
}
