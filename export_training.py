"""
Export C:\AI\training_data\*.jsonl as a single merged dataset.
Usage:
    python export_training.py                    # stats only
    python export_training.py --out dataset.jsonl  # merge all to one file
    python export_training.py --brother byte      # filter by brother
"""
import json
import os
import sys
from pathlib import Path

TRAINING_DIR = Path("C:/AI/training_data")

def main():
    out_file  = None
    filter_br = None
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--out"     and i + 1 < len(sys.argv) - 1: out_file  = sys.argv[i + 2]
        if arg == "--brother" and i + 1 < len(sys.argv) - 1: filter_br = sys.argv[i + 2]

    if not TRAINING_DIR.exists():
        print("No training data yet. Run the bridge and push from Android.")
        return

    records = []
    for jsonl_file in sorted(TRAINING_DIR.glob("*.jsonl")):
        with open(jsonl_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    if filter_br and r.get("brother") != filter_br:
                        continue
                    records.append(r)
                except json.JSONDecodeError:
                    pass

    print(f"Total records : {len(records)}")
    brothers = {}
    for r in records:
        b = r.get("brother", "unknown")
        brothers[b] = brothers.get(b, 0) + 1
    for b, count in sorted(brothers.items()):
        print(f"  {b:12s}: {count}")

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\nExported {len(records)} records → {out_file}")

if __name__ == "__main__":
    main()
