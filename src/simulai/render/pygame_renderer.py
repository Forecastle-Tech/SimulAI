from __future__ import annotations

import pygame

from simulai.agents.simulite import Simulite
from simulai.environment.resources import Food

BG_COLOR = (18, 18, 24)
GRID_COLOR = (50, 50, 70)
FOOD_COLOR = (80, 200, 120)
AGENT_COLOR = (120, 180, 255)
TEXT_COLOR = (220, 220, 230)
HUD_BG = (28, 28, 36)
GRAPH_COLOR = (100, 220, 140)
GRAPH_BORDER = (90, 90, 110)

CELL_SIZE = 40
HUD_HEIGHT = 170
PADDING = 8


class PygameRenderer:
    def __init__(self, width: int, height: int):
        pygame.init()
        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width * CELL_SIZE, height * CELL_SIZE + HUD_HEIGHT))
        pygame.display.set_caption("SimulAI")

        self.font = pygame.font.SysFont("consolas", 16)
        self.small_font = pygame.font.SysFont("consolas", 14)
        self.clock = pygame.time.Clock()

    def render(self, world, fps: int = 5) -> None:
        self._handle_events()

        self.screen.fill(BG_COLOR)

        self._draw_grid(world)
        self._draw_entities(world)
        self._draw_hud(world)

        pygame.display.flip()
        self.clock.tick(fps)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

    def _draw_grid(self, world) -> None:
        for y in range(world.grid.height):
            for x in range(world.grid.width):
                rect = pygame.Rect(
                    x * CELL_SIZE,
                    y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

    def _draw_entities(self, world) -> None:
        for y in range(world.grid.height):
            for x in range(world.grid.width):
                cell = world.grid.get(x, y)

                if isinstance(cell, Food):
                    self._draw_food(x, y)

                elif isinstance(cell, Simulite):
                    self._draw_agent(cell)

    def _draw_food(self, x: int, y: int) -> None:
        cx = x * CELL_SIZE + CELL_SIZE // 2
        cy = y * CELL_SIZE + CELL_SIZE // 2

        pygame.draw.circle(
            self.screen,
            FOOD_COLOR,
            (cx, cy),
            CELL_SIZE // 6,
        )

    def _draw_agent(self, agent: Simulite) -> None:
        x = agent.x * CELL_SIZE
        y = agent.y * CELL_SIZE

        rect = pygame.Rect(
            x + 6,
            y + 6,
            CELL_SIZE - 12,
            CELL_SIZE - 12,
        )

        pygame.draw.rect(self.screen, AGENT_COLOR, rect, border_radius=6)

        label = f"{agent.name[:3]} G{agent.generation}"
        text = self.font.render(label, True, TEXT_COLOR)

        self.screen.blit(text, (x + 4, y + 4))

    def _draw_population_graph(
        self,
        history: list[int],
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        border_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, GRAPH_BORDER, border_rect, 1)

        if len(history) < 2:
            return

        max_pop = max(history)
        min_pop = min(history)

        if max_pop == min_pop:
            max_pop += 1

        points: list[tuple[int, int]] = []
        for i, value in enumerate(history):
            px = x + int((i / max(1, len(history) - 1)) * (width - 1))
            py = y + height - 1 - int(((value - min_pop) / (max_pop - min_pop)) * (height - 1))
            points.append((px, py))

        if len(points) >= 2:
            pygame.draw.lines(self.screen, GRAPH_COLOR, False, points, 2)

    def _draw_hud(self, world) -> None:
        top = world.grid.height * CELL_SIZE

        hud_rect = pygame.Rect(
            0,
            top,
            world.grid.width * CELL_SIZE,
            HUD_HEIGHT,
        )
        pygame.draw.rect(self.screen, HUD_BG, hud_rect)

        stats = world.get_dashboard_stats()

        summary = world.summary()
        summary_surf = self.font.render(summary, True, TEXT_COLOR)
        self.screen.blit(summary_surf, (PADDING, top + PADDING))

        log = world._last_log or ""
        log_surf = self.font.render(log, True, TEXT_COLOR)
        self.screen.blit(log_surf, (PADDING, top + 28))

        dashboard_lines = [
            f"Population: {stats['population']}",
            f"Births: {stats['births']}",
            f"Deaths: {stats['deaths']}",
            f"Max Gen: {stats['max_generation']}",
            f"Ticks: {stats['ticks']}",
            f"Trend: {stats['trend']}",
        ]

        left_x = PADDING
        start_y = top + 55
        line_gap = 18

        for i, line in enumerate(dashboard_lines):
            surf = self.small_font.render(line, True, TEXT_COLOR)
            self.screen.blit(surf, (left_x, start_y + i * line_gap))

        graph_width = 220
        graph_height = 70
        graph_x = world.grid.width * CELL_SIZE - graph_width - PADDING
        graph_y = top + 55

        title_surf = self.small_font.render("Population Trend", True, TEXT_COLOR)
        self.screen.blit(title_surf, (graph_x, graph_y - 18))

        self._draw_population_graph(
            stats["population_history"],
            x=graph_x,
            y=graph_y,
            width=graph_width,
            height=graph_height,
        )
