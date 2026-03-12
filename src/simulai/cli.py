from __future__ import annotations
import argparse
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.agents.simulite import Simulite
from simulai.render.text import TextRenderer

def main():
    parser = argparse.ArgumentParser(prog="simulai", description="SimulAI CLI")
    sub = parser.add_subparsers(dest="command")

    demo = sub.add_parser("demo", help="Run a tiny demo world with a few Simulites")
    demo.add_argument("--steps", type=int, default=20, help="Number of time steps")
    demo.add_argument("--size", type=int, default=8, help="Grid size (NxN)")

    args = parser.parse_args()
    if args.command == "demo":
        run_demo(steps=args.steps, size=args.size)
    else:
        parser.print_help()

def run_demo(steps: int, size: int):
    grid = Grid(width=size, height=size)
    world = World(grid=grid)
    world.add_agent(Simulite(name="Zizi", x=1, y=1))
    world.add_agent(Simulite(name="Karo", x=size - 2, y=size - 2))

    # sprinkle initial food
    world.sprinkle_food(count=max(3, size // 2))

    renderer = TextRenderer()
    for _ in range(steps):
        world.step()
        renderer.render(world)

if __name__ == "__main__":
    main()
``
