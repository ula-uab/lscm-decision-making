"""Runs the experiment and writes its results in results/.

30 runs of each method on each case, with seeds 1 to 30, and the same budget of
evaluations for every method on a case. The shortest route of each case is
computed exactly first (exact.py). The runs are spread over the processor
cores; each run depends only on its seed, so the results do not depend on how
many cores are used.

Run from the root of the repository:

    uv run --with deap==1.4.4 python cases/traveling_salesman/experiments/run_experiment.py

Options: --cases ivanov14 random20 (some cases only), --runs 5, --workers 4.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import exact  # noqa: E402
import instances  # noqa: E402
import methods  # noqa: E402

# Budget of evaluations of each case: about 100 local searches from a random route
BUDGET = {"ivanov14": 85_000, "random20": 300_000, "random30": 1_000_000, "random50": 5_400_000}
RUNS = 30
RESULTS = HERE / "results"


def _task(args):
    case, method, seed = args
    result = methods.run(method, instances.case(case), BUDGET[case], seed)
    result["case"] = case
    return result


def _route_length(d, route):
    return sum(d[a][b] for a, b in zip(route, route[1:] + route[:1]))


def summary(rows: list[dict], optimum: int) -> list[dict]:
    """One row per method: runs that reach the shortest route (%), mean and
    largest gap to it (%), mean evaluations used and mean CPU time (s)."""
    out = []
    for method in methods.METHODS:
        mine = [r for r in rows if r["method"] == method]
        gaps = [100 * (r["best"] - optimum) / optimum for r in mine]
        out.append({"method": method, "runs": len(mine),
                    "reach": 100 * sum(r["best"] == optimum for r in mine) / len(mine),
                    "mean_gap": sum(gaps) / len(gaps), "max_gap": max(gaps),
                    "evaluations": sum(r["evaluations"] for r in mine) / len(mine),
                    "seconds": sum(r["seconds"] for r in mine) / len(mine)})
    return out


def markdown(case: str, n: int, optimum: int, table: list[dict]) -> str:
    lines = [f"### {case}: {n} cities, shortest route {optimum:,}, budget {BUDGET[case]:,} evaluations", "",
             "| Method | Runs that reach the shortest route (%) | Mean gap (%) | Largest gap (%) "
             "| Mean evaluations | Mean CPU time (s) |",
             "|---|---|---|---|---|---|"]
    for t in table:
        lines.append(f"| {t['method']} | {t['reach']:.0f} | {t['mean_gap']:.2f} | {t['max_gap']:.2f} "
                     f"| {t['evaluations']:,.0f} | {t['seconds']:.2f} |")
    return "\n".join(lines) + "\n"


def curve_figure(rows: list[dict], optimum: int, budget: int, path: Path) -> None:
    """Mean over the runs of the shortest length found against the evaluations
    made, one line per method (log scale for the evaluations)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    grid = np.unique(np.geomspace(1, budget, 400).astype(int))
    # With the same seed, LS1, LSR and MA-ER start from the same random route, and
    # MA-ER makes the same local searches as LSR for its initial population, so
    # their curves coincide at first: width, dashes and order keep the three visible
    style = {"LS1": (0, (1, 2)), "LSR": "-", "MA-ER": (0, (4, 3)), "GA-KF": "-", "GA-ER": "-", "GA-OX": "-"}
    width = {"LS1": 2.0, "LSR": 4.0, "MA-ER": 2.0}
    order = {"LS1": 5, "LSR": 3, "MA-ER": 4}
    fig, ax = plt.subplots(figsize=(8, 5))
    for method in methods.METHODS:
        runs = [r for r in rows if r["method"] == method]
        end = max(r["evaluations"] for r in runs)
        xs = grid[grid <= end]
        curves = []
        for r in runs:
            evals = [e for e, _ in r["curve"]]
            lengths = [v for _, v in r["curve"]]
            idx = np.searchsorted(evals, xs, side="right") - 1
            curves.append(np.array(lengths)[idx])
        ax.plot(xs, np.mean(curves, axis=0), label=method, linestyle=style[method],
                linewidth=width.get(method, 1.5), zorder=order.get(method, 2))
    ax.axhline(optimum, color="black", linestyle="--", linewidth=0.8, label=f"Shortest route ({optimum:,})")
    ax.set_xscale("log")
    ax.set_xlim(10, budget * 1.2)
    ax.set_ylim(optimum - 20, 2_300)
    ax.set_xlabel("Routes evaluated (lengths and moves)")
    ax.set_ylabel("Shortest length found, mean of 30 runs (km)")
    ax.set_title("14 cities of Ivanov et al. (2025): shortest length found against routes evaluated")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cases", nargs="+", default=list(instances.CASES))
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    parser.add_argument("--figure", action="store_true",
                        help="only draw the curve again from results/curves_ivanov14.json")
    args = parser.parse_args()
    if args.figure:
        rows = json.loads((RESULTS / "curves_ivanov14.json").read_text())
        curve_figure(rows, exact.shortest(instances.ivanov14())["length"], BUDGET["ivanov14"],
                     RESULTS / "curve_ivanov14.png")
        return
    RESULTS.mkdir(exist_ok=True)

    optimum = {}
    with open(RESULTS / "shortest_routes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "cities", "length", "rounds", "subtour_constraints", "seconds", "route"])
        for case in args.cases:
            r = exact.shortest(instances.case(case))
            optimum[case] = r["length"]
            w.writerow([case, len(r["route"]), r["length"], r["rounds"], r["cuts"], f"{r['seconds']:.2f}",
                        " ".join(map(str, r["route"]))])
            print(f"{case}: shortest route {r['length']:,} ({r['rounds']} rounds, {r['seconds']:.1f} s)", flush=True)

    tasks = [(c, m, s) for c in reversed(args.cases) for m in methods.METHODS for s in range(1, args.runs + 1)]
    start = time.time()
    with Pool(args.workers) as pool:
        results = []
        for k, r in enumerate(pool.imap_unordered(_task, tasks), 1):
            results.append(r)
            if k % 30 == 0:
                print(f"{k}/{len(tasks)} runs, {time.time() - start:.0f} s", flush=True)
    results.sort(key=lambda r: (args.cases.index(r["case"]), methods.METHODS.index(r["method"]), r["seed"]))

    text = ["# Results", ""]
    for case in args.cases:
        d = instances.case(case)
        rows = [r for r in results if r["case"] == case]
        for r in rows:  # every route found is a route of the case, with the length reported
            assert sorted(r["route"]) == list(range(len(d))) and _route_length(d, r["route"]) == r["best"]
            assert r["best"] >= optimum[case]
        text.append(markdown(case, len(d), optimum[case], summary(rows, optimum[case])))
    (RESULTS / "summary.md").write_text("\n".join(text))
    with open(RESULTS / "runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "method", "seed", "best", "evaluations", "seconds", "route"])
        for r in results:
            w.writerow([r["case"], r["method"], r["seed"], r["best"], r["evaluations"], f"{r['seconds']:.3f}",
                        " ".join(map(str, r["route"]))])
    if "ivanov14" in args.cases:
        rows = [r for r in results if r["case"] == "ivanov14"]
        (RESULTS / "curves_ivanov14.json").write_text(json.dumps(
            [{"method": r["method"], "seed": r["seed"], "evaluations": r["evaluations"], "curve": r["curve"]}
             for r in rows]))
        curve_figure(rows, optimum["ivanov14"], BUDGET["ivanov14"], RESULTS / "curve_ivanov14.png")
    print("\n".join(text))
    print(f"Total time: {time.time() - start:.0f} s")


if __name__ == "__main__":
    main()
