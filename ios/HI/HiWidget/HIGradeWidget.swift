import WidgetKit
import SwiftUI

// MARK: - DID YOU KNOW
//
// Mirrors the website's Did You Know carousel (docs/index.html `_dykFacts`).
// Six rotating cards. Two of them (index 0 and index 4) get mutated with live
// Balanced Board data on each timeline build, just like buildDynamicDYK() on
// the web. The rest are static framework talking points.
//
// Widget constraints differ from the web: Apple's WidgetKit won't let us flip
// every 8 seconds (battery), so instead we build a timeline of 6 entries
// spaced 30 minutes apart (3-hour cycle), then refresh with fresh API data
// for the next cycle. Net effect: a fact every half hour, with live counts
// updated every 3 hours.

struct DYKFact {
    let icon: String      // emoji shown top-left
    let body: String      // markdown — **bold** is rendered properly by SwiftUI Text
}

struct HIGradeEntry: TimelineEntry {
    let date: Date
    let fact: DYKFact
}

// MARK: - Static Facts (verbatim parity with website _dykFacts where possible)

private let staticFacts: [DYKFact] = [
    // Card 0 — gets overwritten by live Balanced Board count when API responds
    DYKFact(
        icon: "✨",
        body: "**The Balanced Board is rare.** Only a handful of companies pass — earning all five HUMAN dimensions ≥ 60 with verified public data and no critical decay."
    ),
    // Card 1 — Meta AI rapid displacement (matches homepage Spotlight #2)
    DYKFact(
        icon: "🤖",
        body: "**AI rapid displacement: Meta.** 21,000+ employees laid off in 2022–2023. In January 2025, AI announced to replace mid-level engineers. The H dimension reflects it — months before layoffs hit headlines."
    ),
    // Card 2 — Floor rule (matches homepage Spotlight #3)
    DYKFact(
        icon: "📐",
        body: "**A composite of 50 with four 90s.** The floor rule caps composite at 50 if any HUMAN dimension falls below 42. Greatness in three areas doesn't excuse failure in a fourth. 42 = Douglas Adams said so."
    ),
    // Card 3 — HUMAN Decline
    DYKFact(
        icon: "🔍",
        body: "**HUMAN Decline tracks which companies are eroding.** Combined signals from Heartbeat (decay), Shield (moat), Contagion (industry drift), Lens (ESG gap), and Watermark (performative empathy)."
    ),
    // Card 4 — gets overwritten by live featured Balanced Board member when API responds
    DYKFact(
        icon: "🏆",
        body: "**The Balanced Board features rare leaders.** Companies that earn all five HUMAN dimensions above 60 with verified public data, every dimension grounded in real metrics."
    ),
    // Card 5 — The credit-rating mission (matches homepage Spotlight #5)
    DYKFact(
        icon: "📊",
        body: "**The first credit-rating-style score for being human.** No AI. Deterministic math. Edge-to-cloud. 42 public data sources. No ESG raters. No certification fees. No paid placements. Just the math."
    ),
]

// MARK: - Timeline Provider

struct HIGradeProvider: TimelineProvider {

    private let apiBase = "https://api.thehibalance.org/api/v1"
    private let cycleEntryCount = 6
    private let entryIntervalMinutes = 30

    func placeholder(in context: Context) -> HIGradeEntry {
        HIGradeEntry(date: .now, fact: staticFacts[0])
    }

    func getSnapshot(in context: Context, completion: @escaping (HIGradeEntry) -> Void) {
        // Snapshot is shown in the widget gallery; static fact is fine.
        completion(HIGradeEntry(date: .now, fact: staticFacts[0]))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<HIGradeEntry>) -> Void) {
        Task {
            let facts = await buildFacts()
            let now = Date()
            let cal = Calendar.current

            var entries: [HIGradeEntry] = []
            for i in 0..<cycleEntryCount {
                let date = cal.date(byAdding: .minute, value: i * entryIntervalMinutes, to: now) ?? now
                let fact = facts[i % facts.count]
                entries.append(HIGradeEntry(date: date, fact: fact))
            }

            // Reload after the last entry plays out — fresh API fetch, fresh card 0/4 data.
            let timeline = Timeline(entries: entries, policy: .atEnd)
            completion(timeline)
        }
    }

    // MARK: Live Data Injection
    //
    // Mirrors the website's buildDynamicDYK(). Fetches /grades/top, filters to actually
    // balanced companies, mutates cards 0 and 4 with the real count and the top member.
    // Returns the static array unchanged on any failure.

    private func buildFacts() async -> [DYKFact] {
        var facts = staticFacts

        guard let url = URL(string: "\(apiBase)/grades/top?limit=100") else { return facts }
        guard let (data, _) = try? await URLSession.shared.data(from: url) else { return facts }

        struct TopResponse: Codable {
            let results: [TopCompany]?
        }
        struct TopCompany: Codable {
            let company: String?
            let composite: Double?
            let hi_balanced: Bool?
        }

        guard let response = try? JSONDecoder().decode(TopResponse.self, from: data),
              let results = response.results else { return facts }

        // Filter to actually balanced companies, dedup by name, sort by composite descending.
        var seen = Set<String>()
        let balanced = results
            .filter { $0.hi_balanced == true }
            .filter { c in
                guard let name = c.company, !name.isEmpty else { return false }
                if seen.contains(name) { return false }
                seen.insert(name)
                return true
            }
            .sorted { ($0.composite ?? 0) > ($1.composite ?? 0) }

        let n = balanced.count
        let totalRounded = "700"   // matches website default until /stats endpoint is wired

        // ── Card 0 — count + names ─────────────────────────────────────
        if n == 0 {
            facts[0] = DYKFact(
                icon: "✨",
                body: "**No companies currently pass the Balanced Board.** Earning all five HUMAN dimensions above 60 with verified public data is rare. The math is strict on purpose."
            )
        } else if n == 1, let c = balanced.first, let name = c.company {
            facts[0] = DYKFact(
                icon: "✨",
                body: "**Only \(name) passes the Balanced Board today.** Out of \(totalRounded)+ scored, \(name) is the only company earning all five HUMAN dimensions above 60. The bar is high on purpose."
            )
        } else {
            let names = balanced.compactMap { $0.company }
            let namesStr: String
            if names.count == 2 {
                namesStr = "\(names[0]) and \(names[1])"
            } else {
                namesStr = names.dropLast().joined(separator: ", ") + ", and \(names.last ?? "")"
            }
            facts[0] = DYKFact(
                icon: "✨",
                body: "**\(n) companies pass the Balanced Board.** Out of \(totalRounded)+ scored, \(namesStr) earn all five HUMAN dimensions above 60. The bar is high on purpose."
            )
        }

        // ── Card 4 — featured top Balanced Board member ────────────────
        if let top = balanced.first, let name = top.company {
            let composite = Int(top.composite ?? 0)
            let countWord: String
            switch n {
            case 1: countWord = "the only company"
            case 2: countWord = "one of only two companies"
            case 3: countWord = "one of only three companies"
            default: countWord = "one of \(n) companies"
            }
            let countWordCapitalized = countWord.prefix(1).uppercased() + countWord.dropFirst()
            facts[4] = DYKFact(
                icon: "🏆",
                body: "**\(name) passes the Balanced Board.** Composite \(composite). All five HUMAN dimensions scored 60 or higher with verified public data. \(countWordCapitalized) out of \(totalRounded)+ that made the cut."
            )
        } else {
            facts[4] = DYKFact(
                icon: "🏆",
                body: "**The Balanced Board is empty today.** The decay system caught quality drift in companies that previously passed. The math is strict on purpose."
            )
        }

        return facts
    }
}

// MARK: - Theme

private let navy = Color(red: 0.106, green: 0.227, blue: 0.361)
private let gold = Color(red: 0.769, green: 0.608, blue: 0.125)
private let cardBg = Color(red: 0.980, green: 0.973, blue: 0.949)   // matches website #FAF8F2

// MARK: - Small Widget

struct HIGradeSmallView: View {
    let entry: HIGradeEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .top, spacing: 8) {
                Text(entry.fact.icon)
                    .font(.system(size: 18))
                Text("HUMAN SPOTLIGHT")
                    .font(.system(size: 8, weight: .heavy))
                    .tracking(1.5)
                    .foregroundColor(gold)
                    .padding(.top, 4)
                Spacer()
                Text("hi.")
                    .font(.system(size: 11, weight: .black, design: .rounded))
                    .foregroundColor(navy)
            }
            Text(.init(entry.fact.body))
                .font(.system(size: 11))
                .foregroundColor(navy)
                .lineSpacing(2)
                .multilineTextAlignment(.leading)
                .lineLimit(7)
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .padding(12)
    }
}

// MARK: - Medium Widget

struct HIGradeMediumView: View {
    let entry: HIGradeEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 10) {
                Text(entry.fact.icon)
                    .font(.system(size: 22))
                VStack(alignment: .leading, spacing: 2) {
                    Text("HUMAN SPOTLIGHT")
                        .font(.system(size: 9, weight: .heavy))
                        .tracking(1.8)
                        .foregroundColor(gold)
                    Text("hi.™ · The HI Balance™")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.secondary)
                }
                Spacer()
                Text("hi.")
                    .font(.system(size: 14, weight: .black, design: .rounded))
                    .foregroundColor(navy)
            }
            Text(.init(entry.fact.body))
                .font(.system(size: 12))
                .foregroundColor(navy)
                .lineSpacing(3)
                .multilineTextAlignment(.leading)
                .lineLimit(5)
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .padding(14)
    }
}

// MARK: - Family-aware Entry View

struct HIGradeWidgetEntryView: View {
    @Environment(\.widgetFamily) var family
    let entry: HIGradeEntry

    var body: some View {
        Group {
            switch family {
            case .systemMedium:
                HIGradeMediumView(entry: entry)
            default:
                HIGradeSmallView(entry: entry)
            }
        }
        .modifier(WidgetBackgroundModifier())
    }
}

private struct WidgetBackgroundModifier: ViewModifier {
    func body(content: Content) -> some View {
        if #available(iOS 17.0, *) {
            content.containerBackground(cardBg.gradient, for: .widget)
        } else {
            content.padding().background(cardBg)
        }
    }
}

// MARK: - Widget Configuration

struct HIGradeWidget: Widget {
    let kind = "HIGradeWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: HIGradeProvider()) { entry in
            HIGradeWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("HUMAN Spotlight — hi.")
        .description("Rotating insights from the HI Balance™ framework. Live-updated with the Balanced Board™.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

// MARK: - Entry Point

@main
struct HIWidgetBundle: WidgetBundle {
    var body: some Widget {
        HIGradeWidget()
    }
}
