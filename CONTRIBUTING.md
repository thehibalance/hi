# Contributing to HI Grade™

Thanks for showing up. HI Grade gets better when people challenge it.

## The three kinds of contribution we specifically need

### 1. Score challenges

You think company X should score higher or lower than it does. This is the most valuable kind of contribution.

**How to file:** Open a [new issue](https://github.com/thehibalance/hi/issues/new) with the **"score-challenge"** label. Include:

- Company name + ticker
- Current composite + dimension scores (from the API or extension)
- What you think is wrong and why
- Specific data sources or evidence (news articles, SEC filings, court records)
- What direction the score should move (up / down / much more / much less)

**What we'll do:** investigate within 5 business days. If your challenge is backed by evidence we can trace, we adjust the score or (if the issue is methodology-level) add to the known-gaps backlog. Either way, we respond publicly on the issue.

**What we won't do:** adjust a score because a company asks us to. HI Grade is estimated from public data; if the data supports the score, the score stays.

### 2. Data source additions

Proposing a new free, public, auditable data source. Bonus points if it's from a government agency or academic institution.

**Criteria for a valid source:**

- **Free** — no paywall, no tier-gated access
- **Public** — anyone can verify the data themselves
- **Auditable** — traceable to a stable URL or filing number
- **Stable** — published on a predictable schedule (annual, quarterly, continuous)
- **Non-AI** — not LLM-generated, not synthesized, not "AI-powered insights"

**How to contribute:** open a PR that adds a new pipeline file to `pipeline/` following the pattern of existing files (e.g., `cfpb_pipeline.py`). Include:

- Docstring explaining the data source
- Citation for the source's published methodology
- Mapping to which sub-signal(s) it informs
- Sample output format

Ping us in the PR with the proposed dimension impact.

### 3. Ladder grounding

Many sub-signal scoring ladders in HI v1.1.0 are **editorial** — the data is authoritative but the tier cutoffs were chosen by the engine authors. We've flagged all of them in [`RUBRIC.md`](RUBRIC.md) as PARTIAL or UNGROUNDED.

If you have an academic paper, regulatory framework, or published industry standard that would ground one of our editorial ladders, **that is the single most valuable contribution you can make**.

**Example:** our CFPB sub-signal currently uses editorial tier cutoffs (<100 complaints/$B = 85, <500 = 70, <2000 = 55). If you know of published CFPB methodology or an academic framework that assigns specific thresholds to complaint volumes, drop us a pointer.

## Less-glamorous but still useful

### Company additions

If a major public company isn't in our universe, open an issue with:
- Company name
- Ticker (or "private — no ticker")
- Industry / GICS sub-industry
- Why it should be tracked (revenue > $500M, broad consumer impact, notable harm, etc.)

We add companies in batches during quarterly refreshes.

### Bug reports

Pipeline errors, API errors, extension glitches, iOS crashes — issue with:
- What you were doing
- What happened
- What you expected
- Browser/OS/version
- Full console output if applicable

### Documentation improvements

README typos, methodology clarifications, examples that could be better — PR welcome. No need to file an issue first for small docs fixes.

## What we're NOT looking for

- Pull requests that add AI to the scoring engine (this is non-negotiable)
- Pull requests that add paid data sources
- "Why is my company scored poorly?" complaints from the company being scored (see **Score challenges** above — bring evidence)
- Integrations with LLM APIs in the scoring path (explanations yes, scoring no)
- Feature additions without an issue first

## Development setup

```bash
git clone https://github.com/thehibalance/hi.git
cd hi/pipeline
pip install -r requirements.txt

# Run full pipeline (nightly equivalent — takes ~60-90min)
python3 run_all.py

# Faster: skip data collection, re-score from cached data (~5min)
python3 run_all.py --skip-collect

# Even faster: just regenerate features from scores (~1min)
python3 run_all.py --features-only

# Start API locally
python3 api_server.py --port 8080
```

## Code style

- Python: we follow PEP 8 loosely, no formatter required. Readability > strict style.
- JavaScript: the extension uses vanilla ES6+ (no React, no build step). Keep the bundle small.
- Comments: explain **why**, not what. The code tells you what.
- No AI-generated code without review. Committer is responsible for every line.

## Commit messages

Conventional style preferred but not required:

```
feat: add NHTSA recall pipeline → M.4
fix: SEC EDGAR int/str bug in data_collector
docs: update RUBRIC.md H.3 grounding status
refactor: consolidate harm_documentation penalty application
```

## Issue templates

- `score-challenge` — a specific company's score is wrong
- `data-source` — proposing a new source
- `ladder-grounding` — academic/regulatory source for an editorial ladder
- `bug` — something broke
- `enhancement` — new feature or improvement
- `question` — not sure what to do

## Code of Conduct

Be kind. Challenge ideas, not people. If you see a score that upsets you, investigate before yelling. If you see someone else yelling without evidence, redirect gently.

We do not tolerate harassment, dismissiveness, or gatekeeping. Violations result in being asked to leave.

## Licensing

By contributing, you agree that your contributions will be licensed under Apache 2.0 (see [LICENSE](LICENSE)).

You retain copyright on your contribution. You grant Morf Innovations LLC the rights described in Apache 2.0 §5.

## Questions?

Email [hi@thehibalance.org](mailto:hi@thehibalance.org) or open a GitHub Discussion.

---

**The math decides. When we get the math wrong, we fix it and say so.**
