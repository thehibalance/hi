# Subsidiary Transparency Rule (STR)

## The Gap

Section 8.4.7 of the whitepaper identifies Supply Chain Laundering: companies moving low-scoring operations into separate legal entities to clean their parent profile. The Contagion Effect Score (CES) detects the gap between a parent's score and its supply chain — but CES is informational only. It never touches the actual HUMAN Grade. A company can show massive downstream displacement in its CES report and still earn Gold HI Grade.

## The Fix

The Subsidiary Transparency Rule adds a scoring adjustment — not a gate — that penalizes parent companies whose known subsidiaries, contractors, or majority-owned entities score significantly lower than the parent. This closes the laundering loophole without adding complexity to the 3-gate system.

## Rule Definition

```
subsidiary_delta = parent_composite - weighted_avg(subsidiary_composites)

IF subsidiary_delta > 20 AND subsidiaries_coverage >= 30%:
    penalty = min(subsidiary_delta × 0.25, 15)
    adjusted_composite = parent_composite - penalty
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Delta threshold** | 20 points | The gap between parent and subsidiary average must exceed this before the penalty activates. Prevents false positives from normal business variation. |
| **Coverage threshold** | 30% | At least 30% of the parent's known subsidiaries/contractors (by revenue or headcount) must be scored for the rule to apply. Below this, STR is reported as "Insufficient Coverage." |
| **Penalty rate** | 0.25 | 25% of the delta above the threshold is applied as a composite penalty. |
| **Maximum penalty** | 15 points | Hard cap. Prevents a single subsidiary relationship from destroying a parent's score. Aligned with the MSSI (Maximum Single-Source Impact) from the Data Integrity Firewall. |

### Subsidiary Identification

Subsidiaries and contractors are identified through:

- **SEC filings:** 10-K Exhibit 21 (list of subsidiaries), proxy statements
- **Corporate structure databases:** SEC EDGAR entity relationships
- **Press releases and news:** Outsourcing announcements, contractor relationships
- **Job postings:** Companies posting jobs under subsidiary names for parent company operations

A "subsidiary" for STR purposes includes: majority-owned subsidiaries (>50% ownership), wholly-owned subsidiaries, primary contractors receiving >15% of the parent's operational spend, and entities created through corporate restructuring within the past 3 years where operations were transferred from the parent.

## Examples

### Example 1: The Laundering Play

**TechCorp (parent):** Composite 72. Employs 5,000 in marketing, sales, strategy.
**TechCorp Services LLC (subsidiary):** Composite 31. Employs 15,000 in customer service, data processing — heavily automated, minimal human involvement.

```
subsidiary_delta = 72 - 31 = 41
penalty = min(41 × 0.25, 15) = 10.25 → 10
adjusted_composite = 72 - 10 = 62
```

TechCorp's published score drops from 72 to 62. They can no longer hide displacement in a subsidiary.

### Example 2: Legitimate Diversification

**ConglomCo (parent):** Composite 68.
**ConglomCo Manufacturing (subsidiary):** Composite 55. Different industry, different workforce.

```
subsidiary_delta = 68 - 55 = 13
13 < 20 (threshold) → NO PENALTY
```

Normal business diversification doesn't trigger the rule.

### Example 3: Ethical Supply Chain

**GoodCorp (parent):** Composite 75.
**GoodCorp Partners (subsidiary):** Composite 71.

```
subsidiary_delta = 75 - 71 = 4
4 < 20 → NO PENALTY
```

Companies with aligned subsidiary scores are unaffected.

## Interaction with Existing Systems

- **CES (Contagion Effect Score):** STR and CES are complementary. CES measures the full supply chain (hundreds of vendors). STR targets majority-owned or primary subsidiaries/contractors only. CES remains informational. STR adjusts the score.
- **3 Gates:** STR adjusts the composite score *before* Gate 1 (Score) is evaluated. A company that would have passed the threshold at 72 but drops to 62 after STR may fail Gate 1. This is by design — you don't earn Gold by hiding your displacement in a subsidiary.
- **Floor Rule:** STR is applied after the floor rule. If the floor rule already caps the score at 40, STR does not reduce it further.
- **Gold HI Grade:** STR makes it harder to earn Gold for companies with laundered structures. That's the point.

## Data Sources

All from existing Priority 1-3 sources:

- **SEC EDGAR Exhibit 21:** Legally required list of subsidiaries for public companies
- **SEC 10-K operational disclosures:** Revenue breakdown by segment
- **Corporate structure databases:** Already ingested by the pipeline
- **Existing scored entities:** If the subsidiary is already in the 815+ company database, the score is available

For subsidiaries not yet scored, STR does not apply (coverage threshold prevents false penalties). As the database grows, coverage naturally improves.

## Why This Matters

Without STR, a company can:
1. Move all customer service to "ServiceBot LLC" (a subsidiary)
2. Automate ServiceBot to 95% AI
3. Keep the parent company's headcount stable (marketing, sales, executives)
4. Score well on H and U because the parent's numbers look human
5. Earn Gold HI Grade while the humans who were displaced are invisible

With STR:
1. ServiceBot LLC gets scored at 31
2. Parent's composite drops by 10 points
3. Parent fails Gate 1 (Score)
4. No Gold until the subsidiary's humans are restored or disclosed

**You can't earn Gold by hiding your displacement in a shell company. The data follows the humans.**

## Implementation Priority

This can be implemented in phases:

**Phase 1 (now):** Add STR logic to the scoring engine. Use SEC Exhibit 21 data for public companies. Flag companies with high deltas in the API response as "STR Adjustment: -X points."

**Phase 2 (Q3 2026):** Expand subsidiary identification to include contractor relationships from job posting analysis and press release NLP.

**Phase 3 (Q4 2026):** Community-submitted subsidiary relationships with verification through the Data Integrity Firewall.

## Whitepaper Language

Add to Part V (Humanwashing) or Part VI (Data Integrity):

> **Subsidiary Transparency Rule.** A company cannot earn a high HI Grade by moving low-scoring operations into subsidiaries or contractors. When a parent company's known subsidiaries score 20+ points below the parent, a penalty of up to 15 points is applied to the parent's composite score before Gold HI Grade gates are evaluated. You can't hide displacement in a shell company. The data follows the humans.

## Seed Data Consideration

For the seed database (206 hand-scored companies), subsidiary relationships should be noted in the `notes` field. Example:

```json
{
  "name": "Meta Platforms",
  "h": 35, "u": 30, "m": 28, "a": 45, "n": 32,
  "notes": "Parent of Instagram, WhatsApp, Reality Labs. Content moderation outsourced to Accenture/Cognizant contractors.",
  "subsidiaries": ["Instagram", "WhatsApp", "Reality Labs"],
  "primary_contractors": ["Accenture (content moderation)", "Cognizant (content moderation)"]
}
```

This data isn't used in scoring yet but establishes the relationship map for when STR activates in the pipeline.
