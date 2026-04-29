
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
