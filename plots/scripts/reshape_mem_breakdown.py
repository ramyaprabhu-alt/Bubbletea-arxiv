#!/usr/bin/env python3
"""Reshape the long-format trainer memory breakdown (one row per model x
part) into the wide CSV read by plots/mem_breakdown.tex: one row per model
(source order), one column per stacked part in GiB per GPU, and the total.
Refuses to write if a part is missing or the parts do not add up to the
total.

Usage: python3 plots/scripts/reshape_mem_breakdown.py SRC_CSV [OUT_CSV]
"""
import csv
import sys

# stacking order, bottom to top
PARTS = ["lora_state", "graph_pool", "eager_live", "cached", "context"]


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs/mem_breakdown.csv"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    models, cells = [], {}
    for r in rows:
        if r["model"] not in cells:
            models.append(r["model"])
            cells[r["model"]] = {}
        cells[r["model"]][r["part"]] = float(r["GiB_per_GPU"])
    with open(out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["model"] + PARTS + ["total"])
        for m in models:
            if set(cells[m]) != set(PARTS) | {"total"}:
                sys.exit(f"{m}: parts differ from the expected list")
            if abs(sum(cells[m][p] for p in PARTS) - cells[m]["total"]) > 1e-3:
                sys.exit(f"{m}: parts do not add up to the total")
            w.writerow([m] + [f"{cells[m][p]:.4f}" for p in PARTS + ["total"]])


if __name__ == "__main__":
    main()
