import os
import time
import tracemalloc
from collections import deque

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ATTRACTIONS_PATH = "input_data/Barcelona_20_Attractions_With_Importance.xlsx"
TIMES_PATH = "input_data/Barcelona_Times_20_Attractions.xlsx"
OUTPUT_DIR = "results"
CATEGORIES = ["History", "Art", "Architecture", "Nature", "Local Culture", "Views", "Religion", "Science"]
TRAVEL_SHEETS = {"walking": "Walking", "transit": "Public transport"}

STARTS = None
MODES = ["walking", "transit"]
LAMBDAS = [0.0, 0.5, 1.0]
BUDGETS = {"short": 120, "half-day": 240, "full-day": 480}

PROFILES = {
    "History": {"History": 5, "Art": 2, "Architecture": 3, "Nature": 1, "Local Culture": 2,
                "Views": 1, "Religion": 3, "Science": 1},
    "Architecture": {"History": 2, "Art": 3, "Architecture": 5, "Nature": 1, "Local Culture": 1,
                     "Views": 2, "Religion": 2, "Science": 1},
    "Nature and views": {"History": 1, "Art": 1, "Architecture": 1, "Nature": 5, "Local Culture": 2,
                         "Views": 5, "Religion": 0, "Science": 3},
    "Art and culture": {"History": 2, "Art": 5, "Architecture": 2, "Nature": 1, "Local Culture": 5,
                        "Views": 1, "Religion": 0, "Science": 0},
    "Balanced": {c: 3 for c in CATEGORIES},
}

ALGORITHM_COLORS = {"Greedy": "#0072B2", "DFS": "#D55E00"}


def load_data(attractions_path=ATTRACTIONS_PATH, times_path=TIMES_PATH, mode="walking"):
    attractions = pd.read_excel(attractions_path).set_index("Attraction")
    travel = pd.read_excel(times_path, sheet_name=TRAVEL_SHEETS[mode], index_col=0)
    travel = travel.loc[attractions.index, attractions.index]
    return attractions, travel.to_numpy(dtype=float)


def compute_scores(attractions, preferences, lam=0.5):
    weights = np.array([preferences[c] for c in CATEGORIES], dtype=float)
    x = attractions[CATEGORIES].to_numpy(dtype=float)
    interest = (x @ weights) / (5 * x.sum(axis=1))

    def minmax(values):
        values = np.asarray(values, dtype=float)
        return (values - values.min()) / (values.max() - values.min())

    quality = 0.5 * minmax(attractions["Rating /5"]) + 0.5 * minmax(attractions["Importance /5"])
    return 100 * interest * (1 - lam + lam * quality)


def make_expansion(scores, visit, travel, budget):
    n = len(scores)

    def expand(w):
        route, elapsed, score, _ = w
        last = route[-1]
        children = []
        for j in range(n):
            if j in route:
                continue
            cost = travel[last, j] + visit[j]
            if elapsed + cost > budget:
                continue
            children.append((route + (j,), elapsed + cost, score + scores[j], scores[j] / cost))
        return children

    return expand


def goal_cost(w):
    return (-w[2], w[1])


def merge_dfs(working_set, children):
    working_set.extendleft(reversed(children))
    return working_set


def merge_greedy(working_set, children):
    if children:
        working_set.append(max(children, key=lambda child: child[3]))
    return working_set


def search(initial, expand, merge):
    working_set = deque([initial])
    best = initial
    nodes = 0
    while working_set:
        w = working_set.popleft()
        nodes += 1
        if goal_cost(w) < goal_cost(best):
            best = w
        working_set = merge(working_set, expand(w))
    return best, nodes


def run_search(merge, scores, visit, travel, start, budget):
    t0 = time.perf_counter()
    best, nodes = (((), 0.0, 0.0, 0.0), 0)
    if visit[start] <= budget:
        initial = ((start,), visit[start], scores[start], 0.0)
        best, nodes = search(initial, make_expansion(scores, visit, travel, budget), merge)
    return {"route": list(best[0]), "score": best[2], "time": best[1],
            "nodes_expanded": nodes, "runtime": time.perf_counter() - t0}


def greedy_search(scores, visit, travel, start, budget):
    return run_search(merge_greedy, scores, visit, travel, start, budget)


def dfs_search(scores, visit, travel, start, budget):
    return run_search(merge_dfs, scores, visit, travel, start, budget)


def route_time(route, visit, travel):
    return visit[route[0]] + sum(travel[i, j] + visit[j] for i, j in zip(route, route[1:]))


def measure_peak_memory(algorithm, scores, visit, travel, start, budget):
    tracemalloc.start()
    algorithm(scores, visit, travel, start, budget)
    peak = tracemalloc.get_traced_memory()[1] / 1024
    tracemalloc.stop()
    return peak


def run_scenarios(data, profiles, budgets, lambdas, modes, starts=None):
    algorithms = {"Greedy": greedy_search, "DFS": dfs_search}
    memory = {}
    rows = []

    for mode in modes:
        attractions, travel = data[mode]
        names = list(attractions.index)
        visit = attractions["Visiting time (min)"].to_numpy(dtype=float)

        for start_name in (starts or names):
            print(f"{mode} | {start_name}", flush=True)
            start = names.index(start_name)

            for budget_name, budget in budgets.items():
                for lam in lambdas:
                    for profile, preferences in profiles.items():
                        scores = compute_scores(attractions, preferences, lam)
                        scenario_rows = []
                        for algorithm_name, algorithm in algorithms.items():
                            result = algorithm(scores, visit, travel, start, budget)
                            key = (mode, start_name, budget, algorithm_name)
                            if key not in memory:
                                memory[key] = measure_peak_memory(algorithm, scores, visit, travel, start, budget)
                            used = route_time(result["route"], visit, travel)
                            scenario_rows.append({
                                "mode": mode,
                                "start": start_name,
                                "profile": profile,
                                "lam": lam,
                                "budget_name": budget_name,
                                "budget_min": budget,
                                "algorithm": algorithm_name,
                                "score": result["score"],
                                "time_used_min": used,
                                "budget_used_pct": 100 * used / budget,
                                "within_budget": used <= budget,
                                "n_attractions": len(result["route"]),
                                "nodes_expanded": result["nodes_expanded"],
                                "runtime_s": result["runtime"],
                                "peak_memory_kb": memory[key],
                                "route": " > ".join(names[i] for i in result["route"]),
                            })
                        optimal = max(r["score"] for r in scenario_rows)
                        for r in scenario_rows:
                            r["gap_to_best_pct"] = 100 * (optimal - r["score"]) / optimal if optimal > 0 else 0.0
                        rows.extend(scenario_rows)
    return pd.DataFrame(rows)


def summarize(results, factor):
    greedy = results[results["algorithm"] == "Greedy"].groupby(factor, sort=False)
    dfs = results[results["algorithm"] == "DFS"].groupby(factor, sort=False)
    return pd.DataFrame({
        "greedy_mean_gap_pct": greedy["gap_to_best_pct"].mean(),
        "greedy_max_gap_pct": greedy["gap_to_best_pct"].max(),
        "greedy_optimal_pct": greedy["gap_to_best_pct"].apply(lambda g: 100 * (g < 1e-9).mean()),
        "dfs_mean_nodes": dfs["nodes_expanded"].mean(),
        "dfs_mean_runtime_s": dfs["runtime_s"].mean(),
    })


def grouped_bars(ax, table, colors, ylabel, log_scale=False):
    x = np.arange(len(table))
    width = 0.8 / len(table.columns)
    for k, (column, color) in enumerate(zip(table.columns, colors)):
        offset = (k - (len(table.columns) - 1) / 2) * width
        ax.bar(x + offset, table[column], width, label=str(column), color=color)
    ax.set_xticks(x)
    ax.set_xticklabels([str(i) for i in table.index], rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    if log_scale:
        ax.set_yscale("log")
    ax.set_ylim(top=ax.get_ylim()[1] * (5 if log_scale else 1.2))
    ax.legend(frameon=False, loc="upper left", ncol=len(table.columns))


def plot_results(results, path_stem):
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "axes.spines.top": False,
                         "axes.spines.right": False})
    palette = ["#0072B2", "#D55E00", "#009E73"]
    budget_order = list(BUDGETS)
    greedy = results[results["algorithm"] == "Greedy"]
    dfs = results[results["algorithm"] == "DFS"]

    def pivot(frame, index, columns, values, index_order, column_order):
        table = frame.pivot_table(index=index, columns=columns, values=values, aggfunc="mean")
        return table.loc[index_order, column_order]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    grouped_bars(axes[0, 0], pivot(greedy, "profile", "budget_name", "gap_to_best_pct",
                                   list(PROFILES), budget_order), palette,
                 "Greedy gap to best score (%)")
    grouped_bars(axes[0, 1], pivot(greedy, "lam", "mode", "gap_to_best_pct",
                                   LAMBDAS, MODES), palette, "Greedy gap to best score (%)")
    grouped_bars(axes[0, 2], pivot(results, "budget_name", "algorithm", "budget_used_pct",
                                   budget_order, ["Greedy", "DFS"]), palette[:2],
                 "Time budget used (%)")
    grouped_bars(axes[1, 0], pivot(dfs, "budget_name", "mode", "nodes_expanded",
                                   budget_order, MODES), palette, "DFS nodes expanded", log_scale=True)
    grouped_bars(axes[1, 1], pivot(dfs, "budget_name", "mode", "runtime_s",
                                   budget_order, MODES), palette, "DFS runtime (s)", log_scale=True)
    grouped_bars(axes[1, 2], pivot(results, "budget_name", "algorithm", "peak_memory_kb",
                                   budget_order, ["Greedy", "DFS"]), palette[:2], "Peak memory (KiB)")
    axes[0, 0].set_xlabel("User profile")
    axes[0, 1].set_xlabel("Lambda")
    for ax in axes.ravel()[2:]:
        ax.set_xlabel("Time budget")
    fig.tight_layout()
    fig.savefig(f"{path_stem}.pdf")
    fig.savefig(f"{path_stem}.png", dpi=300)
    plt.close(fig)


def main():
    data = {mode: load_data(mode=mode) for mode in MODES}
    results = run_scenarios(data, PROFILES, BUDGETS, LAMBDAS, MODES, STARTS)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results.to_csv(os.path.join(OUTPUT_DIR, "results.csv"), index=False)
    plot_results(results, os.path.join(OUTPUT_DIR, "performance"))

    greedy = results[results["algorithm"] == "Greedy"]
    print(f"\nScenarios: {len(greedy)} | Runs: {len(results)}")
    print(f"Runs exceeding the time budget: {int((~results['within_budget']).sum())}")
    print(f"Greedy optimal in {100 * (greedy['gap_to_best_pct'] < 1e-9).mean():.1f}% of scenarios | "
          f"mean gap {greedy['gap_to_best_pct'].mean():.2f}% | max gap {greedy['gap_to_best_pct'].max():.2f}%")

    for factor in ["profile", "budget_name", "mode", "lam"]:
        print(f"\nBy {factor}")
        print(summarize(results, factor).round(4).to_string())

    print("\nStarting attractions with the largest Greedy gap")
    print(summarize(results, "start").sort_values("greedy_mean_gap_pct", ascending=False).head(5).round(4).to_string())


if __name__ == "__main__":
    main()
