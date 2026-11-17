# Evaluation figures (§6)

Generated from `/mnt/nfs/home/ramya/BubbleTea-results/eval` (updated 2026-10-16); each script
writes one PNG and one CSV with exactly the values plotted. The figures of `../sections/evaluation.tex`
are now drawn with pgfplots from `../plots/`, with their data reshaped into `../plots/CSVs/`; their
original PNGs and CSVs were removed (`../sections/dump.tex`, commented out, still names some of them).

| Figure (evaluation.tex) | Files | Script (in BubbleTea-results/eval) |
|---|---|---|
| fig:eval-e2e-tput (body: Qwen3, 4k-32k) and fig:appx-e2e-tput (Appendix B.1: 3 models x 1k-32k); LLMStation, naive colocation (40% MPS cap), BubbleTea | drawn by `../plots/ft_throughput_qwen3.tex` and `../plots/ft_throughput.tex` from `../plots/CSVs/ft_throughput.csv` | `s62/v4/collect_v4.py` (s62.json; s62_tt40.json with `TT_RUNS=naive_torchtune/runs_cap40`), then `../plots/scripts/make_e2e_csvs.py` |
| fig:eval-e2e-lat / fig:appx-e2e-lat, p90 TTFT / TPOT relative to serving alone, same systems and split | drawn by `../plots/e2e_latency_qwen3.tex` and `../plots/e2e_latency.tex` from `../plots/CSVs/e2e_latency.csv` | as above (`make_e2e_csvs.py`) |
| fig:appx-naive-tput / fig:appx-naive-lat (Appendix B.2), naive colocation at 6% / 40% / no MPS cap | drawn by `../plots/naive_sweep_{tput,lat}.tex` from `../plots/CSVs/naive_sweep.csv` | `make_e2e_csvs.py` (s62.json, s62_tt40.json, s62_ttuncapped.json) |
| fig:eval-traces, Azure code / conversation | drawn by `../plots/trace.tex` from `../plots/CSVs/trace_{arrivals,results}.csv` | `s62/collect_trace_v2.py` then `s62/v5/make_figs.py main`, split with `../plots/scripts/split_trace.py` |
| fig:eval-sources, steps A/B/E throughput | drawn by `../plots/sources.tex` from `../plots/CSVs/sources.csv` | `s63/v2/make_ladder.py` then `s63/v2/make_sources_latency.py`, reshaped with `../plots/scripts/reshape_sources.py` |
| fig:eval-bubble-use, 8k@2 bubble accounting + 8k@4 bubble growth | drawn by `../plots/bubble_supply.tex` from `../plots/CSVs/bubble_{accounting,growth}.csv` | `s65/breakdown.py` (bt_8k2.txt) then `s65/make_bubble_use.py`, split with `../plots/scripts/split_bubble_supply.py` |
| fig:eval-latency-ablation, steps B-E throughput / p90 TTFT / p90 TPOT | drawn by `../plots/latency_ablation.tex` from `../plots/CSVs/latency_ablation.csv` | `s63/v2/make_sources_latency.py`, reshaped with `../plots/scripts/reshape_latency_ablation.py` |
| fig:eval-eplb, throughput with/without EPLB and bubbles; latency vs serving alone with EPLB | drawn by `../plots/eplb.tex` from `../plots/CSVs/eplb.csv` | `s64/make_eplb.py` (fig64_eplb.csv) then `s64/make_eplb_v2.py`, reshaped with `../plots/scripts/reshape_eplb.py` |

Older figures, not used by evaluation.tex (the appendix ones are now drawn with pgfplots; their PNGs are unused):

| Figure | Files | Script (in BubbleTea-results/eval) |
|---|---|---|
| Qwen3 at TP=EP=2 | `fig62_4_tp2.{png,csv}` | `s62/v4/make_tp2.py` |
| mechanism ladder A-E | `fig63_ladder.{png,csv}` | `s63/v2/make_ladder.py` |
| EPLB (2x2 with bubble share) | `fig64_eplb.{png,csv}` | `s64/make_eplb.py` |
| fig:appx-sched-overhead (Appendix), scheduling overhead + hook cost | drawn by `../plots/sched_overhead.tex` from `../plots/CSVs/{sched_overhead,hook_cost}.csv`, reshaped from `fig66_sched_overhead.csv` and `fig66_hook_cost.csv` with `../plots/scripts/reshape_sched_overhead.py` | `s66/make_sched2.py` |
| fig:appx-capacity (Appendix), spare capacity: idle, decode, prefill bubbles (3 models, 1k-32k, 4 loads) | drawn by `../plots/capacity.tex` from `../plots/CSVs/capacity.csv`, reshaped from `fig_capacity.csv` with `../plots/scripts/reshape_capacity.py` | `s62/capacity/make_capacity.py` |
| fig:appx-overheads (Appendix), memory + accuracy | drawn by `../plots/overheads.tex` from `../plots/CSVs/{gpu_memory,training_loss}.csv`, split from `fig66_overheads.csv` with `../plots/scripts/split_overheads.py` | `s66/make_overheads.py` |
| fig:appx-mem-breakdown (Appendix), trainer memory breakdown | drawn by `../plots/mem_breakdown.tex` from `../plots/CSVs/mem_breakdown.csv`, reshaped from `fig66_mem_breakdown.csv` with `../plots/scripts/reshape_mem_breakdown.py` | `s66/make_membreak.py` |

Plots use `/mnt/nfs/home/ramya/deltaserve/.venv/bin/python`; `make_overheads.py` uses the DeltaServe-vLLM venv.
