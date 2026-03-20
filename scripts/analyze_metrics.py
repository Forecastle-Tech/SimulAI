from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

INPUT_CSV = Path("outputs/simulation_metrics.csv")
OUTPUT_DIR = Path("outputs/analysis")


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Metrics file not found: {INPUT_CSV}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)

    if df.empty:
        raise ValueError("The metrics CSV is empty.")

    print("\n=== Simulation Metrics Summary ===")
    print(f"Rows: {len(df)}")
    print(f"Ticks recorded: {df['tick'].min()} to {df['tick'].max()}")
    print(f"Final population: {df['population'].iloc[-1]}")
    print(f"Peak population: {df['population'].max()}")
    print(f"Minimum population: {df['population'].min()}")
    print(f"Final births: {df['births'].iloc[-1]}")
    print(f"Final deaths: {df['deaths'].iloc[-1]}")
    print(f"Max generation reached: {df['max_generation'].max()}")

    df["population_change"] = df["population"].diff().fillna(0)
    df["births_per_tick"] = df["births"].diff().fillna(df["births"])
    df["deaths_per_tick"] = df["deaths"].diff().fillna(df["deaths"])

    print(f"Average population: {df['population'].mean():.2f}")
    print(f"Average births per tick: {df['births_per_tick'].mean():.2f}")
    print(f"Average deaths per tick: {df['deaths_per_tick'].mean():.2f}")

    summary_path = OUTPUT_DIR / "summary_stats.csv"
    df.describe().to_csv(summary_path)

    plt.figure()
    plt.plot(df["tick"], df["population"])
    plt.title("Population Over Time")
    plt.xlabel("Tick")
    plt.ylabel("Population")
    plt.savefig(OUTPUT_DIR / "population.png")
    plt.close()

    plt.figure()
    plt.plot(df["tick"], df["births"], label="Births")
    plt.plot(df["tick"], df["deaths"], label="Deaths")
    plt.legend()
    plt.title("Births vs Deaths")
    plt.savefig(OUTPUT_DIR / "births_deaths.png")
    plt.close()

    print(f"\nSaved outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
