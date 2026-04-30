
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
