from __future__ import annotations

class TextRenderer:
    def render(self, world):
        grid = world.grid
        lines = []
        for y in range(grid.height):
            row = []
            for x in range(grid.width):
                cell = grid.get(x, y)
                row.append("·" if cell is None else "S")  # S marks a Simulite
            lines.append(" ".join(row))
        print("\x1b[2J\x1b[H", end="")  # clear screen
        print(f"SimulAI — tick {world.tick}")
        print("\n".join(lines))
        if hasattr(world, "_last_log"):
            print("\n" + world._last_log)
