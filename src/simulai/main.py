from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Any

from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.render.pygame_renderer import PygameRenderer

DEFAULT_SIM_TICKS = 800
DEFAULT_FPS = 5
OUTPUTS_DIR = Path("outputs")
HISTORY_CSV = OUTPUTS_DIR / "simulation_history.csv"
SUMMARY_CSV = OUTPUTS_DIR / "simulation_metrics.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one SimulAI ecosystem simulation.")
    parser.add_argument(
        "--ticks",
        type=int,
        default=DEFAULT_SIM_TICKS,
        help="Number of simulation ticks to run.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=DEFAULT_FPS,
        help="Renderer FPS when visualization is enabled.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without opening the pygame renderer.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible runs.",
    )
    return parser.parse_args()


def build_world() -> World:
    grid = Grid(10, 10)
    world = World(grid)

    a = Simulite("A", 2, 2, traits=Traits(curiosity=4, sociability=7))
    b = Simulite("B", 7, 7, traits=Traits(curiosity=6, sociability=5))

    world.add_agent(a)
    world.add_agent(b)

    world.sprinkle_food(count=12)
    return world


def ensure_outputs_dir() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def as_number(value: Any) -> float | int | str:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


def safe_stat(stats: dict[str, Any], key: str, default: float = 0.0) -> float | int | str:
    return as_number(stats.get(key, default))


def build_history_row(world: World) -> dict[str, Any]:
    stats = world.get_dashboard_stats()
    living_agents = world.living_agents()
    dead_agents = world.dead_agents()

    row = {
        "tick": world.tick_count,
        "population": len(living_agents),
        "living_agents": len(living_agents),
        "dead_agents": len(dead_agents),
        "births": safe_stat(stats, "births", 0.0),
        "deaths": safe_stat(stats, "deaths", 0.0),
        "max_generation": safe_stat(stats, "max_generation", 0.0),
    }

    optional_keys = [
        "generation_limit",
        "average_age_at_death",
        "food_on_grid",
        "chips_on_grid",
        "weather",
        "avg_life_force",
        "average_life_force",
        "avg_health",
        "average_health",
        "avg_energy",
        "average_energy",
        "avg_nutrition",
        "average_nutrition",
        "avg_rest",
        "average_rest",
        "avg_exercise",
        "average_exercise",
        "avg_social",
        "average_social",
        "avg_speed",
        "average_speed",
        "avg_agility",
        "average_agility",
        "stability",
        "status",
    ]

    for key in optional_keys:
        if key in stats:
            row[key] = as_number(stats[key])

    return row


def write_history_csv(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        return

    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(
    world: World,
    stats: dict[str, Any],
    path: Path,
    ticks_requested: int,
    seed: int | None,
) -> None:
    living_agents = world.living_agents()
    dead_agents = world.dead_agents()

    summary_row = {
        "seed": "" if seed is None else seed,
        "ticks_requested": ticks_requested,
        "ticks_recorded": world.tick_count,
        "final_population": len(living_agents),
        "living_agents": len(living_agents),
        "dead_agents": len(dead_agents),
        "total_births": safe_stat(stats, "births", 0.0),
        "total_deaths": safe_stat(stats, "deaths", 0.0),
        "max_generation": safe_stat(stats, "max_generation", 0.0),
    }

    optional_keys = [
        "generation_limit",
        "average_age_at_death",
        "food_on_grid",
        "chips_on_grid",
        "weather",
        "avg_life_force",
        "average_life_force",
        "avg_health",
        "average_health",
        "avg_energy",
        "average_energy",
        "avg_nutrition",
        "average_nutrition",
        "avg_rest",
        "average_rest",
        "avg_exercise",
        "average_exercise",
        "avg_social",
        "average_social",
        "avg_speed",
        "average_speed",
        "avg_agility",
        "average_agility",
        "stability",
        "status",
    ]

    for key in optional_keys:
        if key in stats:
            summary_row[key] = as_number(stats[key])

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_row.keys()))
        writer.writeheader()
        writer.writerow(summary_row)


def main() -> None:
    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    ensure_outputs_dir()

    world = build_world()
    renderer = None if args.headless else PygameRenderer(world.grid.width, world.grid.height)

    history_rows: list[dict[str, Any]] = []

    for _ in range(args.ticks):
        world.step()
        if renderer is not None:
            renderer.render(world, fps=args.fps)

        history_rows.append(build_history_row(world))

    stats = world.get_dashboard_stats()

    write_history_csv(history_rows, HISTORY_CSV)
    write_summary_csv(
        world=world,
        stats=stats,
        path=SUMMARY_CSV,
        ticks_requested=args.ticks,
        seed=args.seed,
    )

    print("Simulation complete.")
    print(f"History CSV: {HISTORY_CSV}")
    print(f"Summary CSV: {SUMMARY_CSV}")
    print(f"Ticks: {world.tick_count}")
    print(f"Living agents: {len(world.living_agents())}")
    print(f"Dead agents: {len(world.dead_agents())}")
    print(f"Births: {stats['births']}")
    print(f"Max generation: {stats['max_generation']}")
    print()
    print(world.summary())

    if world.deaths_by_cause:
        print()
        print(f"Deaths by cause: {world.deaths_by_cause}")


if __name__ == "__main__":
    main()
