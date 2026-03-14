from __future__ import annotations

import argparse

from simulai.agents.simulite import Simulite
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.io.serialize import load_world, save_world
from simulai.render.pygame_renderer import PygameRenderer
from simulai.render.text import TextRenderer


def main():
    parser = argparse.ArgumentParser(prog="simulai", description="SimulAI CLI")
    sub = parser.add_subparsers(dest="command")

    demo = sub.add_parser("demo", help="Run a tiny demo world with a few Simulites")
    demo.add_argument("--steps", type=int, default=20, help="Number of time steps")
    demo.add_argument("--size", type=int, default=8, help="Grid size (NxN)")
    demo.add_argument(
        "--view",
        choices=["text", "pygame"],
        default="text",
        help="Renderer to use",
    )
    demo.add_argument("--fps", type=int, default=6, help="Viewer speed for pygame")

    savep = sub.add_parser(
        "save",
        help="Build a world, run for N steps, then save to JSON/YAML",
    )
    savep.add_argument("--file", "-f", required=True, help="Output file path")
    savep.add_argument("--size", type=int, default=10, help="Grid size (NxN)")
    savep.add_argument("--steps", type=int, default=20, help="Steps before saving")
    savep.add_argument(
        "--format",
        choices=["json", "yaml"],
        help="Override format (otherwise inferred from extension)",
    )

    loadp = sub.add_parser(
        "load",
        help="Load a saved world (JSON/YAML) and simulate further",
    )
    loadp.add_argument("--file", "-f", required=True, help="Input file path")
    loadp.add_argument("--steps", type=int, default=20, help="Steps after loading")
    loadp.add_argument(
        "--view",
        choices=["text", "pygame"],
        default="text",
        help="Renderer to use",
    )
    loadp.add_argument("--fps", type=int, default=6, help="Viewer speed for pygame")

    args = parser.parse_args()
    if args.command == "demo":
        run_demo(steps=args.steps, size=args.size, view=args.view, fps=args.fps)
    elif args.command == "save":
        cmd_save(args)
    elif args.command == "load":
        cmd_load(args)
    else:
        parser.print_help()


def build_world(size: int) -> World:
    grid = Grid(width=size, height=size)
    world = World(grid=grid)

    world.add_agent(Simulite(name="Zizi", x=1, y=1))
    world.add_agent(Simulite(name="Karo", x=size - 2, y=size - 2))

    world.sprinkle_food(count=max(3, size // 2))
    return world


def get_renderer(view: str):
    if view == "pygame":
        return PygameRenderer()
    return TextRenderer()


def run_demo(steps: int, size: int, view: str, fps: int):
    world = build_world(size=size)
    renderer = get_renderer(view)

    try:
        for _ in range(steps):
            world.step()
            if view == "pygame":
                keep_running = renderer.render(world, fps=fps)
                if not keep_running:
                    break
            else:
                renderer.render(world)
    finally:
        if view == "pygame":
            renderer.close()


def cmd_save(args):
    world = build_world(size=args.size)
    for _ in range(args.steps):
        world.step()
    save_world(args.file, world, fmt=args.format)
    print(f"✅ Saved world to {args.file}")


def cmd_load(args):
    world = load_world(args.file)
    renderer = get_renderer(args.view)
    print(
        f"📂 Loaded world from {args.file} "
        f"(tick={world.tick}, size={world.grid.width}x{world.grid.height})"
    )

    try:
        for _ in range(args.steps):
            world.step()
            if args.view == "pygame":
                keep_running = renderer.render(world, fps=args.fps)
                if not keep_running:
                    break
            else:
                renderer.render(world)
    finally:
        if args.view == "pygame":
            renderer.close()


if __name__ == "__main__":
    main()
