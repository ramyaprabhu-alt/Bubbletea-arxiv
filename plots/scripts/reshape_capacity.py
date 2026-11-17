#!/usr/bin/env python3
"""Reshape the spare-capacity CSV (one row per model x prompt length x request
rate, many diagnostic columns) into the CSV read by plots/capacity.tex.

Rows are in plot order: model (Qwen3, Qwen1.5, DeepSeek), then prompt length
(1k-32k), then request rate from the high load down to a quarter of it, so a
panel plots 4 consecutive rows. Columns idle, decode, bubbles give the share
of one GPU in percent (the three stacked segments). Refuses to write if a
panel does not have exactly 4 loads.

Usage: python3 plots/scripts/reshape_capacity.py SRC_CSV [OUT_CSV]
"""
import csv
import sys

MODELS = ["Qwen3-30B-A3B", "Qwen1.5-MoE-A2.7B", "DeepSeek-V2-Lite"]
PROMPTS = [1024, 2048, 4096, 8192, 16384, 24576, 32768]


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs/capacity.csv"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    panels = {}
    for r in rows:
        panels.setdefault((r["model"], int(r["prompt_tokens"])), []).append(r)
    if set(panels) != {(m, p) for m in MODELS for p in PROMPTS}:
        sys.exit("models or prompt lengths differ from the expected list")

    with open(out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["model", "prompt_tokens", "req_per_s", "frac_of_high",
                    "idle", "decode", "bubbles"])
        for m in MODELS:
            for p in PROMPTS:
                panel = sorted(panels[(m, p)], key=lambda r: -float(r["qps"]))
                if [float(r["frac_of_high"]) for r in panel] != \
                        [1.0, 0.75, 0.5, 0.25]:
                    sys.exit(f"{m} {p}: loads are not 1, 3/4, 1/2, 1/4")
                for r in panel:
                    w.writerow([m, p, r["qps"], r["frac_of_high"]] +
                               [f"{100 * float(r[k]):.3f}"
                                for k in ("idle", "decode", "bubbles")])


if __name__ == "__main__":
    main()
