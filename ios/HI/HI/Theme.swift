import SwiftUI

extension Color {
    static let hiNavy = Color(red: 0.106, green: 0.227, blue: 0.361)       // #1B3A5C
    static let hiSky = Color(red: 0.180, green: 0.369, blue: 0.557)        // #2E5E8E
    static let hiGold = Color(red: 0.769, green: 0.608, blue: 0.125)       // #C49B20
    static let hiGreen = Color(red: 0.086, green: 0.639, blue: 0.247)      // #16A34A
    static let hiOrange = Color(red: 0.851, green: 0.467, blue: 0.024)     // #D97706
    static let hiRed = Color(red: 0.863, green: 0.145, blue: 0.145)        // #DC2626
    static let hiBackground = Color(red: 0.976, green: 0.980, blue: 0.988) // #F9FAFB
    
    static func hiScore(_ score: Double) -> Color {
        if score >= 70 { return .hiGreen }
        if score >= 42 { return .hiOrange }
        return .hiRed
    }
}

struct HIFont {
    static func title(_ size: CGFloat = 28) -> Font { .system(size: size, weight: .bold, design: .serif) }
    static func score(_ size: CGFloat = 32) -> Font { .system(size: size, weight: .heavy, design: .rounded) }
    static func body(_ size: CGFloat = 15) -> Font { .system(size: size, weight: .regular) }
    static func caption(_ size: CGFloat = 12) -> Font { .system(size: size, weight: .medium) }
    static func label(_ size: CGFloat = 11) -> Font { .system(size: size, weight: .semibold) }
}
