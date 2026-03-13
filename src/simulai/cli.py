from __future__ import annotations
import argparse
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.agents.simulite import Simulite
from simulai.render.text import TextRenderer
from simulai.io.serialize import save_world, load_world

def main():
    parser = argparse.ArgumentParser(prog="simulai", description="SimulAI CLI")
    sub = parser.add_subparsers(dest="command")

    # demo
    demo = sub.add_parser("demo", help="Run a tiny demo world with a few Simulites")
    demo.add_argument("--steps", type=int, default=20, help="Number of time steps")
    demo.add_argument("--size", type=int, default=8, help="Grid size (NxN)")

    # save: build a fresh world, simulate, then save to file
    savep = sub.add_parser("save", help="Build a world, run for N steps, then save to JSON/YAML")
    savep.add_argument("--file", "-f", required=True, help="Output file path (e.g., world.json / world.yaml)")
    savep.add_argument("--size", type=int, default=10, help="Grid size (NxN)")
    savep.add_argument("--steps", type=int, default=20, help="Steps to simulate before saving")
    savep.add_argument("--format", choices=["json", "yaml"], help="Override format (otherwise inferred from extension)")

    # load: load a saved world and continue simulating
    loadp = sub.add_parser("load", help="Load a saved world (JSON/YAML) and simulate further")
    loadp.add_argument("--file", "-f", required=True, help="Input file path")
    loadp.add_argument("--steps", type=int, default=20, help="Steps to simulate after loading")

    args = parser.parse_args()
    if args.command == "demo":
        run_demo(steps=args.steps, size=args.size)
    elif args.command == "save":
        cmd_save(args)
    elif args.command == "load":
        cmd_load(args)
    else:
        parser.print_help()

def build_world(size: int) -> World:
    grid = Grid(width=size, height=size)
    world = World(grid=grid)
    # spawn a couple of Simulites
    world.add_agent(Simulite(name="Zizi", x=1, y=1))
    world.add_agent(Simulite(name="Karo", x=size - 2, y=size - 2))
    # sprinkle initial food
    world.sprinkle_food(count=max(3, size // 2))
    return world

def run_demo(steps: int, size: int):
    world = build_world(size=size)
    renderer = TextRenderer()
    for _ in range(steps):
        world.step()
        renderer.render(world)

def cmd_save(args):
    world = build_world(size=args.size)
    renderer = TextRenderer()
    # simulate some steps so there's state to save
    for _ in range(args.steps):
        world.step()
        # comment out rendering for faster saves; enable if you want visuals
        # renderer.render(world)
    save_world(args.file, world, fmt=args.format)
    print(f"✅ Saved world to {args.file}")

def cmd_load(args):
    world = load_world(args.file)
    renderer = TextRenderer()
    print(f"📂 Loaded world from {args.file} (tick={world.tick}, size={world.grid.width}x{world.grid.height})")
    for _ in range(args.steps):
        world.step()
        renderer.render(world)

if __name__ == "__main__":
    main()
``
