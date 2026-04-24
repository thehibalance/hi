import AppIntents

struct HIShortcutsProvider: AppShortcutsProvider {
    
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: GetHIGradeIntent(),
            phrases: [
                "Get \(.applicationName) for \(\.$company)",
                "\(.applicationName) \(\.$company)",
                "HI Grade \(\.$company) with \(.applicationName)",
                "Check \(\.$company) on \(.applicationName)",
                "How human is \(\.$company) on \(.applicationName)",
                "Score \(\.$company) with \(.applicationName)",
            ],
            shortTitle: "Get HI Grade",
            systemImageName: "chart.bar.fill"
        )
        AppShortcut(
            intent: QuickHIGradeIntent(),
            phrases: [
                "Quick \(.applicationName) for \(\.$company)",
                "\(.applicationName) score \(\.$company)",
            ],
            shortTitle: "Quick Score",
            systemImageName: "bolt.fill"
        )
    }
}
