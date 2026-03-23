#!/usr/bin/env python3
"""
Merge scores: keeps all existing companies, updates with fresh data.
Score count can only go UP, never down.
Usage: python3 merge_scores.py backup.json fresh.json output.json
"""
import json, sys

def merge(backup_path, fresh_path, output_path):
    backup = json.load(open(backup_path))
    fresh = json.load(open(fresh_path))
    
    merged = {}
    for c in backup:
        key = c.get("company", "").lower()
        if key:
            merged[key] = c
    for c in fresh:
        key = c.get("company", "").lower()
        if key:
            merged[key] = c  # fresh overwrites backup
    
    result = list(merged.values())
    json.dump(result, open(output_path, "w"), indent=2)
    print(f"Merged: {len(backup)} existing + {len(fresh)} fresh = {len(result)} total")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 merge_scores.py backup.json fresh.json output.json")
        sys.exit(1)
    merge(sys.argv[1], sys.argv[2], sys.argv[3])
