#!/usr/bin/env python3
"""Reshape the scheduling-overhead CSVs into the two CSVs read by
plots/sched_overhead.tex:

- sched_overhead.csv: one row per model x load (source order, which is the
  plot order), with the latency change of BubbleTea's idle-trainer hooks vs
  serving alone in percent, one column per metric (p50/p90 TTFT/TPOT).
- hook_cost.csv: one row per model, GPU and host time of the hooks in
  microseconds per prefill MoE layer.

Refuses to write if a metric or side is missing or duplicated.

Usage: python3 plots/scripts/reshape_sched_overhead.py SCHED_CSV HOOK_CSV [OUT_DIR]
"""
import csv
import os
import sys

METRICS = {"p50 TTFT": "p50_ttft", "p90 TTFT": "p90_ttft",
           "p50 TPOT": "p50_tpot", "p90 TPOT": "p90_tpot"}
MODELS = ["Qwen3-30B-A3B", "Qwen1.5-MoE-A2.7B", "DeepSeek-V2-Lite"]


def main():
    sched_src, hook_src = sys.argv[1], sys.argv[2]
    out_dir = sys.argv[3] if len(sys.argv) > 3 else "plots/CSVs"
    with open(sched_src, newline="") as f:
        sched = list(csv.DictReader(f))
    with open(hook_src, newline="") as f:
        hook = list(csv.DictReader(f))

    settings, cells = [], {}
    for r in sched:
        key = (r["model"], r["load"], r["qps"])
        if key not in cells:
            settings.append(key)
            cells[key] = {"runs": f'{r["vllm_runs"]}+{r["bubbletea_runs"]}'}
        col = METRICS[r["metric"]]
        if col in cells[key]:
            sys.exit(f"duplicate {key} {col}")
        cells[key][col] = f'{100 * float(r["change_vs_vllm"]):.3f}'
    with open(os.path.join(out_dir, "sched_overhead.csv"), "w",
              newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["model", "load", "req_per_s", "runs"] +
                   list(METRICS.values()))
        for key in settings:
            if len(cells[key]) != len(METRICS) + 1:
                sys.exit(f"missing metric for {key}")
            # "high−" (U+2212) -> plain ASCII for the LaTeX tick labels
            w.writerow([key[0], key[1].replace("−", "-"), key[2],
                        cells[key]["runs"]] +
                       [cells[key][c] for c in METRICS.values()])

    cost = {(r["model"], r["side"]): r["us_per_prefill_moe_layer"]
            for r in hook}
    if len(cost) != len(hook) or \
            set(cost) != {(m, s) for m in MODELS for s in ("gpu", "host")}:
        sys.exit("hook cost: models or sides differ from the expected list")
    with open(os.path.join(out_dir, "hook_cost.csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["model", "gpu_us", "host_us"])
        for m in MODELS:
            w.writerow([m, f'{float(cost[(m, "gpu")]):.3f}',
                        f'{float(cost[(m, "host")]):.3f}'])


if __name__ == "__main__":
    main()
