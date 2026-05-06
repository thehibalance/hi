
## v1.2.1 — HOW IT COMPARES in extension panel

Add 'vs {industry} median' and 'vs S&P 500 average' to extension panel.
Mirrors web detail page (docs/index.html line 1324-1336).

Implementation choice: probably (a) add industry_median + sp500_average
fields to API response so extension doesn't need to compute. Single
backend change, both web and extension read same field.

Estimate: 2-3 hours (backend field + extension rendering + verification)
Defer to v1.2.1 (week of May 12, post-launch).


## v1.2.1 — HOW IT COMPARES in extension panel
Add 'vs {industry} median' and 'vs S&P 500 average' to extension panel.
Probably needs API fields: industry_median, sp500_average.

## v1.2.1 — H dimension industry-default fallback widespread
~30-40% of S&P 500 companies have H sub-signals from industry medians, not 
per-company SEC data. Pattern: when SEC RPE data is missing, fallback to 
INDUSTRY_RPE_MEDIANS dict. Effects: identical H scores within an industry 
(KO=SBUX=80/65/55/80 because both consumer goods).

Already disclosed at /methodology page (line 935 deep-dive card).

Fix path: integrate FMP/Yahoo as fallback SEC sources for revenue + headcount,
push per-company coverage above ~75% before next H ladder revision.

Not a launch blocker — disclosed limitation, not a bug.

## v1.2.1 — H dimension industry-default fallback widespread
~30-40% of S&P 500 companies have H sub-signals from industry medians, not 
per-company SEC data. Pattern: when SEC RPE data is missing, fallback to 
INDUSTRY_RPE_MEDIANS dict. Effects: identical H scores within an industry 
(KO=SBUX=80/65/55/80 because both consumer goods).

Already disclosed at /methodology page (line 935 deep-dive card).

Fix path: integrate FMP/Yahoo as fallback SEC sources for revenue + headcount,
push per-company coverage above ~75% before next H ladder revision.

Not a launch blocker — disclosed limitation, not a bug.

## v1.2.1 — Heartbeat decay factor calibration
Audit #5 found decay system is structurally sound (117 alerts, all multi-factor,
zero empty/single-factor decays). However:
- "Aggressive AI pivot (N articles)" appears in ~95% of alerts — non-differentiating in 2026
- "High 8-K activity (20 filings)" similarly universal
- Real differentiation comes from layoff counts and ethics/legal counts
EFX (Equifax) example: critical=65 is well-justified by 8 ethics articles + 2 HW
flags + 4 scrutiny articles. The signal works when ethics issues are present.

For v1.2.1: rebalance decay_index weights to lean more on ethics/legal/layoff
signals over AI-pivot/8K-activity. Consider per-industry baselines for what
counts as "aggressive AI pivot" — a payroll processor with 11 AI articles is
different from a Big Tech company with the same.

## v1.2.1 — Heartbeat decay factor calibration
Audit #5 found decay system is structurally sound (117 alerts, all multi-factor,
zero empty/single-factor decays). However:
- "Aggressive AI pivot (N articles)" appears in ~95% of alerts — non-differentiating in 2026
- "High 8-K activity (20 filings)" similarly universal
- Real differentiation comes from layoff counts and ethics/legal counts
EFX (Equifax) example: critical=65 is well-justified by 8 ethics articles + 2 HW
flags + 4 scrutiny articles. The signal works when ethics issues are present.

For v1.2.1: rebalance decay_index weights to lean more on ethics/legal/layoff
signals over AI-pivot/8K-activity. Consider per-industry baselines for what
counts as "aggressive AI pivot" — a payroll processor with 11 AI articles is
different from a Big Tech company with the same.
