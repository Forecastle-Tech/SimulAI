from __future__ import annotations

import pygame

from simulai.agents.simulite import Simulite
from simulai.environment.resources import Food

BG_COLOR = (18, 18, 24)
GRID_COLOR = (50, 50, 70)
FOOD_COLOR = (80, 200, 120)
HUD_BG_COLOR = (30, 30, 40)
HUD_TEXT_COLOR = (245, 245, 245)
PANEL_BG_COLOR = (24, 24, 32)
PANEL_BORDER_COLOR = (70, 70, 90)
PANEL_TITLE_COLOR = (255, 255, 255)
PANEL_TEXT_COLOR = (210, 210, 210)

MOOD_COLORS = {
    "happy": (80, 200, 120),
    "neutral": (240, 210, 90),
    "sad": (100, 160, 255),
    "angry": (220, 80, 80),
}


class PygameRenderer:
    def __init__(self, cell_size: int = 48, margin: int = 24, panel_width: int = 320):
        self.cell_size = cell_size
        self.margin = margin
        self.panel_width = panel_width

        self._initialized = False
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.tiny_font = None
        self.event_log: list[str] = []
        self._last_seen_log: str | None = None

    def _init(self, world):
        pygame.init()

        grid_width = world.grid.width * self.cell_size
        grid_height = world.grid.height * self.cell_size

        width = grid_width + self.margin * 3 + self.panel_width
        height = grid_height + self.margin * 2 + 100

        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("SimulAI Viewer")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.tiny_font = pygame.font.SysFont("arial", 12)

        self._initialized = True

    def close(self):
        if self._initialized:
            pygame.quit()
            self._initialized = False

    def _agent_color(self, agent: Simulite):
        mood = agent.mood

        if mood >= 1.5:
            return MOOD_COLORS["happy"]
        if mood <= -1.5:
            return MOOD_COLORS["angry"]
        if mood < 0:
            return MOOD_COLORS["sad"]
        return MOOD_COLORS["neutral"]

    def _mood_label(self, agent: Simulite) -> str:
        mood = agent.mood
        if mood >= 1.5:
            return "Happy"
        if mood <= -1.5:
            return "Angry"
        if mood < 0:
            return "Sad"
        return "Neutral"

    def _goal_label(self, agent: Simulite) -> str:
        goal = getattr(agent, "goal", None)
        if goal is None:
            return "Idle"
        name = getattr(goal, "name", None)
        return name or "Goal"

    def _memory_food_label(self, agent: Simulite) -> str:
        food_locations = getattr(agent.memory, "food_locations", [])
        if not food_locations:
            return "Food: none"

        recent = food_locations[-2:]
        formatted = " | ".join(f"{x},{y}" for x, y in recent)
        return f"Food: {formatted}"

    def _friend_label(self, agent: Simulite) -> str:
        affinity = getattr(agent.memory, "friend_affinity", {})
        if not affinity:
            return "Friend: none"

        best_name = None
        best_value = float("-inf")

        for name, value in affinity.items():
            if value > best_value:
                best_name = name
                best_value = value

        if best_name is None:
            return "Friend: none"

        return f"Friend: {best_name} ({best_value:+.1f})"

    def _grid_origin(self) -> tuple[int, int]:
        return self.margin, self.margin

    def _panel_origin(self, world) -> tuple[int, int]:
        panel_x = self.margin * 2 + world.grid.width * self.cell_size
        panel_y = self.margin
        return panel_x, panel_y

    def _update_event_log(self, world):
        log_text = getattr(world, "_last_log", "")
        if log_text and log_text != self._last_seen_log:
            entry = f"Tick {world.tick}: {log_text}"
            self.event_log.append(entry)
            self.event_log = self.event_log[-12:]
            self._last_seen_log = log_text

    def _draw_grid(self, world):
        origin_x, origin_y = self._grid_origin()

        for y in range(world.grid.height):
            for x in range(world.grid.width):
                rect = pygame.Rect(
                    origin_x + x * self.cell_size,
                    origin_y + y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pygame.draw.rect(self.screen, GRID_COLOR, rect, width=1)

    def _draw_food(self, x: int, y: int):
        origin_x, origin_y = self._grid_origin()

        cx = origin_x + x * self.cell_size + self.cell_size // 2
        cy = origin_y + y * self.cell_size + self.cell_size // 2

        pygame.draw.circle(self.screen, FOOD_COLOR, (cx, cy), self.cell_size // 6)

    def _draw_agent(self, agent: Simulite):
        origin_x, origin_y = self._grid_origin()

        x = origin_x + agent.x * self.cell_size
        y = origin_y + agent.y * self.cell_size

        rect = pygame.Rect(
            x + 6,
            y + 20,
            self.cell_size - 12,
            self.cell_size - 20,
        )

        pygame.draw.rect(
            self.screen,
            self._agent_color(agent),
            rect,
            border_radius=10,
        )

    def _draw_agent_hud(self, agent: Simulite):
        origin_x, origin_y = self._grid_origin()

        x = origin_x + agent.x * self.cell_size
        y = origin_y + agent.y * self.cell_size

        hud_width = self.cell_size + 72
        hud_height = 58
        hud_x = x - 10
        hud_y = y - 34

        hud_rect = pygame.Rect(hud_x, hud_y, hud_width, hud_height)
        pygame.draw.rect(self.screen, HUD_BG_COLOR, hud_rect, border_radius=8)

        name_surface = self.tiny_font.render(agent.name, True, HUD_TEXT_COLOR)
        energy_surface = self.tiny_font.render(
            f"E:{agent.energy}",
            True,
            HUD_TEXT_COLOR,
        )
        mood_surface = self.tiny_font.render(
            self._mood_label(agent),
            True,
            HUD_TEXT_COLOR,
        )
        food_surface = self.tiny_font.render(
            self._memory_food_label(agent),
            True,
            HUD_TEXT_COLOR,
        )
        friend_surface = self.tiny_font.render(
            self._friend_label(agent),
            True,
            HUD_TEXT_COLOR,
        )

        self.screen.blit(name_surface, (hud_x + 6, hud_y + 4))
        self.screen.blit(energy_surface, (hud_x + 6, hud_y + 18))
        self.screen.blit(mood_surface, (hud_x + 48, hud_y + 18))
        self.screen.blit(food_surface, (hud_x + 6, hud_y + 32))
        self.screen.blit(friend_surface, (hud_x + 6, hud_y + 44))

    def _draw_agent_goal(self, agent: Simulite):
        origin_x, origin_y = self._grid_origin()

        x = origin_x + agent.x * self.cell_size
        y = origin_y + agent.y * self.cell_size

        goal_text = self._goal_label(agent)
        goal_surface = self.tiny_font.render(goal_text, True, (210, 210, 210))
        self.screen.blit(goal_surface, (x + 2, y + self.cell_size + 2))

    def _draw_event_panel(self, world):
        panel_x, panel_y = self._panel_origin(world)
        panel_height = world.grid.height * self.cell_size

        panel_rect = pygame.Rect(
            panel_x,
            panel_y,
            self.panel_width,
            panel_height,
        )
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_rect, border_radius=10)
        pygame.draw.rect(
            self.screen,
            PANEL_BORDER_COLOR,
            panel_rect,
            width=1,
            border_radius=10,
        )

        title_surface = self.font.render("Event Log", True, PANEL_TITLE_COLOR)
        self.screen.blit(title_surface, (panel_x + 14, panel_y + 12))

        info_surface = self.tiny_font.render(
            "Recent world activity",
            True,
            (170, 170, 170),
        )
        self.screen.blit(info_surface, (panel_x + 14, panel_y + 38))

        line_y = panel_y + 68
        line_height = 22

        if not self.event_log:
            empty_surface = self.small_font.render(
                "No events yet...",
                True,
                PANEL_TEXT_COLOR,
            )
            self.screen.blit(empty_surface, (panel_x + 14, line_y))
            return

        for entry in reversed(self.event_log):
            entry_surface = self.tiny_font.render(entry[:44], True, PANEL_TEXT_COLOR)
            self.screen.blit(entry_surface, (panel_x + 14, line_y))
            line_y += line_height

            if line_y > panel_y + panel_height - 24:
                break

    def _draw_footer(self, world):
        footer_y = self.margin + world.grid.height * self.cell_size + 28

        tick_text = self.font.render(
            f"Tick: {world.tick}",
            True,
            (230, 230, 230),
        )
        self.screen.blit(tick_text, (self.margin, footer_y))

        weather_kind = getattr(getattr(world, "weather", None), "kind", "unknown")
        weather_text = self.font.render(
            f"Weather: {weather_kind}",
            True,
            (230, 230, 230),
        )
        self.screen.blit(weather_text, (self.margin + 150, footer_y))

        hint_surface = self.tiny_font.render(
            "ESC to close viewer",
            True,
            (180, 180, 180),
        )
        self.screen.blit(hint_surface, (self.margin, footer_y + 30))

    def render(self, world, fps: int = 6) -> bool:
        if not self._initialized:
            self._init(world)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        self._update_event_log(world)

        self.screen.fill(BG_COLOR)
        self._draw_grid(world)

        for y in range(world.grid.height):
            for x in range(world.grid.width):
                obj = world.grid.get(x, y)
                if isinstance(obj, Food):
                    self._draw_food(x, y)

        for agent in world.agents:
            self._draw_agent(agent)

        for agent in world.agents:
            self._draw_agent_hud(agent)
            self._draw_agent_goal(agent)

        self._draw_event_panel(world)
        self._draw_footer(world)

        pygame.display.flip()
        pygame.event.pump()
        self.clock.tick(fps)
        return True
