from __future__ import annotations
from simulai.environment.resources import Food
from simulai.agents.simulite import Simulite

MOOD_EMOJI = {
    -3: "😤",
    -2: "🙁",
    -1: "😐",
     0: "🙂",
     1: "😄",
     2: "🤩",
     3: "🧠",
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
        print(f"SimulAI — tick {world.tick}")
        print("\n".join(lines))
        if hasattr(world, "_last_log"):
            mood_score = getattr(world, "_last_mood", 0)
            # clamp mood to -3..3 for display
            mood_key = max(-3, min(3, int(mood_score)))
            emoji = MOOD_EMOJI.get(mood_key, "🙂")
            print(f"\n{world._last_log}  {emoji}")
