"""The source-publication rule, in one place.

    from source_rules import NOT_SOURCES, normalize_source

Two callers apply it and must not disagree:

  * `api_server.get_contributing_sources()` — what /api/v1/stats serves as `data_sources`
  * `check_continuity.contributing_sources()` — what the gate checks the README against

They disagreed for eight hours, because the rule existed twice. api_server's copy gained
"Industry+EPA" (PR #40), "Glassdoor" and "Jobs" (PRs #42/#43); check_continuity's copy kept its
original four members and therefore reported a stale README figure of 21 as correct. The gate
built to catch a stale source count was itself the stale source count, asserting agreement.

Two artefacts agreeing is only evidence when they are derived independently. One rule authored
twice is not two artefacts.

This module imports nothing. It is deliberately cheap, because the alternative — the gate
importing api_server — boots the whole API on import: 1,140 companies, heartbeat, HUMAN 100,
arbitrage, contagion, thresholds. A CI check should not start a web service to learn seven
strings.

See claude/FINDING-the-gate-copies-the-rule-it-claims-to-mirror.md
"""

NOT_SOURCES = {
    # Industry+EPA was A.3's source label until PR #40. The value came from the
    # DEFORESTATION_RISK industry table; the EPA store is 26 records, every one an
    # error, last fetched 2026-04-14. Excluded here rather than mapped to "EPA"
    # below, because deleting that mapping alone would publish the literal string
    # "Industry+EPA" as a source name.
    "Industry+EPA",

    "Industry", "Manual Scoring", "Defaults", "Seed Estimate",
    # GLASSDOOR_DATA (glassdoor_pipeline.py:26) and JOB_DATA
    # (job_board_pipeline.py:34) are literal Python dicts — 43 and 37 hand-typed
    # companies. Neither module fetches anything; neither is in the nightly. Every
    # sampled ai_ratio is a multiple of 0.05 and exactly equals
    # ai_postings/total_postings, so the ratio was authored and the count derived
    # from it. A hand-authored table cannot be credited to the company whose name
    # it carries — the same correction as Industry+EPA in v1.12.x, at ~70x the rows.
    #
    # They still feed scores. This only stops them being published as external
    # PROVIDERS. Whether they should count as evidence in real_count is a separate
    # and larger decision: 30 of 30 'Strong'/'Verified' rows cite one of them.
    # See claude/FINDING-glassdoor-and-jobs-are-hand-authored-dicts.md
    "Glassdoor", "Jobs",
}

def normalize_source(src):
    """The published name for a raw source tag, or None if it must not be published.

    SEC filing types count once as SEC: a company is not better documented for having filed a
    DEF 14A as well as a 10-K through the same collector against the same registry.
    """
    if src in NOT_SOURCES:
        return None
    if src.startswith("SEC"):
        return "SEC"
    return src
