#!/usr/bin/env python3
"""Reshape the long-format EPLB CSV (one row per panel x setting x series)
into the wide CSV read by plots/eplb.tex (one row per prompt length x
request rate, one column per panel and series).

Rows keep the source order (medium load, then high load), which is the plot
order. Columns:
- ft_{noeplb,eplb}_{base,bubbletea}: FT samples/s without and with EPLB,
  without bubble harvesting and with BubbleTea;
- {ttft,tpot}_{alone_noeplb,bubbletea_eplb}: p90 latency relative to serving
  alone with EPLB.
Refuses to write if any cell is missing, duplicated or unknown.

Usage: python3 plots/scripts/reshape_eplb.py SRC_CSV [OUT_CSV]
"""
import csv
import sys

# (source panel, source series) -> wide column
COLUMNS = {
    ("ft_throughput", "without EPLB: no bubble harvesting"): "ft_noeplb_base",
    ("ft_throughput", "without EPLB: BubbleTea"): "ft_noeplb_bubbletea",
    ("ft_throughput", "with EPLB: no bubble harvesting"): "ft_eplb_base",
    ("ft_throughput", "with EPLB: BubbleTea"): "ft_eplb_bubbletea",
    ("p90_ttft_ratio", "serving alone, no EPLB"): "ttft_alone_noeplb",
    ("p90_ttft_ratio", "BubbleTea + EPLB"): "ttft_bubbletea_eplb",
    ("p90_tpot_ratio", "serving alone, no EPLB"): "tpot_alone_noeplb",
    ("p90_tpot_ratio", "BubbleTea + EPLB"): "tpot_bubbletea_eplb",
}


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs/eplb.csv"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    settings, cells = [], {}
    for r in rows:
        key = (r["prompt_tokens"], r["req_per_s"])
        if key not in settings:
            settings.append(key)
        cell = key + (COLUMNS[r["panel"], r["series"]],)
        if cell in cells:
            sys.exit(f"duplicate cell {cell}")
        cells[cell] = r["value"]
    if len(cells) != len(settings) * len(COLUMNS):
        sys.exit(f"expected {len(settings) * len(COLUMNS)} cells, "
                 f"got {len(cells)}")

    with open(out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["prompt_tokens", "req_per_s"] + list(COLUMNS.values()))
        for p, rate in settings:
            w.writerow([p, rate] + [cells[p, rate, c] for c in COLUMNS.values()])


if __name__ == "__main__":
    main()
