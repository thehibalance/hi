import Foundation

/// Maps iOS app bundle identifiers to company tickers.
/// This is the core of the phone extension — when a user opens an app,
/// Shortcuts passes the bundle ID, and we resolve it to a HI Grade.
struct BundleMapping {
    
    /// Bundle ID → Ticker mapping for S&P 500 + major consumer apps
    static let bundleToTicker: [String: String] = [
        // Big Tech
        "com.apple.mobilesafari": "AAPL",
        "com.apple.AppStore": "AAPL",
        "com.google.chrome.ios": "GOOGL",
        "com.google.Maps": "GOOGL",
        "com.google.Gmail": "GOOGL",
        "com.google.YouTube": "GOOGL",
        "com.google.photos": "GOOGL",
        "com.microsoft.Office.Outlook": "MSFT",
        "com.microsoft.teams": "MSFT",
        "com.microsoft.Office.Word": "MSFT",
        "com.microsoft.Office.Excel": "MSFT",
        "com.microsoft.skype.skype": "MSFT",
        "com.linkedin.LinkedIn": "MSFT",
        
        // Social Media
        "com.facebook.Facebook": "META",
        "com.burbn.instagram": "META",
        "com.facebook.Messenger": "META",
        "com.atebits.Tweetie2": "X",
        "com.zhiliaoapp.musically": "BDNCE",  // TikTok / ByteDance
        "com.toyopagroup.picaboo": "SNAP",
        "com.pinterest": "PINS",
        "com.reddit.Reddit": "RDDT",
        
        // Streaming
        "com.netflix.Netflix": "NFLX",
        "com.spotify.client": "SPOT",
        "com.disney.disneyplus": "DIS",
        "com.hbo.hbonow": "WBD",
        "com.amazon.aiv": "AMZN",
        "com.apple.tv": "AAPL",
        "com.peacocktv.peacock": "CMCSA",
        "com.paramount.paramountplus": "PARA",
        
        // E-Commerce
        "com.amazon.Amazon": "AMZN",
        "com.walmart.electronics.Walmart": "WMT",
        "com.target.TargetApp": "TGT",
        "com.costco.app.native": "COST",
        "com.ebay.iphone": "EBAY",
        "com.etsy.etsy": "ETSY",
        "com.shopify.ShopifyInternalApp": "SHOP",
        
        // Ride-hailing / Delivery
        "com.ubercab.UberClient": "UBER",
        "com.ubercab.UberEats": "UBER",
        "com.lyft.ios": "LYFT",
        "com.grubhub.grubhub": "JTKWY",
        "com.dd.doordash": "DASH",
        "com.instacart.client": "CART",
        
        // Finance / Banking
        "com.jpmorgan.chase": "JPM",
        "com.bankofamerica.BofA": "BAC",
        "com.wf.wellsfargo": "WFC",
        "com.citi.citimobile": "C",
        "com.americanexpress.amex": "AXP",
        "com.capitalone.enterprisemobilebanking": "COF",
        "com.discover.mobile": "DFS",
        "com.paypal.PPClient": "PYPL",
        "com.venmo.Venmo": "PYPL",
        "com.squareup.cashapp": "SQ",
        "com.robinhood.release": "HOOD",
        "com.coinbase.ios": "COIN",
        "com.sofi.mobile": "SOFI",
        
        // Payments
        "com.apple.Passbook": "AAPL",
        "com.visa.VDP-Offers": "V",
        "com.mastercard.mp.maapp": "MA",
        
        // Food & Beverage
        "com.starbucks.mystarbucks": "SBUX",
        "com.McDonalds.mobileapp": "MCD",
        "com.chipotle.ChipotleApp": "CMG",
        "com.dominos.DominosApp": "DPZ",
        "com.subway.SubwayApp": "SBWY",
        "com.dunkinbrands.DunkinApp": "DNKN",
        "com.pepsico.PepsiPass": "PEP",
        "com.coca-cola.CocaCola": "KO",
        
        // Travel
        "com.airbnb.app": "ABNB",
        "com.booking.BookingApp": "BKNG",
        "com.expedia.app": "EXPE",
        "com.tripadvisor.TripAdvisorMobileApp": "TRIP",
        "com.united.UnitedCustomerFacing": "UAL",
        "com.delta.Delta": "DAL",
        "com.southwest.Southwest": "LUV",
        "com.aa.AmericanAirlines": "AAL",
        "com.marriott.ipp.mrt": "MAR",
        "com.hilton.hhonors": "HLT",
        
        // Health / Fitness
        "com.peloton.atlas": "PTON",
        "com.nike.nikeapp": "NKE",
        "com.underarmour.myfitnesspal": "UA",
        "com.CVS.cvspharmacy": "CVS",
        "com.walgreens.Walgreens": "WBA",
        "com.uhg.optumrx": "UNH",
        
        // Telecom
        "com.att.myatt": "T",
        "com.vzw.hss.myverizon": "VZ",
        "com.tmobile.TMobilePlan": "TMUS",
        "com.comcast.xfinity": "CMCSA",
        
        // Auto
        "com.tesla.TeslaApp": "TSLA",
        "com.ford.fordpass": "F",
        "com.gm.myChevrolet": "GM",
        
        // Gaming
        "com.activision.callofduty": "MSFT",
        "com.roblox.robloxmobile": "RBLX",
        "com.supercell.laser": "TCEHY",
        
        // Productivity / Cloud
        "com.salesforce.chatter": "CRM",
        "com.tinyspeck.chatlyio": "CRM",  // Slack
        "com.getdropbox.Dropbox": "DBX",
        "com.adobe.Adobe-Reader": "ADBE",
        "com.intuit.turbotax": "INTU",
        "com.intuit.quickbooks": "INTU",
        "com.zoom.us.zVideo": "ZM",
        
        // Home / Retail
        "com.homedepot.HomeDepot": "HD",
        "com.lowes.consumer": "LOW",
        "com.ikea.kompis": "IKEA",
        
        // News / Info
        "com.nytimes.NYTimes": "NYT",
        "com.washingtonpost.rainbow": "AMZN",
        
        // Crypto / Fintech
        "com.binance.dev": "BNB",
        "com.blockfi.mobile": "BLKFI",
    ]
    
    /// Reverse lookup: ticker → list of bundle IDs
    static let tickerToBundles: [String: [String]] = {
        var map: [String: [String]] = [:]
        for (bundle, ticker) in bundleToTicker {
            map[ticker, default: []].append(bundle)
        }
        return map
    }()
    
    /// Common app display names for Siri/Shortcuts
    static let bundleToAppName: [String: String] = [
        "com.ubercab.UberClient": "Uber",
        "com.starbucks.mystarbucks": "Starbucks",
        "com.amazon.Amazon": "Amazon",
        "com.netflix.Netflix": "Netflix",
        "com.burbn.instagram": "Instagram",
        "com.facebook.Facebook": "Facebook",
        "com.google.YouTube": "YouTube",
        "com.tesla.TeslaApp": "Tesla",
        "com.airbnb.app": "Airbnb",
        "com.McDonalds.mobileapp": "McDonald's",
        "com.dd.doordash": "DoorDash",
        "com.lyft.ios": "Lyft",
        "com.nike.nikeapp": "Nike",
        "com.walmart.electronics.Walmart": "Walmart",
        "com.apple.mobilesafari": "Safari (Apple)",
        "com.paypal.PPClient": "PayPal",
        "com.robinhood.release": "Robinhood",
        "com.zoom.us.zVideo": "Zoom",
        "com.tinyspeck.chatlyio": "Slack",
    ]
    
    /// Resolve a bundle ID to a ticker
    static func ticker(for bundleID: String) -> String? {
        bundleToTicker[bundleID]
    }
    
    /// Resolve a bundle ID to a company name (for display)
    static func appName(for bundleID: String) -> String? {
        bundleToAppName[bundleID]
    }
    
    /// Get all known bundle IDs (for Shortcuts automation setup)
    static var allBundleIDs: [String] {
        Array(bundleToTicker.keys).sorted()
    }
    
    /// Get all unique tickers we can resolve
    static var allTickers: [String] {
        Array(Set(bundleToTicker.values)).sorted()
    }
}
