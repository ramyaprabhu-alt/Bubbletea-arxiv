#!/usr/bin/env python3
"""Split the long-format overheads CSV (two panels in one file) into the two
CSVs read by plots/overheads.tex:

- gpu_memory.csv: one row per model x configuration (LLMStation, BubbleTea,
  EPLB, BubbleTea + EPLB; source order, which is the plot order), with the
  stacked parts (trainer, experts, other) and the total in % of 80 GB per
  GPU. Configurations without data (no EPLB in vLLM for Qwen1.5-MoE) have
  available=0 and zeros (not empty cells: pgfplots stacks bars by index, so
  a discarded row would shift the following bars).
- training_loss.csv: one row per training step, 25-step moving-average loss
  of BubbleTea (mean over runs) and of the standalone HF + PEFT trainer.

Refuses to write if a part, configuration or step is missing or duplicated.

Usage: python3 plots/scripts/split_overheads.py SRC_CSV [OUT_DIR]
"""
import csv
import os
import sys

CONFIGS = ["LLMStation", "BubbleTea", "EPLB", "BubbleTea + EPLB"]
PARTS = ["trainer", "experts", "other", "total"]
LOSS_SERIES = {"BubbleTea (mean over runs)": "bubbletea",
               "HF + PEFT trainer alone": "hf_peft"}


def main():
    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    mem = [r for r in rows if r["panel"] == "gpu_memory"]
    loss = [r for r in rows if r["panel"] == "training_loss"]
    if len(mem) + len(loss) != len(rows):
        sys.exit("unknown panel")

    settings, cells = [], {}
    for r in mem:
        key = (r["model"], r["series"])
        if key not in cells:
            settings.append(key)
            cells[key] = {}
        if r["x"] in cells[key]:
            sys.exit(f"duplicate {key} {r['x']}")
        cells[key][r["x"]] = r["value"]
    with open(os.path.join(out_dir, "gpu_memory.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["model", "config", "available"] + PARTS)
        for key in settings:
            if key[1] not in CONFIGS:
                sys.exit(f"unknown configuration {key}")
            c = cells[key]
            if c.get("total") == "n/a" and len(c) == 1:
                w.writerow(list(key) + [0] + ["0"] * len(PARTS))
                continue
            if not set(PARTS) <= set(c):
                sys.exit(f"{key}: parts differ from the expected list")
            if abs(sum(float(c[p]) for p in PARTS[:-1]) -
                   float(c["total"])) > 1e-3:
                sys.exit(f"{key}: parts do not add up to the total")
            w.writerow(list(key) + [1] +
                       [f"{float(c[p]):.3f}" for p in PARTS])

    steps = {}
    for r in loss:
        col = LOSS_SERIES[r["series"]]
        step = steps.setdefault(int(r["x"]), {})
        if col in step:
            sys.exit(f"duplicate step {r['x']} {col}")
        step[col] = r["value"]
    with open(os.path.join(out_dir, "training_loss.csv"), "w",
              newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["step"] + list(LOSS_SERIES.values()))
        for s in sorted(steps):
            if len(steps[s]) != len(LOSS_SERIES):
                sys.exit(f"step {s}: missing series")
            w.writerow([s] + [f"{float(steps[s][c]):.5f}"
                              for c in LOSS_SERIES.values()])


if __name__ == "__main__":
    main()
