import SwiftUI

extension Color {
    static let hiNavy = Color(red: 0.106, green: 0.227, blue: 0.361)
    static let hiSky = Color(red: 0.180, green: 0.369, blue: 0.557)
    static let hiGold = Color(red: 0.769, green: 0.608, blue: 0.125)
    static let hiGreen = Color(red: 0.086, green: 0.639, blue: 0.247)
    static let hiOrange = Color(red: 0.851, green: 0.467, blue: 0.024)
    static let hiRed = Color(red: 0.863, green: 0.145, blue: 0.145)
    static let hiBackground = Color(red: 0.976, green: 0.980, blue: 0.988)
    #if os(iOS)
    static let hiCardBg = Color(UIColor.secondarySystemBackground)
    static let hiSystemBg = Color(UIColor.systemBackground)
    static let hiGray6 = Color(UIColor.systemGray6)
    #else
    static let hiCardBg = Color(NSColor.controlBackgroundColor)
    static let hiSystemBg = Color(NSColor.windowBackgroundColor)
    static let hiGray6 = Color(NSColor.controlBackgroundColor)
    #endif
    
    static func hiScore(_ score: Double) -> Color {
        if score >= 70 { return .hiGreen }
        if score >= 42 { return .hiOrange }
        return .hiRed
    }
}

struct HIFont {
    static func title(_ size: CGFloat = 28) -> Font { .system(size: size, weight: .bold, design: .serif) }
    static func score(_ size: CGFloat = 32) -> Font { .system(size: size, weight: .heavy, design: .rounded) }
    static func caption(_ size: CGFloat = 12) -> Font { .system(size: size, weight: .medium) }
}
