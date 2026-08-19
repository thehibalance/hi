#!/usr/bin/env python3
"""Summarize pipeline collection errors. Fails the job on systematic failures."""
import collections, os, pathlib, re, sys

LOG = pathlib.Path(os.environ.get("PIPELINE_LOG", "/tmp/pipeline.log"))
SYSTEMATIC_THRESHOLD = int(os.environ.get("SYSTEMATIC_THRESHOLD", "10"))

if not LOG.exists():
    print(f"No log at {LOG}; nothing to summarize.")
    sys.exit(0)

text = LOG.read_text(errors="replace")

COMPANY_ERR = re.compile(r"\[(\d+)/(\d+)\]\s+(.*?)\s+\(([^)]*)\)\s+ERROR:\s*(.+)")
SOURCE_ERR = re.compile(r"^\s*([A-Z][A-Za-z0-9_]*)\s+error:\s*(.+)", re.MULTILINE)
UNIVERSE = re.compile(r"Universe tickers:\s+(\d+)\s+new tickers added \(total:\s+(\d+)\)")
SKIPPED = re.compile(r"Skipped\s+(\d+)\s+companies")

by_msg = collections.defaultdict(list)
total = 0
for m in COMPANY_ERR.finditer(text):
    total = max(total, int(m.group(2)))
    by_msg[m.group(5).strip()[:110]].append(m.group(4) or m.group(3))

src = collections.Counter(m.group(1) for m in SOURCE_ERR.finditer(text))
uni = UNIVERSE.search(text)
skip = SKIPPED.search(text)

lines = ["## Pipeline run summary", ""]
if uni:
    lines.append(f"- Companies in universe: **{uni.group(2)}** ({uni.group(1)} new this run)")
if skip:
    lines.append(f"- Skipped as fresh (<24h): **{skip.group(1)}**")
n_err = sum(len(v) for v in by_msg.values())
lines.append(f"- Companies that errored: **{n_err}**")
lines.append("")

systematic = []
if by_msg:
    lines += ["### Company failures, grouped", "",
              "| count | error | examples |", "|---:|---|---|"]
    for msg, tickers in sorted(by_msg.items(), key=lambda kv: -len(kv[1])):
        flag = ""
        if len(tickers) >= SYSTEMATIC_THRESHOLD:
            systematic.append((msg, len(tickers)))
            flag = " 🚨"
        ex = ", ".join(tickers[:6]) + ("…" if len(tickers) > 6 else "")
        lines.append(f"| {len(tickers)}{flag} | `{msg}` | {ex} |")
    lines.append("")

if src:
    lines += ["### Data sources erroring", "", "| source | occurrences |", "|---|---:|"]
    for s, c in src.most_common():
        lines.append(f"| {s} | {c} |")
    lines.append("")

if systematic:
    lines += ["", f"> **Systematic failure detected.** One error affected "
                  f"{SYSTEMATIC_THRESHOLD}+ companies — that is a bug, not flaky upstream data."]

report = "\n".join(lines)
print(report)
summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a") as f:
        f.write(report + "\n")

if systematic:
    for msg, n in systematic:
        print(f"::error::{n} companies failed with: {msg}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
