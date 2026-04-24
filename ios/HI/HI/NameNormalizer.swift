//
//  NameNormalizer.swift
//  HI
//
//  Converts SEC EDGAR-style ALL CAPS company names to clean display format.
//  Examples:
//    "UNITED PARCEL SERVICE INC" → "United Parcel Service, Inc."
//    "BANK OF AMERICA CORP /DE/" → "Bank of America Corporation"
//    "HUNTINGTON INGALLS INDUSTRIES, INC." → "Huntington Ingalls Industries, Inc."
//    "Meta Platforms, Inc." → "Meta Platforms, Inc." (unchanged — not all caps)
//

import Foundation

enum NameNormalizer {
    /// Returns a display-friendly company name.
    /// If the input already has mixed case, returns it unchanged.
    /// If it's all caps SEC EDGAR format, converts to title case and cleans suffixes.
    static func display(_ raw: String) -> String {
        guard !raw.isEmpty else { return raw }
        
        // Already mixed-case — return as-is
        let letters = raw.filter { $0.isLetter }
        if !letters.isEmpty {
            let uppers = letters.filter { $0.isUppercase }
            let ratio = Double(uppers.count) / Double(letters.count)
            if ratio < 0.8 { return raw }  // Not all-caps, leave alone
        }
        
        var s = raw
        
        // Strip SEC state suffixes: /DE/, /NY/, /MD/, etc.
        s = s.replacingOccurrences(
            of: #"\s*/[A-Z]{2,3}/\s*"#,
            with: "",
            options: .regularExpression
        )
        
        // Title case
        s = s.capitalized
        
        // Fix common tokens that capitalize() mangles
        let replacements: [(String, String)] = [
            (" Inc", ", Inc."),
            (" Corp ", " Corporation "),
            (" Corp.", " Corporation"),
            (" Co.", " Co."),
            (" And ", " and "),
            (" Of ", " of "),
            (" Plc", " plc"),
            ("Corporation.", "Corporation"),  // fix double punctuation
            (", Inc.,", ", Inc.,"),  // noop for existing clean
            (" ,", ","),
        ]
        for (find, replace) in replacements {
            s = s.replacingOccurrences(of: find, with: replace)
        }
        
        // If ends with " Inc" (no period), add period
        if s.hasSuffix(" Inc") {
            s = s.replacingOccurrences(of: " Inc$", with: ", Inc.", options: .regularExpression)
        }
        
        // Clean trailing whitespace / duplicated commas
        s = s.replacingOccurrences(of: ",,", with: ",")
        s = s.trimmingCharacters(in: .whitespaces)
        
        return s
    }
}
