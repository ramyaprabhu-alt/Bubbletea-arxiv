#!/usr/bin/env python3
"""Reshape the long-format throughput-sources CSV (one row per configuration)
into the wide CSV read by plots/sources.tex (one row per prompt length x
load, one column per configuration).

Rows are ordered by prompt length, then load, so the plot draws group k as
rows 3k..3k+2. Refuses to write if any cell is missing or duplicated, if a
setting has two request rates, or if the run count or campaign varies (they
are dropped from the output).

Usage: python3 plots/scripts/reshape_sources.py SRC_CSV [OUT_CSV]
"""
import csv
import sys

PROMPTS = ["4096", "8192", "16384"]
LOADS = ["low", "med", "high"]
# source configuration name -> wide column, in plot order
STEPS = {
    "(A) plain colocation": "a_plain",
    "(B) + second chain": "b_second_chain",
    "(E) + early close = BubbleTea": "e_bubbletea",
}


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs/sources.csv"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    for col in ["panel", "runs", "campaign"]:
        if len({r[col] for r in rows}) != 1:
            sys.exit(f"{col} is not constant")

    cells, rates = {}, {}
    for r in rows:
        key = (r["prompt_tokens"], r["load_level"])
        if rates.setdefault(key, r["req_per_s"]) != r["req_per_s"]:
            sys.exit(f"{key}: two request rates")
        cell = key + (STEPS[r["step"]],)
        if cell in cells:
            sys.exit(f"duplicate cell {cell}")
        cells[cell] = r["value"]
    if len(cells) != len(PROMPTS) * len(LOADS) * len(STEPS):
        sys.exit(f"expected {len(PROMPTS) * len(LOADS) * len(STEPS)} cells, "
                 f"got {len(cells)}")

    with open(out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["prompt_tokens", "load_level", "req_per_s"]
                   + list(STEPS.values()))
        for p in PROMPTS:
            for l in LOADS:
                w.writerow([p, l, rates[p, l]]
                           + [cells[p, l, s] for s in STEPS.values()])


if __name__ == "__main__":
    main()
