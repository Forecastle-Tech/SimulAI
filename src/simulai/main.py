from __future__ import annotations

from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.render.pygame_renderer import PygameRenderer

SIM_TICKS = 800
FPS = 5


def build_world() -> World:
    grid = Grid(10, 10)
    world = World(grid)

    a = Simulite("A", 2, 2, traits=Traits(curiosity=4, sociability=7))
    b = Simulite("B", 7, 7, traits=Traits(curiosity=6, sociability=5))

    world.add_agent(a)
    world.add_agent(b)

    world.sprinkle_food(count=12)
    return world


def main() -> None:
    world = build_world()
    renderer = PygameRenderer(world.grid.width, world.grid.height)

    for _ in range(SIM_TICKS):
        world.step()
        renderer.render(world, fps=FPS)

    stats = world.get_dashboard_stats()

    print("Simulation complete. Check outputs/simulation_metrics.csv")
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
