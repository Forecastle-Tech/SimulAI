from __future__ import annotations

import csv
from pathlib import Path


class MetricsExporter:
    def __init__(self, output_path: str = "outputs/simulation_metrics.csv", overwrite: bool = True):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
        self.overwrite = overwrite

        if self.overwrite and self.output_path.exists():
            self.output_path.unlink()

    def _initialize_file(self) -> None:
        if self._initialized:
            return

        with self.output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "tick",
                    "population",
                    "births",
                    "deaths",
                    "max_generation",
                    "trend",
                    "weather",
                ]
            )

        self._initialized = True

    def record(self, world) -> None:
        self._initialize_file()

        stats = world.get_dashboard_stats()

        with self.output_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    stats["ticks"],
                    stats["population"],
                    stats["births"],
                    stats["deaths"],
                    stats["max_generation"],
                    stats["trend"],
                    stats["weather_kind"],
                ]
            )
