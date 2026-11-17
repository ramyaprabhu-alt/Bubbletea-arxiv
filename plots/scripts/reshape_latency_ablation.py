#!/usr/bin/env python3
"""Reshape the long-format latency-ablation CSV (one row per metric x
setting x configuration) into the wide CSV read by
plots/latency_ablation.tex (one row per prompt length x load, one column per
configuration and metric).

Rows are ordered by prompt length, then load, so bar group k is row k.
Refuses to write if any cell is missing or duplicated, if a setting has two
request rates, if the run count varies, or if a configuration mixes
campaigns. Run count and campaign are dropped from the output; at the time
of writing (B) and (E) come from campaign s62v2, (C) and (D) from s63v2, all
with 2 runs.

Usage: python3 plots/scripts/reshape_latency_ablation.py SRC_CSV [OUT_CSV]
"""
import csv
import sys

PROMPTS = ["4096", "8192", "16384"]
LOADS = ["low", "med", "high"]
# source configuration name -> wide column prefix, in plot order
STEPS = {
    "(B) + second chain": "b",
    "(C) + bubbles, ungated": "c",
    "(D) + adaptive pairing": "d",
    "(E) + early close = BubbleTea": "e",
}
# source panel -> wide column suffix
METRICS = {"sps": "ft", "p90_ttft_ratio": "ttft", "p90_tpot_ratio": "tpot"}


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs/latency_ablation.csv"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    if len({r["runs"] for r in rows}) != 1:
        sys.exit("run count is not constant")
    campaigns = {}
    cells, rates = {}, {}
    for r in rows:
        step = STEPS[r["step"]]
        if campaigns.setdefault(step, r["campaign"]) != r["campaign"]:
            sys.exit(f"{r['step']}: mixes campaigns")
        key = (r["prompt_tokens"], r["load_level"])
        if rates.setdefault(key, r["req_per_s"]) != r["req_per_s"]:
            sys.exit(f"{key}: two request rates")
        cell = key + (f"{step}_{METRICS[r['panel']]}",)
        if cell in cells:
            sys.exit(f"duplicate cell {cell}")
        cells[cell] = r["value"]

    cols = [f"{s}_{m}" for m in METRICS.values() for s in STEPS.values()]
    if len(cells) != len(PROMPTS) * len(LOADS) * len(cols):
        sys.exit(f"expected {len(PROMPTS) * len(LOADS) * len(cols)} cells, "
                 f"got {len(cells)}")
    with open(out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["prompt_tokens", "load_level", "req_per_s"] + cols)
        for p in PROMPTS:
            for l in LOADS:
                w.writerow([p, l, rates[p, l]] + [cells[p, l, c] for c in cols])


if __name__ == "__main__":
    main()
