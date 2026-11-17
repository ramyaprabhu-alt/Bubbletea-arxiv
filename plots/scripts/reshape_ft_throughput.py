#!/usr/bin/env python3
"""Reshape the long-format fine-tuning throughput CSV (one row per system)
into the wide CSV read by plots/ft_throughput.tex (one row per
model x prompt length x load, one column per system).

Rows are ordered model-major, then prompt length, then load, so the plot
selects panel k as rows 3k..3k+2. Refuses to write if any cell is missing
or duplicated, or if a ratio label disagrees with the throughputs.

Usage: python3 plots/scripts/reshape_ft_throughput.py SRC_CSV [OUT_CSV]
"""
import csv
import sys

MODELS = ["Qwen3-30B-A3B", "Qwen1.5-MoE-A2.7B", "DeepSeek-V2-Lite"]
PROMPTS = ["4096", "8192", "16384", "24576", "32768"]
LOADS = ["low", "med", "high"]
# source system name -> wide column prefix, in plot order
SYSTEMS = {
    "LLMStation": "llmstation",
    "Naive colocation (6% cap)": "naive_cap",
    "Naive colocation (no cap)": "naive_nocap",
    "BubbleTea": "bubbletea",
}


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs/ft_throughput.csv"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    cells = {}
    for r in rows:
        key = (r["model"], r["prompt_tokens"], r["load_level"])
        cell = cells.setdefault(key, {"req_per_s": r["req_per_s"]})
        if cell["req_per_s"] != r["req_per_s"]:
            sys.exit(f"req_per_s differs across systems for {key}")
        prefix = SYSTEMS[r["system"]]
        if prefix in cell:
            sys.exit(f"duplicate {r['system']} row for {key}")
        cell[prefix] = r["ft_samples_per_s"]
        cell[prefix + "_reps"] = r["reps"]
        if r["system"] == "BubbleTea":
            cell["ratio"] = r["label_bubbletea_over_llmstation"]

    expected = [(m, p, l) for m in MODELS for p in PROMPTS for l in LOADS]
    if sorted(cells) != sorted(expected) or len(rows) != len(expected) * len(SYSTEMS):
        sys.exit(f"unexpected cells: got {len(cells)} cells from {len(rows)} rows")

    header = ["model", "prompt_tokens", "load_level", "req_per_s"]
    for prefix in SYSTEMS.values():
        header += [prefix, prefix + "_reps"]
    header += ["bubbletea_over_llmstation"]
    with open(out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for key in expected:
            c = cells[key]
            ratio = float(c["bubbletea"]) / float(c["llmstation"])
            if abs(ratio - float(c["ratio"])) > 1e-9 * ratio:
                sys.exit(f"ratio label {c['ratio']} != {ratio} for {key}")
            w.writerow(list(key) + [c[h] for h in header[3:-1]] + [c["ratio"]])
    print(f"wrote {out} ({len(expected)} rows from {len(rows)} source rows)")


if __name__ == "__main__":
    main()
