from __future__ import annotations

from simulai.agents.simulite import Simulite
from simulai.environment.resources import Food

MOOD_EMOJI = {
    -3: "😤",
    -2: "🙁",
    -1: "😐",
    0: "🙂",
    1: "😄",
    2: "🤩",
    3: "🧠",
}

WEATHER_ICON = {
    "clear": "☀️",
    "breezy": "🍃",
    "cloudy": "☁️",
    "rain": "🌧️",
    "storm": "⛈️",
}


class TextRenderer:
    def symbol_for(self, cell):
        if cell is None:
            return "·"
        if isinstance(cell, Food):
            return "F"
        if isinstance(cell, Simulite):
            return "S"
        return "?"

    def render(self, world):
        grid = world.grid
        lines = []
        for y in range(grid.height):
            row = []
            for x in range(grid.width):
                cell = grid.get(x, y)
                row.append(self.symbol_for(cell))
            lines.append(" ".join(row))

        print("\x1b[2J\x1b[H", end="")  # clear screen
        w = getattr(world, "weather", None)
        if w:
            w_icon = WEATHER_ICON.get(w.kind, "❓")
            print(f"SimulAI — tick {world.tick}   Weather: {w_icon} {w.kind} ({w.duration})")
        else:
            print(f"SimulAI — tick {world.tick}")
