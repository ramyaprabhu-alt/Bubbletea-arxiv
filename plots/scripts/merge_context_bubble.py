#!/usr/bin/env python3
"""Merge the per-model context_bubble_<model>.csv files into one wide CSV.

Output: one row per context length, with the per-model columns prefixed by
the model key (e.g. qwen3_median_ms). Refuses to write if the models disagree
on the context rows, so no data is silently dropped or misaligned.

Usage: python3 plots/scripts/merge_context_bubble.py [CSV_DIR]
"""
import csv
import sys
from pathlib import Path

# model key -> source file suffix, in plot/legend order
MODELS = ["qwen3", "qwen15moe", "deepseek"]
KEY_COLS = ["context_label", "context_tokens"]


def main():
    csv_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "plots/CSVs")
    tables = {}
    for model in MODELS:
        with open(csv_dir / f"context_bubble_{model}.csv", newline="") as f:
            tables[model] = list(csv.DictReader(f))

    keys = {m: [tuple(r[c] for c in KEY_COLS) for r in rows]
            for m, rows in tables.items()}
    ref = keys[MODELS[0]]
    for m in MODELS[1:]:
        if keys[m] != ref:
            sys.exit(f"context rows differ between {MODELS[0]} and {m}: "
                     f"{ref} vs {keys[m]}")

    value_cols = [c for c in tables[MODELS[0]][0] if c not in KEY_COLS]
    header = KEY_COLS + [f"{m}_{c}" for m in MODELS for c in value_cols]
    out_path = csv_dir / "context_bubble.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for i, key in enumerate(ref):
            w.writerow(list(key) + [tables[m][i][c]
                                    for m in MODELS for c in value_cols])
    print(f"wrote {out_path} ({len(ref)} rows, {len(header)} columns)")


if __name__ == "__main__":
    main()
