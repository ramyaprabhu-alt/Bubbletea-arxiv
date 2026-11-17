#!/usr/bin/env python3
"""Split the long-format bubble-use CSV (two panels in one file) into the two
CSVs read by plots/bubble_supply.tex:

- bubble_accounting.csv: where BubbleTea's non-straggler bubble time goes at
  8k tokens and 2 req/s, one row per category (% of bubble time and ms).
- bubble_growth.csv: total bubble time at 8k tokens and 4 req/s under each
  execution policy, one row per policy (% change vs serving alone).

Rows keep the source order, which is the plot order. Refuses to write if a
category or policy is missing, duplicated or unknown.

Usage: python3 plots/scripts/split_bubble_supply.py SRC_CSV [OUT_DIR]
"""
import csv
import os
import sys

ACCOUNTING_PANEL = "left: 8k@2 slack accounting"
GROWTH_PANEL = "right: 8k@4 total bubble time"
# source category -> short key, in plot order
CATEGORIES = {
    "trained (training kernel running)": "trained",
    "gate open, no training kernel": "open_idle",
    "closed early, before straggler arrived": "closed_early",
    "before the gate opened (open latency)": "open_latency",
    "gate never opened": "never_opened",
}
# source run name, in plot order
POLICIES = ["nobub_bp", "work_bp", "gating_bp", "v1_min_bp", "v1_min_1ch_bp"]


def main():
    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    accounting = [r for r in rows if r["panel"] == ACCOUNTING_PANEL]
    growth = [r for r in rows if r["panel"] == GROWTH_PANEL]
    if len(accounting) + len(growth) != len(rows):
        sys.exit("unknown panel")
    if [r["category"] for r in accounting] != list(CATEGORIES):
        sys.exit("accounting categories differ from the expected list")
    if [r["config"] for r in growth] != POLICIES:
        sys.exit("growth policies differ from the expected list")

    with open(os.path.join(out_dir, "bubble_accounting.csv"), "w",
              newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["category", "pct", "ms"])
        for r in accounting:
            w.writerow([CATEGORIES[r["category"]], r["value"], r["ms"]])

    with open(os.path.join(out_dir, "bubble_growth.csv"), "w",
              newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["policy", "pct_change"])
        for r in growth:
            w.writerow([r["config"], r["value"]])


if __name__ == "__main__":
    main()
