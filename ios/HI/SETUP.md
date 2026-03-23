# HI. — iOS App + Safari Extension Setup

## Quick Start (15 minutes)

### Step 1: Create Xcode Project

1. Open Xcode → File → New → Project
2. Choose **App** → Next
3. Product Name: `HI`
4. Team: Your Apple Developer account
5. Organization Identifier: `com.morfinnovations`
6. Interface: **SwiftUI**
7. Language: **Swift**
8. ✅ Check "Include Tests" (optional)
9. Save to `~/Desktop/repo/ios/`

### Step 2: Add Source Files

Drag these folders from `ios/HI/HI/` into the Xcode project navigator:
- `Models/` (Models.swift)
- `Services/` (APIService.swift)
- `Views/` (HomeView.swift, CompanyDetailView.swift, Human100View.swift, FeaturesView.swift, AboutView.swift)
- `Theme.swift`
- `ContentView.swift`

**Delete** the auto-generated `ContentView.swift` that Xcode created — we have our own.

**Replace** the auto-generated app entry point with our `HIApp.swift`.

### Step 3: Add Safari Extension Target

1. File → New → Target
2. Choose **Safari Web Extension**
3. Product Name: `HI Safari`
4. Language: Swift
5. This creates a `HI Safari` folder with boilerplate

6. **Replace** the boilerplate `Resources/` contents with files from `ios/HI/Safari/Resources/`:
   - Copy `manifest.json` → `HI Safari/Resources/manifest.json`
   
7. **Copy Chrome extension files** into `HI Safari/Resources/`:
   ```
   cp ~/Desktop/repo/human-edge/content.js "HI Safari/Resources/"
   cp ~/Desktop/repo/human-edge/content.css "HI Safari/Resources/"
   cp ~/Desktop/repo/human-edge/background.js "HI Safari/Resources/"
   cp -r ~/Desktop/repo/human-edge/lib "HI Safari/Resources/"
   ```

### Step 4: App Icon

1. In Xcode, click Assets.xcassets → AppIcon
2. Drag your 1024x1024 logo into the "All Sizes" slot
3. Xcode auto-generates all required sizes

### Step 5: Configure Signing

1. Click the `HI` target → Signing & Capabilities
2. Team: Your Apple Developer team
3. Bundle Identifier: `com.morfinnovations.hi`
4. Repeat for `HI Safari` target: `com.morfinnovations.hi.safari`

### Step 6: Build & Run

1. Select your iPhone or Simulator
2. ⌘R to build and run
3. The app connects to `api.thehibalance.org` — no local server needed

### Step 7: Enable Safari Extension

1. Open Safari on iPhone/Mac
2. Settings → Extensions → HI Safari → Enable
3. Grant "Allow on All Websites"

---

## Project Structure

```
ios/HI/
├── HI/
│   ├── HIApp.swift              # App entry point
│   ├── ContentView.swift         # Tab navigation
│   ├── Theme.swift              # Colors, fonts (navy, gold, etc.)
│   ├── Models/
│   │   └── Models.swift         # All API response models
│   ├── Services/
│   │   └── APIService.swift     # API client (all 32 endpoints)
│   └── Views/
│       ├── HomeView.swift       # Search + Gold ticker + Quick links
│       ├── CompanyDetailView.swift  # Full company profile + 10 gates
│       ├── Human100View.swift   # HUMAN 100 Index
│       ├── FeaturesView.swift   # Shield, Lens, Heartbeat, Contagion, Industry
│       └── AboutView.swift      # Manifesto + framework + stats
├── Safari/
│   └── Resources/
│       └── manifest.json        # Safari Web Extension manifest
└── SETUP.md                     # This file
```

## Features

### iOS App
- Search 815+ companies
- Full HUMAN dimension breakdown
- 10 Gates to Gold
- HUMAN Genome visualization
- Algorithmic Harm Index
- Humanwashing detection
- Gold HI Grade ticker
- HUMAN 100 Index
- HUMAN Shield (moat depth)
- HUMAN Lens (ESG vs HI gaps)
- Heartbeat decay monitoring
- Contagion tracking
- Industry benchmarks

### Safari Extension
- Same human silhouette pill as Chrome
- Floating badge on every website
- Click to expand full score panel
- Gold companies get gold silhouette
- Works on iOS Safari + macOS Safari

## API

All data comes from: `https://api.thehibalance.org/api/v1/`

No API key needed. No authentication. Free.

## TestFlight

1. In Xcode: Product → Archive
2. Distribute → App Store Connect
3. Go to appstoreconnect.apple.com → TestFlight
4. Add testers → Start beta testing

## App Store Submission

1. Archive + Upload to App Store Connect
2. Fill in app metadata:
   - Name: HI. — Human Intelligence Grade
   - Subtitle: Think human intelligence.
   - Category: Business / Reference
   - Description: See how human any company is. 815+ brands scored on the things AI can't replace.
   - Keywords: ethics, ESG, AI, human, corporate, scoring, sustainability, transparency
3. Add screenshots (iPhone 15 Pro, iPad)
4. Submit for review (typically 24-48 hours)

---

*HI. — Think human intelligence.*
*thehibalance.org · @thehibalance · Morf Innovations LLC*
