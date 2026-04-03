from __future__ import annotations

import argparse
import csv
import math
import os
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunSummary:
    run_id: int
    seed: int
    ticks_recorded: int
    final_population: float
    peak_population: float
    minimum_population: float
    final_births: float
    final_deaths: float
    max_generation: float
    average_population: float
    average_births_per_tick: float
    average_deaths_per_tick: float
    extinct: int
    history_file: str
    summary_file: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the SimulAI ecosystem many times and summarize stability."
    )
    parser.add_argument("--runs", type=int, default=50, help="Number of runs.")
    parser.add_argument("--ticks", type=int, default=800, help="Ticks per run.")
    parser.add_argument(
        "--python",
        type=str,
        default=sys.executable,
        help="Python executable to use.",
    )
    parser.add_argument(
        "--module",
        type=str,
        default="simulai.main",
        help="Python module to run for each simulation.",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        default=Path("outputs/simulation_history.csv"),
        help="Per-tick history CSV produced by a single simulation run.",
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        default=Path("outputs/simulation_metrics.csv"),
        help="One-row summary CSV produced by a single simulation run.",
    )
    parser.add_argument(
        "--batch-dir",
        type=Path,
        default=Path("outputs/batch_analysis"),
        help="Directory where batch outputs will be stored.",
    )
    parser.add_argument(
        "--stable-min-survival-rate",
        type=float,
        default=0.90,
        help="Minimum survival rate for stability.",
    )
    parser.add_argument(
        "--stable-max-final-pop-cv",
        type=float,
        default=0.75,
        help="Maximum final population coefficient of variation for stability.",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.05,
        help="Small pause between runs.",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def try_parse_number(value: str) -> float | str:
    value = value.strip()
    if value == "":
        return value
    try:
        return float(value)
    except ValueError:
        return value


def read_csv_rows(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            parsed: dict[str, Any] = {}
            for key, value in row.items():
                if key is None:
                    continue
                parsed[key] = "" if value is None else try_parse_number(value)
            rows.append(parsed)
    return rows


def normalize_name(name: str) -> str:
    return name.strip().lower().replace("_", " ").replace("-", " ")


def detect_column(columns: list[str], candidates: list[str], label: str) -> str:
    normalized_map = {normalize_name(col): col for col in columns}
    for candidate in candidates:
        normalized_candidate = normalize_name(candidate)
        if normalized_candidate in normalized_map:
            return normalized_map[normalized_candidate]
    raise KeyError(f"Could not find a {label} column. Available columns: {columns}")


def numeric_series(rows: list[dict[str, Any]], column: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(column)
        if isinstance(value, (int, float)):
            values.append(float(value))
        else:
            raise ValueError(f"Column '{column}' contains a non-numeric value: {value!r}")
    return values


def summarize_run(
    run_id: int,
    seed: int,
    history_csv_path: Path,
    summary_csv_path: Path,
) -> RunSummary:
    rows = read_csv_rows(history_csv_path)
    if not rows:
        raise ValueError(f"History file is empty: {history_csv_path}")

    columns = list(rows[0].keys())

    tick_col = detect_column(columns, ["tick"], "tick")
    population_col = detect_column(
        columns,
        ["population", "living_agents", "living agents", "alive_agents", "alive agents"],
        "population",
    )
    births_col = detect_column(
        columns,
        ["births", "total_births", "total births"],
        "births",
    )
    deaths_col = detect_column(
        columns,
        ["deaths", "total_deaths", "total deaths"],
        "deaths",
    )
    generation_col = detect_column(
        columns,
        ["max_generation", "max generation", "generation"],
        "generation",
    )

    ticks = numeric_series(rows, tick_col)
    populations = numeric_series(rows, population_col)
    births = numeric_series(rows, births_col)
    deaths = numeric_series(rows, deaths_col)
    generations = numeric_series(rows, generation_col)

    final_population = populations[-1]
    peak_population = max(populations)
    minimum_population = min(populations)
    final_births = births[-1]
    final_deaths = deaths[-1]
    max_generation = max(generations)
    average_population = statistics.fmean(populations)
    average_births_per_tick = statistics.fmean(births)
    average_deaths_per_tick = statistics.fmean(deaths)
    extinct = int(final_population <= 0)

    return RunSummary(
        run_id=run_id,
        seed=seed,
        ticks_recorded=int(ticks[-1]),
        final_population=final_population,
        peak_population=peak_population,
        minimum_population=minimum_population,
        final_births=final_births,
        final_deaths=final_deaths,
        max_generation=max_generation,
        average_population=average_population,
        average_births_per_tick=average_births_per_tick,
        average_deaths_per_tick=average_deaths_per_tick,
        extinct=extinct,
        history_file=str(history_csv_path),
        summary_file=str(summary_csv_path),
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def stddev(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def coefficient_of_variation(values: list[float]) -> float:
    avg = mean(values)
    if math.isclose(avg, 0.0):
        return 0.0 if all(math.isclose(v, 0.0) for v in values) else float("inf")
    return stddev(values) / avg


def build_report(
    run_summaries: list[RunSummary],
    stable_min_survival_rate: float,
    stable_max_final_pop_cv: float,
) -> dict[str, float | int | str]:
    final_populations = [r.final_population for r in run_summaries]
    peak_populations = [r.peak_population for r in run_summaries]
    minimum_populations = [r.minimum_population for r in run_summaries]
    avg_populations = [r.average_population for r in run_summaries]
    generations = [r.max_generation for r in run_summaries]
    extinctions = sum(r.extinct for r in run_summaries)
    runs = len(run_summaries)
    survival_rate = (runs - extinctions) / runs if runs else 0.0
    cv_final_population = coefficient_of_variation(final_populations)

    stable = (
        survival_rate >= stable_min_survival_rate and cv_final_population <= stable_max_final_pop_cv
    )

    return {
        "runs": runs,
        "extinctions": extinctions,
        "survival_rate": survival_rate,
        "mean_final_population": mean(final_populations),
        "std_final_population": stddev(final_populations),
        "cv_final_population": cv_final_population,
        "min_final_population": min(final_populations) if final_populations else 0.0,
        "max_final_population": max(final_populations) if final_populations else 0.0,
        "mean_peak_population": mean(peak_populations),
        "mean_minimum_population": mean(minimum_populations),
        "mean_average_population": mean(avg_populations),
        "mean_max_generation": mean(generations),
        "stable_min_survival_rate": stable_min_survival_rate,
        "stable_max_final_pop_cv": stable_max_final_pop_cv,
        "stable_assessment": "STABLE" if stable else "UNSTABLE",
    }


def print_report(report: dict[str, float | int | str]) -> None:
    print("\n=== Batch Stability Summary ===")
    for key, value in report.items():
        print(f"{key}: {value}")


def main() -> None:
    args = parse_args()

    ensure_dir(args.batch_dir)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    batch_path = args.batch_dir / f"batch_{timestamp}"
    run_history_dir = batch_path / "run_history"
    run_summary_dir = batch_path / "run_summary"
    ensure_dir(batch_path)
    ensure_dir(run_history_dir)
    ensure_dir(run_summary_dir)

    run_summaries: list[RunSummary] = []

    print(f"Running {args.runs} simulations at {args.ticks} ticks each...")

    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = "src" if not existing_pythonpath else f"src;{existing_pythonpath}"

    for run_id in range(1, args.runs + 1):
        seed = run_id
        cmd = [
            args.python,
            "-m",
            args.module,
            "--ticks",
            str(args.ticks),
            "--headless",
            "--seed",
            str(seed),
        ]

        print(f"\n--- Run {run_id}/{args.runs} | seed={seed} ---")
        result = subprocess.run(cmd, check=False, env=env)

        if result.returncode != 0:
            raise RuntimeError(f"Run {run_id} failed with exit code {result.returncode}")

        if not args.history_file.exists():
            raise FileNotFoundError(f"Expected history file not found: {args.history_file}")

        if not args.summary_file.exists():
            raise FileNotFoundError(f"Expected summary file not found: {args.summary_file}")

        copied_history = run_history_dir / f"run_{run_id:03d}_seed_{seed}_history.csv"
        copied_summary = run_summary_dir / f"run_{run_id:03d}_seed_{seed}_summary.csv"

        shutil.copy2(args.history_file, copied_history)
        shutil.copy2(args.summary_file, copied_summary)

        summary = summarize_run(
            run_id=run_id,
            seed=seed,
            history_csv_path=copied_history,
            summary_csv_path=copied_summary,
        )
        run_summaries.append(summary)

        print(
            f"Ticks={summary.ticks_recorded}, "
            f"Final pop={summary.final_population:.2f}, "
            f"Peak pop={summary.peak_population:.2f}, "
            f"Min pop={summary.minimum_population:.2f}, "
            f"Max gen={summary.max_generation:.2f}, "
            f"Extinct={bool(summary.extinct)}"
        )

        time.sleep(args.pause_seconds)

    run_summary_csv = batch_path / "batch_run_summaries.csv"
    write_csv(run_summary_csv, [asdict(r) for r in run_summaries])

    report = build_report(
        run_summaries=run_summaries,
        stable_min_survival_rate=args.stable_min_survival_rate,
        stable_max_final_pop_cv=args.stable_max_final_pop_cv,
    )

    report_csv = batch_path / "batch_report.csv"
    write_csv(report_csv, [{"metric": k, "value": v} for k, v in report.items()])

    print_report(report)
    print(f"\nSaved run summaries to: {run_summary_csv}")
    print(f"Saved batch report to: {report_csv}")


if __name__ == "__main__":
    main()
