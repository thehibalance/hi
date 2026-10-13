"""One place that knows what a scored row is.

`data/scores/all_scores.json` holds every company in the tracked universe, scored or not.
A row with no `spec_version` was never scored — it is a private or foreign company with no
SEC filing, so there is no revenue and no headcount to divide, and H.1/H.3 cannot be
computed. Samsung Electronics, TikTok/ByteDance, Stripe, OpenAI and Anthropic are in that
set. They are legitimately tracked and legitimately unscored.

Four feature pipelines used to load the file raw and analyse all 1,139 rows, publishing
grade-arbitrage verdicts and ethical-moat levels for companies with no genome. Hence this
module: the rule lives once, and every consumer calls it.

    load_scored()    the 1,045 rows that have a score — use this
    load_all_rows()  every row, scored or not — for counting the universe
    split()          (scored, unscored) with the counts, for anything reporting both

Published counts should say "1,045 scored of 1,139 tracked" rather than a bare number.
See claude/FINDING-the-ninetyfour-unscorable.md
"""
import json
from pathlib import Path

SCORES_PATH = "data/scores/all_scores.json"


def load_all_rows(path=SCORES_PATH):
    """Every row in the tracked universe, scored or not."""
    p = Path(path)
    if not p.exists():
        return []
    data = json.load(open(p))
    return [r for r in (data if isinstance(data, list) else list(data.values()))
            if isinstance(r, dict)]


def is_scored(row):
    """A row is scored when the engine stamped it with the spec it was scored under."""
    return bool(row.get("spec_version")) and not row.get("error")


def load_scored(path=SCORES_PATH):
    """The rows that have a score. What every feature and every ranking should use."""
    return [r for r in load_all_rows(path) if is_scored(r)]


def split(path=SCORES_PATH):
    """(scored, unscored). The unscored set is not an error state — name it, do not hide it."""
    rows = load_all_rows(path)
    return [r for r in rows if is_scored(r)], [r for r in rows if not is_scored(r)]
