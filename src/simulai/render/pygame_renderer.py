from __future__ import annotations

import pygame

from simulai.agents.simulite import Simulite
from simulai.environment.resources import Food

BG_COLOR = (18, 18, 24)
GRID_COLOR = (50, 50, 70)
FOOD_COLOR = (80, 200, 120)
TEXT_COLOR = (220, 220, 230)
HUD_BG = (28, 28, 36)
GRAPH_COLOR = (100, 220, 140)
GRAPH_BORDER = (90, 90, 110)

ZONE_COLORS = {
    "forest": (34, 68, 46),
    "plains": (92, 86, 52),
    "desert": (120, 94, 58),
}

GENERATION_COLORS = [
    (120, 220, 255),  # Gen 0
    (120, 255, 180),  # Gen 1
    (190, 140, 255),  # Gen 2
    (255, 180, 100),  # Gen 3
    (255, 120, 180),  # Gen 4
    (180, 255, 120),  # Gen 5
]

VISOR_COLOR = (235, 245, 255)
CORE_COLOR = (255, 255, 255)
OUTLINE_COLOR = (15, 15, 20)

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

        self._draw_zones(world)
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

    def _zone_polygon_to_screen_points(
        self,
        polygon: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        return [
            (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2) for x, y in polygon
        ]

    def _draw_zones(self, world) -> None:
        for zone in world.food_zones:
            color = ZONE_COLORS.get(zone["name"], (60, 60, 60))
            points = self._zone_polygon_to_screen_points(zone["polygon"])
            if len(points) >= 3:
                pygame.draw.polygon(self.screen, color, points)

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

        pygame.draw.circle(
            self.screen,
            (180, 255, 200),
            (cx, cy),
            max(2, CELL_SIZE // 10),
        )

    def _generation_color(self, generation: int) -> tuple[int, int, int]:
        return GENERATION_COLORS[generation % len(GENERATION_COLORS)]

    def _draw_agent(self, agent: Simulite) -> None:
        color = self._generation_color(agent.generation)

        cx = agent.x * CELL_SIZE + CELL_SIZE // 2
        cy = agent.y * CELL_SIZE + CELL_SIZE // 2

        # Back glow
        pygame.draw.circle(self.screen, color, (cx, cy), 12, 1)

        # Head
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (cx, cy - 10), 6)
        pygame.draw.circle(self.screen, color, (cx, cy - 10), 5)

        # Visor
        visor_rect = pygame.Rect(cx - 4, cy - 12, 8, 4)
        pygame.draw.rect(self.screen, VISOR_COLOR, visor_rect, border_radius=2)

        # Torso
        torso_points = [
            (cx, cy - 4),
            (cx + 6, cy + 6),
            (cx, cy + 14),
            (cx - 6, cy + 6),
        ]
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, torso_points)

        inner_torso_points = [
            (cx, cy - 3),
            (cx + 5, cy + 6),
            (cx, cy + 13),
            (cx - 5, cy + 6),
        ]
        pygame.draw.polygon(self.screen, color, inner_torso_points)

        # Core light
        pygame.draw.circle(self.screen, CORE_COLOR, (cx, cy + 5), 2)

        # Arms
        pygame.draw.line(self.screen, color, (cx - 3, cy + 2), (cx - 9, cy + 7), 2)
        pygame.draw.line(self.screen, color, (cx + 3, cy + 2), (cx + 9, cy + 7), 2)

        # Legs
        pygame.draw.line(self.screen, color, (cx - 2, cy + 13), (cx - 7, cy + 20), 2)
        pygame.draw.line(self.screen, color, (cx + 2, cy + 13), (cx + 7, cy + 20), 2)

        # Small shoulder accents
        pygame.draw.circle(self.screen, VISOR_COLOR, (cx - 5, cy + 1), 1)
        pygame.draw.circle(self.screen, VISOR_COLOR, (cx + 5, cy + 1), 1)

        label = self.small_font.render(f"G{agent.generation}", True, TEXT_COLOR)
        self.screen.blit(label, (cx - 10, cy + 21))

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
