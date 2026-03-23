import SwiftUI

struct ContentView: View {
    @EnvironmentObject var api: APIService
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem { Label("Search", systemImage: "magnifyingglass") }
                .tag(0)
            
            Human100View()
                .tabItem { Label("HUMAN 100", systemImage: "chart.bar.fill") }
                .tag(1)
            
            FeaturesView()
                .tabItem { Label("Features", systemImage: "square.grid.2x2.fill") }
                .tag(2)
            
            AboutView()
                .tabItem { Label("About", systemImage: "info.circle.fill") }
                .tag(3)
        }
        .tint(.hiNavy)
    }
}
