import XCTest
@testable import HI

final class HITests: XCTestCase {
    
    // MARK: - Model Decoding
    
    func testCompanyDecoding() throws {
        let json = """
        {
            "company": "Apple Inc.",
            "ticker": "AAPL",
            "composite": 72.5,
            "industry": "Technology",
            "hi_balanced": true,
            "D_H": 68, "D_U": 75, "D_M": 80, "D_A": 65, "D_N": 74,
            "decay_index": 5.2,
            "decay_level": "stable"
        }
        """.data(using: .utf8)!
        
        let company = try JSONDecoder().decode(Company.self, from: json)
        
        XCTAssertEqual(company.company, "Apple Inc.")
        XCTAssertEqual(company.ticker, "AAPL")
        XCTAssertEqual(company.composite, 72.5)
        XCTAssertEqual(company.hi_balanced, true)
        XCTAssertEqual(company.D_H, 68)
        XCTAssertEqual(company.D_U, 75)
        XCTAssertEqual(company.D_M, 80)
        XCTAssertEqual(company.D_A, 65)
        XCTAssertEqual(company.D_N, 74)
        XCTAssertEqual(company.decay_level, "stable")
    }
    
    func testCompanyPartialDecoding() throws {
        let json = """
        { "company": "Test Corp", "composite": 55 }
        """.data(using: .utf8)!
        
        let company = try JSONDecoder().decode(Company.self, from: json)
        XCTAssertEqual(company.company, "Test Corp")
        XCTAssertNil(company.ticker)
        XCTAssertNil(company.hi_balanced)
        XCTAssertNil(company.D_H)
    }
    
    func testSearchResponseDecoding() throws {
        let json = """
        { "results": [{"company": "Apple", "ticker": "AAPL", "composite": 72}], "count": 1 }
        """.data(using: .utf8)!
        
        let response = try JSONDecoder().decode(SearchResponse.self, from: json)
        XCTAssertEqual(response.results?.count, 1)
        XCTAssertEqual(response.results?.first?.company, "Apple")
    }
    
    func testAlgoHarmDecoding() throws {
        let json = """
        {
            "has_harm": true,
            "algo_harm_score": 35,
            "flags": ["Addictive patterns", "Division signals"],
            "penalties": {"H": -5, "U": -3, "M": -2, "N": -4}
        }
        """.data(using: .utf8)!
        
        let harm = try JSONDecoder().decode(AlgoHarm.self, from: json)
        XCTAssertEqual(harm.has_harm, true)
        XCTAssertEqual(harm.algo_harm_score, 35)
        XCTAssertEqual(harm.flags?.count, 2)
        XCTAssertEqual(harm.penalties?["H"], -5)
    }
    
    func testMoatResponseDecoding() throws {
        let json = """
        {
            "results": [{"company": "Costco", "ticker": "COST", "moat_score": 85, "moat_level": "fortress"}],
            "metadata": {"distribution": {"fortress": 18, "strong": 182}},
            "total": 200
        }
        """.data(using: .utf8)!
        
        let response = try JSONDecoder().decode(MoatResponse.self, from: json)
        XCTAssertEqual(response.results?.first?.moat_level, "fortress")
        XCTAssertEqual(response.metadata?.distribution?["fortress"], 18)
    }
    
    // MARK: - Theme
    
    func testScoreColors() {
        XCTAssertEqual(APIService.scoreColor(80), "green")
        XCTAssertEqual(APIService.scoreColor(50), "orange")
        XCTAssertEqual(APIService.scoreColor(30), "red")
        XCTAssertEqual(APIService.scoreColor(70), "green")
        XCTAssertEqual(APIService.scoreColor(42), "orange")
        XCTAssertEqual(APIService.scoreColor(41), "red")
    }
    
    // MARK: - Cache
    
    func testCacheSaveLoad() {
        let cache = CacheManager.shared
        let company = "TestCompany_\(UUID().uuidString)"
        
        cache.save(company, key: "test_save")
        let loaded: String? = cache.load(String.self, key: "test_save")
        
        XCTAssertEqual(loaded, company)
        cache.clear(key: "test_save")
    }
    
    func testCacheMiss() {
        let cache = CacheManager.shared
        let loaded: String? = cache.load(String.self, key: "nonexistent_key_\(UUID())")
        XCTAssertNil(loaded)
    }
    
    func testCacheFreshness() {
        let cache = CacheManager.shared
        cache.save("test", key: "fresh_test")
        XCTAssertTrue(cache.isFresh(key: "fresh_test"))
        XCTAssertFalse(cache.isFresh(key: "not_cached"))
        cache.clear(key: "fresh_test")
    }
    
    func testCacheClearAll() {
        let cache = CacheManager.shared
        cache.save("a", key: "clear_a")
        cache.save("b", key: "clear_b")
        cache.clearAll()
        XCTAssertNil(cache.load(String.self, key: "clear_a") as String?)
        XCTAssertNil(cache.load(String.self, key: "clear_b") as String?)
    }
    
    // MARK: - Favorites
    
    func testFavoritesToggle() {
        let fm = FavoritesManager.shared
        let initial = fm.favorites.count
        
        let testCompany = Company(
            company: "TestFav_\(UUID().uuidString)", ticker: "TSTF", composite: 60,
            industry: nil, sic_description: nil, hi_balanced: false, hi_grade: nil,
            D_H: nil, D_U: nil, D_M: nil, D_A: nil, D_N: nil,
            decay_index: nil, decay_level: nil, shield_score: nil, shield_tier: nil,
            genome: nil, algo_harm: nil, humanwashing_flags: nil, domains: nil
        )
        
        // Add
        fm.toggle(testCompany)
        XCTAssertTrue(fm.isFavorite("TSTF"))
        XCTAssertEqual(fm.favorites.count, initial + 1)
        
        // Remove
        fm.toggle(testCompany)
        XCTAssertFalse(fm.isFavorite("TSTF"))
        XCTAssertEqual(fm.favorites.count, initial)
    }
    
    func testRecents() {
        let fm = FavoritesManager.shared
        
        let testCompany = Company(
            company: "RecentTest", ticker: "RECT", composite: 55,
            industry: nil, sic_description: nil, hi_balanced: false, hi_grade: nil,
            D_H: nil, D_U: nil, D_M: nil, D_A: nil, D_N: nil,
            decay_index: nil, decay_level: nil, shield_score: nil, shield_tier: nil,
            genome: nil, algo_harm: nil, humanwashing_flags: nil, domains: nil
        )
        
        fm.addRecent(testCompany)
        XCTAssertTrue(fm.recents.contains { $0.ticker == "RECT" })
        
        // Adding again moves to front, no duplicates
        fm.addRecent(testCompany)
        let count = fm.recents.filter { $0.ticker == "RECT" }.count
        XCTAssertEqual(count, 1)
        
        fm.clearRecents()
    }
    
    // MARK: - API Integration (live)
    
    func testLiveStats() async {
        let api = APIService.shared
        await api.loadStats()
        XCTAssertNotNil(api.stats)
        XCTAssertGreaterThan(api.stats?.total_companies ?? 0, 0)
    }
    
    func testLiveSearch() async {
        let results = await APIService.shared.search("apple")
        XCTAssertGreaterThan(results.count, 0)
        XCTAssertTrue(results.contains { $0.company?.lowercased().contains("apple") == true })
    }
    
    func testLiveScoreTicker() async {
        let company = await APIService.shared.score(ticker: "AAPL")
        XCTAssertNotNil(company)
        XCTAssertEqual(company?.ticker, "AAPL")
        XCTAssertNotNil(company?.composite)
    }
    
    func testLiveHuman100() async {
        let entries = await APIService.shared.human100()
        XCTAssertGreaterThan(entries.count, 0)
    }
}
