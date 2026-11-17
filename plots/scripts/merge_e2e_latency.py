#!/usr/bin/env python3
"""Merge the long-format p90 TTFT and TPOT CSVs (one row per system) into the
wide CSV read by plots/e2e_latency.tex (one row per model x prompt length x
load, one column per system and metric).

Rows are ordered model-major, then prompt length, then load, so the plot
selects panel k as rows 3k..3k+2. Refuses to write if any cell is missing or
duplicated, or if the two sources disagree on request rate, reference run or
repetition count.

Usage: python3 plots/scripts/merge_e2e_latency.py TTFT_CSV TPOT_CSV [OUT_CSV]
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
METRICS = ["ttft", "tpot"]


def main():
    srcs = dict(zip(METRICS, sys.argv[1:3]))
    out = sys.argv[3] if len(sys.argv) > 3 else "plots/CSVs/e2e_latency.csv"

    cells = {}
    for metric, path in srcs.items():
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        if len(rows) != len(MODELS) * len(PROMPTS) * len(LOADS) * len(SYSTEMS):
            sys.exit(f"{path}: unexpected row count {len(rows)}")
        for r in rows:
            key = (r["model"], r["prompt_tokens"], r["load_level"])
            cell = cells.setdefault(key, {"req_per_s": r["req_per_s"]})
            if cell["req_per_s"] != r["req_per_s"]:
                sys.exit(f"req_per_s differs for {key}")
            prefix = SYSTEMS[r["system"]]
            col = f"{prefix}_{metric}"
            if col in cell:
                sys.exit(f"duplicate {r['system']} {metric} row for {key}")
            cell[col] = r[f"p90_{metric}_over_serving_alone"]
            # reference run and reps are per system; both metrics must agree
            for field in ("reference", "reps"):
                prev = cell.setdefault(f"{prefix}_{field}", r[field])
                if prev != r[field]:
                    sys.exit(f"{field} differs between metrics for {key} {prefix}")

    expected = [(m, p, l) for m in MODELS for p in PROMPTS for l in LOADS]
    if sorted(cells) != sorted(expected):
        sys.exit(f"unexpected cells: got {len(cells)}")

    header = ["model", "prompt_tokens", "load_level", "req_per_s"]
    for prefix in SYSTEMS.values():
        header += [f"{prefix}_{m}" for m in METRICS]
        header += [f"{prefix}_reference", f"{prefix}_reps"]
    with open(out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for key in expected:
            c = cells[key]
            missing = [h for h in header[3:] if h not in c]
            if missing:
                sys.exit(f"missing {missing} for {key}")
            w.writerow(list(key) + [c[h] for h in header[3:]])
    print(f"wrote {out} ({len(expected)} rows, {len(header)} columns)")


if __name__ == "__main__":
    main()
