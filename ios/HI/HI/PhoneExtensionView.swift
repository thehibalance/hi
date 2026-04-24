import SwiftUI
import AppIntents

// MARK: - Phone Extension Setup View

struct PhoneExtensionView: View {
    @State private var selectedApps: Set<String> = []
    @State private var showingSetup = false
    
    // Popular apps users would want to score
    private let popularApps: [(name: String, bundleID: String, icon: String, ticker: String)] = [
        ("Uber", "com.ubercab.UberClient", "car.fill", "UBER"),
        ("Instagram", "com.burbn.instagram", "camera.fill", "META"),
        ("Amazon", "com.amazon.Amazon", "cart.fill", "AMZN"),
        ("Starbucks", "com.starbucks.mystarbucks", "cup.and.saucer.fill", "SBUX"),
        ("Netflix", "com.netflix.Netflix", "play.tv.fill", "NFLX"),
        ("DoorDash", "com.dd.doordash", "bicycle", "DASH"),
        ("YouTube", "com.google.YouTube", "play.rectangle.fill", "GOOGL"),
        ("TikTok", "com.zhiliaoapp.musically", "music.note", "BDNCE"),
        ("McDonald's", "com.McDonalds.mobileapp", "fork.knife", "MCD"),
        ("Walmart", "com.walmart.electronics.Walmart", "bag.fill", "WMT"),
        ("Tesla", "com.tesla.TeslaApp", "bolt.car.fill", "TSLA"),
        ("Airbnb", "com.airbnb.app", "house.fill", "ABNB"),
        ("PayPal", "com.paypal.PPClient", "creditcard.fill", "PYPL"),
        ("Nike", "com.nike.nikeapp", "figure.run", "NKE"),
        ("Facebook", "com.facebook.Facebook", "person.2.fill", "META"),
        ("Lyft", "com.lyft.ios", "car.rear.fill", "LYFT"),
        ("Slack", "com.tinyspeck.chatlyio", "number", "CRM"),
        ("Zoom", "com.zoom.us.zVideo", "video.fill", "ZM"),
    ]
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    
                    // Hero
                    VStack(spacing: 12) {
                        Image(systemName: "apps.iphone")
                            .font(.system(size: 48))
                            .foregroundColor(.hiGold)
                        Text("Phone Extension")
                            .font(.system(size: 24, weight: .bold, design: .serif))
                            .foregroundColor(.hiNavy)
                        Text("See the HI Grade every time you open an app.\nPowered by Shortcuts automations.")
                            .font(.system(size: 14))
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.top, 20)
                    
                    // How it works
                    VStack(alignment: .leading, spacing: 16) {
                        Text("How It Works")
                            .font(.system(size: 17, weight: .bold))
                            .foregroundColor(.hiNavy)
                        
                        stepRow(number: 1, title: "Choose your apps", desc: "Select which apps you want scored")
                        stepRow(number: 2, title: "We create the automation", desc: "Opens Shortcuts with everything pre-configured")
                        stepRow(number: 3, title: "Open any app", desc: "A HI Grade card appears with the company's score")
                    }
                    .padding()
                    .background(Color.hiSystemBg)
                    .cornerRadius(16)
                    
                    // Siri tip
                    VStack(spacing: 12) {
                        HStack(spacing: 8) {
                            Image(systemName: "mic.fill")
                                .foregroundColor(.hiGold)
                            Text("Also works with Siri")
                                .font(.system(size: 15, weight: .semibold))
                                .foregroundColor(.hiNavy)
                        }
                        Text("\"Hey Siri, what's the HI Grade for Starbucks?\"")
                            .font(.system(size: 14, design: .monospaced))
                            .foregroundColor(.secondary)
                            .italic()
                    }
                    .padding()
                    .background(Color.hiGold.opacity(0.08))
                    .cornerRadius(16)
                    
                    // App picker
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Select Apps to Score")
                            .font(.system(size: 17, weight: .bold))
                            .foregroundColor(.hiNavy)
                        
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible()),
                        ], spacing: 10) {
                            ForEach(popularApps, id: \.bundleID) { app in
                                appCard(app: app)
                            }
                        }
                    }
                    .padding()
                    .background(Color.hiSystemBg)
                    .cornerRadius(16)
                    
                    // Setup button
                    if !selectedApps.isEmpty {
                        VStack(spacing: 8) {
                            Button {
                                openShortcutsSetup()
                            } label: {
                                HStack(spacing: 8) {
                                    Image(systemName: "gear.badge.checkmark")
                                    Text("Set Up \(selectedApps.count) App\(selectedApps.count == 1 ? "" : "s")")
                                }
                                .font(.system(size: 16, weight: .bold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 16)
                                .background(Color.hiNavy)
                                .cornerRadius(14)
                            }
                            
                            Text("Opens Shortcuts app to create automations")
                                .font(.system(size: 11))
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    // Manual setup instructions
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Manual Setup")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.hiNavy)
                        
                        Text("1. Open the Shortcuts app")
                            .font(.system(size: 13)).foregroundColor(.secondary)
                        Text("2. Tap Automation → New Automation")
                            .font(.system(size: 13)).foregroundColor(.secondary)
                        Text("3. Choose \"App\" → select the app → \"Is Opened\"")
                            .font(.system(size: 13)).foregroundColor(.secondary)
                        Text("4. Add action → search \"HI Grade\"")
                            .font(.system(size: 13)).foregroundColor(.secondary)
                        Text("5. Choose \"Get HI Grade\" and enter the company name")
                            .font(.system(size: 13)).foregroundColor(.secondary)
                        Text("6. Toggle \"Run Immediately\" on")
                            .font(.system(size: 13)).foregroundColor(.secondary)
                    }
                    .padding()
                    .background(Color.hiSystemBg)
                    .cornerRadius(16)
                    
                    Spacer(minLength: 40)
                }
                .padding(.horizontal)
            }
            .background(Color.hiBackground)
            .navigationTitle("Phone Extension")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
    
    private func stepRow(number: Int, title: String, desc: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color.hiNavy)
                    .frame(width: 28, height: 28)
                Text("\(number)")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.hiNavy)
                Text(desc)
                    .font(.system(size: 13))
                    .foregroundColor(.secondary)
            }
        }
    }
    
    private func appCard(app: (name: String, bundleID: String, icon: String, ticker: String)) -> some View {
        let isSelected = selectedApps.contains(app.bundleID)
        return Button {
            if isSelected { selectedApps.remove(app.bundleID) }
            else { selectedApps.insert(app.bundleID) }
        } label: {
            HStack(spacing: 10) {
                Image(systemName: app.icon)
                    .font(.system(size: 16))
                    .foregroundColor(isSelected ? .white : .hiNavy)
                    .frame(width: 24)
                VStack(alignment: .leading, spacing: 1) {
                    Text(app.name)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(isSelected ? .white : .hiNavy)
                    Text(app.ticker)
                        .font(.system(size: 10))
                        .foregroundColor(isSelected ? .white.opacity(0.7) : .secondary)
                }
                Spacer()
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.white)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(isSelected ? Color.hiNavy : Color.hiGray6)
            .cornerRadius(12)
        }
    }
    
    private func openShortcutsSetup() {
        // Open the Shortcuts app — users can create automations there
        // The App Intents we registered will appear as actions
        if let url = URL(string: "shortcuts://create-shortcut") {
            UIApplication.shared.open(url)
        }
    }
}

// MARK: - Siri Tip Banner (for HomeView)

struct SiriTipBanner: View {
    @State private var dismissed = false
    
    var body: some View {
        if !dismissed {
            HStack(spacing: 12) {
                Image(systemName: "mic.fill")
                    .font(.system(size: 20))
                    .foregroundColor(.hiGold)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Try: \"Hey Siri, HI Grade Starbucks\"")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.hiNavy)
                    Text("Works with any company name or ticker")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Button { withAnimation { dismissed = true } } label: {
                    Image(systemName: "xmark")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(.secondary)
                }
            }
            .padding(14)
            .background(Color.hiGold.opacity(0.08))
            .cornerRadius(12)
            .padding(.horizontal)
        }
    }
}
