#!/usr/bin/env python3
"""Split the long-format trace CSV (one row per panel x trace x system/bin)
into the two CSVs read by plots/trace.tex:

- trace_arrivals.csv: one row per 10 s bin, one column per trace (requests/s
  in the bin starting at t). Empty after the end of the shorter trace.
- trace_results.csv: one row per trace with its request count and mean rate,
  then one column per system and metric (FT samples/s, p90 TTFT/TPOT in ms).

Refuses to write if any cell is missing or duplicated, or if a trace's bins
do not add up to a whole number of requests.

Usage: python3 plots/scripts/split_trace.py SRC_CSV [OUT_DIR]
"""
import csv
import os
import sys

TRACES = {"Azure code": "code", "Azure conversation": "conversation"}
# source system name -> wide column prefix, in plot order
SYSTEMS = {
    "Serving alone": "alone",
    "LLMStation": "llmstation",
    "Naive colocation (6% cap)": "naive_cap",
    "BubbleTea": "bubbletea",
}
METRICS = {"ft_throughput": "ft", "p90_ttft": "ttft", "p90_tpot": "tpot"}


def put(d, key, value):
    if key in d:
        sys.exit(f"duplicate cell {key}")
    d[key] = value


def main():
    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "plots/CSVs"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))

    bins, means, results = {}, {}, {}
    for r in rows:
        trace = TRACES[r["trace"]]
        if r["panel"] == "arrivals":
            if r["x"] == "mean":
                put(means, trace, r["value"])
            else:
                put(bins, (int(r["x"]), trace), r["value"])
        else:
            col = f"{SYSTEMS[r['system']]}_{METRICS[r['panel']]}"
            put(results, (trace, col), r["value"])

    # arrivals: bins every 10 s from 0 to the end of the longest trace
    ts = sorted({t for t, _ in bins})
    if ts != list(range(0, ts[-1] + 10, 10)):
        sys.exit("arrival bins are not contiguous 10 s steps")
    requests = {}
    for trace in TRACES.values():
        own = sorted(t for t, tr in bins if tr == trace)
        if own != list(range(0, own[-1] + 10, 10)):
            sys.exit(f"{trace}: arrival bins have gaps")
        # each bin is requests/s over 10 s, so 10x its value is a count
        total = sum(float(bins[t, trace]) * 10 for t in own)
        if abs(total - round(total)) > 1e-6:
            sys.exit(f"{trace}: bins add up to {total} requests")
        requests[trace] = round(total)
    with open(os.path.join(out_dir, "trace_arrivals.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t"] + list(TRACES.values()))
        for t in ts:
            w.writerow([t] + [bins.get((t, tr), "") for tr in TRACES.values()])

    # results: every system has every metric except FT for serving alone
    cols = [f"{s}_{m}" for m in METRICS.values() for s in SYSTEMS.values()
            if not (s == "alone" and m == "ft")]
    if len(results) != len(cols) * len(TRACES):
        sys.exit(f"expected {len(cols) * len(TRACES)} results, got {len(results)}")
    with open(os.path.join(out_dir, "trace_results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["trace", "requests", "mean_req_per_s"] + cols)
        for trace in TRACES.values():
            w.writerow([trace, requests[trace], means[trace]]
                       + [results[trace, c] for c in cols])


if __name__ == "__main__":
    main()
