#!/usr/bin/env python3
"""Write the §6.2 / Appendix B CSVs straight from the collected §6.2 numbers.

Inputs (BubbleTea-results/eval/s62/v4, written by v4/collect_v4.py):
  s62.json            all arms; arm "tt" = naive colocation at a 6% MPS cap
  s62_tt40.json       same, arm "tt" from naive_torchtune/runs_cap40 (40% cap)
  s62_ttuncapped.json same, arm "tt" from naive_torchtune/runs (no cap)

Outputs (rows model-major, then prompt length, then load, so a panel plots
3 consecutive rows):
  plots/CSVs/ft_throughput.csv  LLMStation, naive colocation (40% cap), BubbleTea
  plots/CSVs/e2e_latency.csv    same systems, p90 TTFT / TPOT over serving alone
  plots/CSVs/naive_sweep.csv    naive colocation at 6%, 40% and no cap
  plots/CSVs/eplb_8k.csv        §6.6 body figure: 8k @ 2 and 4 req/s, FT samples/s
                                and p90 TTFT / TPOT in ms (s64/fig64_eplb.csv)
  plots/CSVs/trace_results.csv  Fig. 9 per-trace results; naive colocation at
                                the 40% cap (trace.json, trace_tt40.json from
                                s62/collect_trace_v2.py with TT_RUNS=runs_cap40)

Values match v5/make_figs.py: samples/s is the mean over reps, latency the
p90 over pooled requests divided by the system's own serving-only reference.
A cell whose run failed is written as nan and drawn as a missing bar.

Usage: python3 plots/scripts/make_e2e_csvs.py [V4_DIR]
"""
import csv
import json
import math
import sys

V4 = sys.argv[1] if len(sys.argv) > 1 else \
    "/mnt/nfs/home/ramya/BubbleTea-results/eval/s62/v4"
MODELS = [("qwen3", "Qwen3-30B-A3B"), ("qwen15", "Qwen1.5-MoE-A2.7B"),
          ("dsv2", "DeepSeek-V2-Lite")]
PROMPTS = [1024, 2048, 4096, 8192, 16384, 24576, 32768]
LOADS = ["low", "med", "high"]
# collected field -> CSV column suffix
SUFFIX = {"sps": "", "p90_ttft_x": "_ttft", "p90_tpot_x": "_tpot"}


def load(name, rename_tt=None):
    rows = json.load(open(f"{V4}/{name}"))
    if rename_tt:
        rows = [dict(r, arm=rename_tt) for r in rows if r["arm"] == "tt"]
    return {(r["model"], r["len"], r["level"], r["arm"]): r for r in rows}


R = load("s62.json")
R.update(load("s62.json", "tt6"))
R.update(load("s62_tt40.json", "tt40"))
R.update(load("s62_ttuncapped.json", "tt100"))


def get(key, field):
    r = R.get(key)
    if not r or not r["reps"] or r.get(field) is None:
        return math.nan
    return r[field]


def write(path, systems, fields, ratio=None, lift=False):
    header = ["model", "prompt_tokens", "load_level", "req_per_s"]
    for col, _ in systems:
        header += [col + SUFFIX[f] for f in fields]
        header.append(f"{col}_reps")
    if ratio:
        header.append(ratio[2])
    if lift:
        # raise BubbleTea's ratio label above the tallest bar of its group
        header.append("label_lift")
    rows = []
    for m, mname in MODELS:
        for t in PROMPTS:
            for lv in LOADS:
                ref = R.get((m, t, lv, "vllm"))
                if ref is None:
                    sys.exit(f"no serving-only run for {m} {t} {lv}")
                row = [mname, t, lv, ref["qps"]]
                for col, arm in systems:
                    for f in fields:
                        row.append(get((m, t, lv, arm), f))
                    row.append((R.get((m, t, lv, arm)) or {}).get("reps", 0))
                if ratio:
                    num = get((m, t, lv, ratio[0]), "sps")
                    den = get((m, t, lv, ratio[1]), "sps")
                    row.append(num / den if den else math.nan)
                if lift:
                    vals = [get((m, t, lv, arm), "sps") for _, arm in systems]
                    others = [v for v in vals[:-1] if not math.isnan(v)]
                    row.append(max([0.0] + [v - vals[-1] for v in others]))
                rows.append(row)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    missing = sum(1 for r in rows for v in r if isinstance(v, float) and math.isnan(v))
    print(f"{path}: {len(rows)} rows, {missing} missing values")


MAIN = [("llmstation", "llms"), ("naive40", "tt40"), ("bubbletea", "v1_min")]
SWEEP = [("naive6", "tt6"), ("naive40", "tt40"), ("naivenone", "tt100")]
write("plots/CSVs/ft_throughput.csv", MAIN, ["sps"],
      ratio=("v1_min", "llms", "bubbletea_over_llmstation"), lift=True)
write("plots/CSVs/e2e_latency.csv", MAIN, ["p90_ttft_x", "p90_tpot_x"])
write("plots/CSVs/naive_sweep.csv", SWEEP, ["sps", "p90_ttft_x", "p90_tpot_x"])


# --- Fig. 9: production traces at their original rate (1x)
TRACES = [("azure_code", "code"), ("azure_conv", "conversation")]
TR = {(r["trace"], r["scale"], r["arm"]): r for r in json.load(open(f"{V4}/trace.json"))}
TR.update({(r["trace"], r["scale"], "tt40"): r
           for r in json.load(open(f"{V4}/trace_tt40.json")) if r["arm"] == "tt"})
TSYS = [("alone", "vllm"), ("llmstation", "llms"), ("naive40", "tt40"), ("bubbletea", "v1_min")]
header = ["trace", "requests", "mean_req_per_s"]
header += [f"{c}_ft" for c, _ in TSYS[1:]]
header += [f"{c}_{k}" for k in ("ttft", "tpot") for c, _ in TSYS]
rows = []
for tr, name in TRACES:
    alone = TR[(tr, "1x", "vllm")]
    row = [name, alone["requests"], alone["requests"] / alone["trace_seconds"]]
    row += [TR[(tr, "1x", a)]["sps"] for _, a in TSYS[1:]]
    row += [TR[(tr, "1x", a)][f"p90_{k}"] for k in ("ttft", "tpot") for _, a in TSYS]
    rows.append(row)
with open("plots/CSVs/trace_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)
print(f"plots/CSVs/trace_results.csv: {len(rows)} rows")


# --- §6.6 body figure: EPLB at 8k prompts, 2 and 4 req/s
S64 = V4.replace("/s62/v4", "/s64") + "/fig64_eplb.csv"
E = {(r["panel"], r["prompt_tokens"], r["req_per_s"], r["series"]): float(r["value"])
     for r in csv.DictReader(open(S64))}
ECOLS = [  # (CSV column, source panel, source series)
    ("ft_noeplb_base", "ft_throughput", "no EPLB: without bubbles"),
    ("ft_noeplb_bubbletea", "ft_throughput", "no EPLB: BubbleTea total"),
    ("ft_eplb_base", "ft_throughput", "EPLB: without bubbles"),
    ("ft_eplb_bubbletea", "ft_throughput", "EPLB: BubbleTea total"),
] + [(f"{k}_{c}", f"p90_{k}", src) for k in ("ttft", "tpot") for c, src in
     (("alone", "vLLM alone"), ("alone_eplb", "vLLM + EPLB"), ("bubbletea_eplb", "BubbleTea + EPLB"))]
with open("plots/CSVs/eplb_8k.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["prompt_tokens", "req_per_s"] + [c for c, _, _ in ECOLS])
    for q in ("2", "4"):
        w.writerow(["8192", q] + [E[(panel, "8192", q, src)] for _, panel, src in ECOLS])
print("plots/CSVs/eplb_8k.csv: 2 rows")
