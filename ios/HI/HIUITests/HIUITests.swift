import XCTest

final class HIUITests: XCTestCase {
    let app = XCUIApplication()
    
    override func setUp() {
        continueAfterFailure = false
        app.launch()
    }
    
    // MARK: - App Launch
    
    func testAppLaunches() {
        XCTAssertTrue(app.staticTexts["HI."].exists)
        XCTAssertTrue(app.staticTexts["Think human intelligence."].exists)
    }
    
    // MARK: - Tab Navigation
    
    func testTabsExist() {
        XCTAssertTrue(app.tabBars.buttons["Search"].exists)
        XCTAssertTrue(app.tabBars.buttons["Watchlist"].exists)
        XCTAssertTrue(app.tabBars.buttons["HUMAN 100"].exists)
        XCTAssertTrue(app.tabBars.buttons["Features"].exists)
        XCTAssertTrue(app.tabBars.buttons["About"].exists)
    }
    
    func testSwitchTabs() {
        app.tabBars.buttons["HUMAN 100"].tap()
        XCTAssertTrue(app.navigationBars["HUMAN 100"].waitForExistence(timeout: 5))
        
        app.tabBars.buttons["Features"].tap()
        XCTAssertTrue(app.navigationBars["Features"].waitForExistence(timeout: 3))
        
        app.tabBars.buttons["About"].tap()
        XCTAssertTrue(app.staticTexts["We're not anti-AI. We're pro-balance."].waitForExistence(timeout: 3))
        
        app.tabBars.buttons["Search"].tap()
        XCTAssertTrue(app.staticTexts["HI."].waitForExistence(timeout: 3))
    }
    
    // MARK: - Search
    
    func testSearchFlow() {
        let searchField = app.textFields["Search any company..."]
        XCTAssertTrue(searchField.waitForExistence(timeout: 5))
        
        searchField.tap()
        searchField.typeText("Apple")
        
        // Wait for results
        let firstResult = app.staticTexts["Apple Inc."]
        if firstResult.waitForExistence(timeout: 5) {
            firstResult.tap()
            // Should navigate to detail
            XCTAssertTrue(app.staticTexts["HI Grade™"].waitForExistence(timeout: 5))
            XCTAssertTrue(app.staticTexts["HUMAN Dimensions"].waitForExistence(timeout: 5))
        }
    }
    
    func testSearchClear() {
        let searchField = app.textFields["Search any company..."]
        searchField.tap()
        searchField.typeText("test")
        
        // Tap clear button
        let clearButton = app.buttons["xmark.circle.fill"]
        if clearButton.exists {
            clearButton.tap()
            XCTAssertEqual(searchField.value as? String ?? "", "")
        }
    }
    
    // MARK: - Watchlist
    
    func testEmptyWatchlist() {
        app.tabBars.buttons["Watchlist"].tap()
        // Should show empty state or have content
        XCTAssertTrue(app.navigationBars["Watchlist"].waitForExistence(timeout: 3))
    }
    
    // MARK: - Features
    
    func testFeaturesNavigation() {
        app.tabBars.buttons["Features"].tap()
        
        XCTAssertTrue(app.staticTexts["HUMAN Shield"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.staticTexts["HUMAN Lens"].exists)
        XCTAssertTrue(app.staticTexts["Heartbeat"].exists)
        XCTAssertTrue(app.staticTexts["Contagion"].exists)
        XCTAssertTrue(app.staticTexts["Industry Benchmarks"].exists)
        
        // Tap into Shield
        app.staticTexts["HUMAN Shield"].tap()
        XCTAssertTrue(app.navigationBars["HUMAN Shield"].waitForExistence(timeout: 5))
    }
    
    // MARK: - About
    
    func testAboutContent() {
        app.tabBars.buttons["About"].tap()
        
        XCTAssertTrue(app.staticTexts["HI."].waitForExistence(timeout: 3))
        XCTAssertTrue(app.staticTexts["Think human intelligence."].exists)
        XCTAssertTrue(app.staticTexts["The HUMAN Framework"].exists)
        XCTAssertTrue(app.staticTexts["How Scoring Works"].exists)
    }
    
    // MARK: - Company Detail
    
    func testDetailShowsGates() {
        let searchField = app.textFields["Search any company..."]
        searchField.tap()
        searchField.typeText("Costco")
        
        let result = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Costco'")).firstMatch
        if result.waitForExistence(timeout: 5) {
            result.tap()
            XCTAssertTrue(app.staticTexts["10 Gates to Gold"].waitForExistence(timeout: 5))
            XCTAssertTrue(app.staticTexts["HUMAN Dimensions"].exists)
        }
    }
    
    // MARK: - Favorite Toggle
    
    func testFavoriteToggle() {
        // Search and open a company
        let searchField = app.textFields["Search any company..."]
        searchField.tap()
        searchField.typeText("Microsoft")
        
        let result = app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Microsoft'")).firstMatch
        if result.waitForExistence(timeout: 5) {
            result.tap()
            
            // Tap star button
            let star = app.buttons["star"]
            let starFill = app.buttons["star.fill"]
            
            if star.waitForExistence(timeout: 3) {
                star.tap()
                XCTAssertTrue(starFill.waitForExistence(timeout: 2))
                
                // Unfavorite
                starFill.tap()
                XCTAssertTrue(star.waitForExistence(timeout: 2))
            }
        }
    }
}
