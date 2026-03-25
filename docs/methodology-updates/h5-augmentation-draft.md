# H.5 — AI Displacement & Augmentation Trajectory

**Signal ID:** H.5
**Weight:** 0.20 (unchanged)
**Dimension:** H — Human Consciousness

## Definition

H.5 measures the direction of the relationship between AI adoption and human workforce — not just whether AI is replacing humans, but whether AI is being deployed to *empower* them. It is a bidirectional signal: companies that displace humans are penalized, and companies that demonstrably augment their workforce with AI are rewarded.

## Two Components

### Component A: Displacement Signal (Penalty)

Unchanged from current specification.

```
headcount_delta = (headcount_current - headcount_prior) / headcount_prior
ai_invest_delta = (ai_capex_current - ai_capex_prior) / ai_capex_prior
displacement_signal = ai_invest_delta - headcount_delta
```

A positive displacement_signal indicates AI investment is growing faster than headcount (replacement). A zero or negative displacement_signal indicates balanced or human-favoring growth.

### Component B: Augmentation Signal (Bonus)

The augmentation signal rewards companies that invest in human-AI collaboration rather than substitution. It is computed from up to four measurable indicators:

| Indicator | Source | What It Measures |
|-----------|--------|-----------------|
| **AI Training Investment** | SEC 10-K (workforce development disclosures), press releases, job postings mentioning "AI training," "upskilling," "reskilling" | Proportion of AI budget allocated to training existing employees to work *with* AI tools, not being replaced by them |
| **Copilot Deployment Ratio** | Job postings, product disclosures, operational filings | Ratio of AI tools deployed as human-assistive (copilots, decision support, augmentation) vs. autonomous (full replacement, lights-out automation) |
| **No-Displacement Commitment** | Public commitments, SEC filings, press releases | Binary: has the company made a public, verifiable commitment that AI adoption will not result in net workforce reduction? (100 if yes with evidence, 50 if stated but unverified, 0 if absent) |
| **Redeployment Rate** | SEC 10-K, WARN Act cross-reference, press releases | When AI automates a function, what proportion of affected workers are redeployed to new roles within the organization vs. terminated? |

```
augmentation_signal = (
    0.30 × ai_training_investment_score +
    0.30 × copilot_deployment_ratio +
    0.20 × no_displacement_commitment +
    0.20 × redeployment_rate
)
```

Each indicator is scored 0–100 and normalized per GICS Sub-Industry.

When augmentation data is unavailable, the augmentation_signal defaults to 0 (neutral — no bonus, no penalty). This ensures backward compatibility: companies without augmentation data score identically to how they score today.

## Combined H.5 Formula

```
base_score = clamp(100 - (displacement_signal × 100), 0, 100)
augmentation_bonus = augmentation_signal × 0.20
S_H5 = clamp(base_score + augmentation_bonus, 0, 100)
```

The augmentation bonus is capped at +20 points on top of the base displacement score. This means:

- A company with zero displacement and strong augmentation can score up to **100** on H.5
- A company with moderate displacement but strong augmentation programs can partially offset the penalty (e.g., base 50 + bonus 15 = **65**)
- A company with heavy displacement and no augmentation scores as low as **0** (unchanged from current behavior)
- A company with no data on either defaults to **50** (industry median, unchanged)

## Examples

**Example 1: Augmentation leader**
- Headcount grew 5%, AI investment grew 30%
- displacement_signal = 0.30 - 0.05 = 0.25 → base_score = 75
- Company has $50M AI training program, copilot-first deployment policy, public no-layoff pledge, 90% redeployment rate
- augmentation_signal = 85 → bonus = 85 × 0.20 = 17
- **S_H5 = 92** (rewarded for investing in humans alongside AI)

**Example 2: Silent automator**
- Headcount dropped 15%, AI investment grew 40%
- displacement_signal = 0.40 - (-0.15) = 0.55 → base_score = 45
- No training programs, no redeployment, no public commitments
- augmentation_signal = 0 → bonus = 0
- **S_H5 = 45** (penalized for displacement, no offset)

**Example 3: Balanced adopter**
- Headcount flat, AI investment grew 20%
- displacement_signal = 0.20 → base_score = 80
- Moderate training investment, some copilot tools, no formal commitment
- augmentation_signal = 45 → bonus = 45 × 0.20 = 9
- **S_H5 = 89** (slightly rewarded for effort)

## Data Sources

All augmentation indicators use existing public data source categories from the Source Hierarchy (Section 11.1):

- **Priority 2:** SEC 10-K workforce development disclosures (newly required under SEC human capital rules)
- **Priority 3:** Published training program documentation, third-party verified workforce reports
- **Priority 4:** Company press releases, career pages, sustainability reports
- **Priority 5:** Job posting analysis (AI training keywords vs. AI replacement keywords), workforce analytics APIs

No new data source categories are required. The AI Enhancement Layer (when enabled) can use NLP on SEC filings and earnings calls to extract augmentation signals with higher precision.

## Why This Matters

The current H.5 creates an implicit message: *AI adoption lowers your score.* That's not the HI. movement's position. The position is: *AI that replaces humans without transparency or investment in those humans lowers your score. AI that empowers humans raises it.*

The Augmentation Bonus makes the framework's values explicit:
- **We're not anti-AI.** We reward companies that use AI to make their people better.
- **We're pro-balance.** Displacement without augmentation is the problem, not AI itself.
- **We're pro-transparency.** Companies that publicly commit to human-AI collaboration and follow through earn measurable credit.

This aligns the scoring with the movement: **Think human intelligence** means valuing both the human *and* the intelligence — together.

## Whitepaper Language (Seventh Edition)

For the whitepaper's H dimension section (Part III, Section 3.1), replace the H.5 bullet:

**Current:**
> • H.5 Innovation Stewardship — Patent analysis for human-augmenting vs. human-replacing technology

**Proposed:**
> • H.5 AI Displacement & Augmentation — Measures the direction of AI adoption. Penalizes companies replacing humans without investment. Rewards companies that retrain, redeploy, and deploy AI as copilots rather than replacements. Includes AI training investment, copilot deployment ratio, no-displacement commitments, and redeployment rate. We're not anti-AI — we reward companies that use AI to empower their people.

## Impact on Existing Scores

- **No company's score decreases.** The augmentation bonus is additive only. Companies without augmentation data score identically to today (augmentation_signal defaults to 0).
- **Some companies may increase by up to 4 points on composite.** The maximum H.5 bonus is +20 points, and H.5 carries a 0.20 weight within H, which carries a 0.20 weight in the composite. Maximum composite impact: 20 × 0.20 × 0.20 = 0.8 points. In practice, companies with strong augmentation programs might see H dimension increases of 2-4 points and composite increases of 0.4-0.8 points.
- **Gold HI Grade eligibility is unaffected.** The threshold is adaptive and will absorb any upward drift naturally.
