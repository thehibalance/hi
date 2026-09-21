#!/usr/bin/env python3
"""Give each data file the timestamp of the commit that last changed it.

Why: data_collector.py decides whether a company needs re-collecting by the
age of its files (is_stale -> st_mtime). A fresh `actions/checkout` stamps
every file with the checkout time, so every company looked minutes old and
every nightly run skipped all of them ("Skipped as fresh: 1233"). Raw data
stopped refreshing in April 2026 while scores kept recomputing.

Run from the repo root, after checkout (needs full history: fetch-depth: 0).
  python3 pipeline/restore_mtimes.py [dir ...]
"""
import os
import subprocess
import sys
import time

DIRS = sys.argv[1:] or ["pipeline/data/subsignals", "pipeline/data/extended"]
THRESHOLD_H = 20  # matches --incremental 20 in daily-pipeline.yml

log = subprocess.run(
    ["git", "-c", "core.quotePath=false", "log", "--format=@%ct",
     "--name-only", "--no-renames", "--", *DIRS],
    capture_output=True, text=True, check=True).stdout

last_commit = {}
ts = None
for line in log.splitlines():
    if line.startswith("@"):
        ts = int(line[1:])
    elif line and line not in last_commit:
        last_commit[line] = ts  # git log is newest-first: first sighting wins

now = time.time()
restored = older = 0
for path, t in last_commit.items():
    if os.path.isfile(path):
        os.utime(path, (t, t))
        restored += 1
        if now - t > THRESHOLD_H * 3600:
            older += 1

print(f"Restored commit timestamps on {restored} files in {', '.join(DIRS)}")
print(f"  {older} are older than {THRESHOLD_H}h and will be re-collected; "
      f"{restored - older} are fresher and will be skipped")
