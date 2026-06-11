"""
Command-line interface for the hashi package.

Subcommands:
    generate   create one puzzle and write it to CSV
    solve      solve a puzzle CSV; optionally enumerate all solutions
    score     compute a normalised difficulty score
    render     render a puzzle (display or save to PNG)
    produce    mass-generate scored puzzles into bucketed directories
    book       assemble a printable PDF from a directory of produced puzzles
    calibrate  regenerate hashi/data/difficulty_map.json from scratch
"""

from __future__ import annotations

import argparse
import os
import sys


def _add_generate(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("generate", help="generate one puzzle and write it to CSV")
    p.add_argument("width", type=int)
    p.add_argument("height", type=int)
    p.add_argument("-o", "--output", required=True, help="path to write the puzzle CSV")
    p.set_defaults(func=_cmd_generate)


def _cmd_generate(args: argparse.Namespace) -> int:
    from hashi.generator import generate_till_full
    from hashi.formats import save_grid

    if args.width <= 0 or args.height <= 0:
        print("ERROR: width and height must be positive", file=sys.stderr)
        return 2
    grid = generate_till_full(args.width, args.height)
    save_grid(grid, args.output)
    print(f"wrote {args.width}x{args.height} puzzle to {args.output}")
    return 0


def _add_solve(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("solve", help="solve a puzzle CSV")
    p.add_argument("path", help="path to the puzzle CSV")
    p.add_argument(
        "--all",
        action="store_true",
        help="enumerate every solution (default: stop at the first)",
    )
    p.add_argument(
        "--show",
        action="store_true",
        help="open a matplotlib window with the first solution",
    )
    p.set_defaults(func=_cmd_solve)


def _cmd_solve(args: argparse.Namespace) -> int:
    from hashi.formats import import_empty_grid
    from hashi.solver import solve

    grid = import_empty_grid(args.path)
    if grid is None:
        return 2
    solutions = solve(grid, stop_at_first=not args.all)
    print(f"solutions: {len(solutions)}")
    if not solutions:
        return 1
    for i, sol in enumerate(solutions):
        print(f"  [{i}] rule_steps={sol.rule_steps} brutal_steps={sol.brutal_steps}")
    if args.show:
        from hashi.render import draw_grid, show_grid
        show_grid(draw_grid(solutions[0].grid))
    return 0


def _add_score(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("score", help="compute a normalised difficulty score")
    p.add_argument("path", help="path to the puzzle CSV")
    p.set_defaults(func=_cmd_score)


def _cmd_score(args: argparse.Namespace) -> int:
    from hashi.formats import import_empty_grid
    from hashi.solver import solve
    from hashi.categorize import get_difficulty_value

    grid = import_empty_grid(args.path)
    if grid is None:
        return 2
    solutions = solve(grid, stop_at_first=True)
    if not solutions:
        print("ERROR: puzzle is unsolvable", file=sys.stderr)
        return 1
    sol = solutions[0]
    score = get_difficulty_value(grid, sol.rule_steps, sol.brutal_steps)
    print(f"{score:.5f}")
    return 0


def _add_render(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("render", help="render a puzzle to a window or PNG")
    p.add_argument("path", help="path to the puzzle CSV")
    p.add_argument(
        "--solution",
        action="store_true",
        help="render the solved grid stored in the CSV (default: empty grid)",
    )
    p.add_argument(
        "-o",
        "--output",
        help="save to PNG instead of opening a window",
    )
    p.set_defaults(func=_cmd_render)


def _cmd_render(args: argparse.Namespace) -> int:
    from hashi.formats import import_empty_grid, import_solution_grid
    from hashi.render import draw_grid, save_grid_to_image, show_grid

    loader = import_solution_grid if args.solution else import_empty_grid
    grid = loader(args.path)
    if grid is None:
        return 2
    fig = draw_grid(grid)
    if args.output:
        save_grid_to_image(fig, args.output)
    else:
        show_grid(fig)
    return 0


def _add_produce(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "produce", help="mass-generate scored puzzles into bucketed directories"
    )
    p.add_argument("width", type=int)
    p.add_argument("height", type=int)
    p.add_argument("amount", type=int)
    p.add_argument(
        "-d",
        "--output-dir",
        default=os.path.join("output", "database"),
        help="root directory for the easy/intermediate/hard/unordered subdirs",
    )
    p.add_argument(
        "--no-categorize",
        action="store_true",
        help="skip the categoriser and write everything into <output-dir>/unordered",
    )
    p.set_defaults(func=_cmd_produce)


def _cmd_produce(args: argparse.Namespace) -> int:
    from hashi.production import produce

    if args.width <= 0 or args.height <= 0 or args.amount <= 0:
        print("ERROR: width, height, amount must be positive", file=sys.stderr)
        return 2
    produce(
        args.width,
        args.height,
        args.amount,
        output_dir=args.output_dir,
        categorize=not args.no_categorize,
    )
    return 0


def _add_book(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "book", help="assemble a printable PDF from a directory of produced puzzles"
    )
    p.add_argument(
        "input_dir",
        help="directory containing easy/, intermediate/, hard/ subdirs of CSVs",
    )
    p.add_argument(
        "-o",
        "--output",
        required=True,
        help="path to write the PDF",
    )
    p.set_defaults(func=_cmd_book)


def _cmd_book(args: argparse.Namespace) -> int:
    from hashi.book import assemble_book

    if not os.path.isdir(args.input_dir):
        print(f"ERROR: {args.input_dir} is not a directory", file=sys.stderr)
        return 2
    try:
        assemble_book(args.input_dir, args.output)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def _add_calibrate(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "calibrate", help="regenerate hashi/data/difficulty_map.json from scratch"
    )
    p.add_argument(
        "--samples",
        type=int,
        default=None,
        help="puzzles per geometry (default: mapper.ITERATION_COUNT)",
    )
    p.add_argument(
        "--max-brutal",
        type=int,
        default=None,
        help="abort puzzles past this many brute moves (default: mapper.MAX_BRUTAL_STEPS)",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=None,
        help="pool size (default: mapper.WORKER_COUNT)",
    )
    p.set_defaults(func=_cmd_calibrate)


def _cmd_calibrate(args: argparse.Namespace) -> int:
    from hashi.categorize import mapper

    if args.samples is not None:
        mapper.ITERATION_COUNT = args.samples
    if args.max_brutal is not None:
        mapper.MAX_BRUTAL_STEPS = args.max_brutal
    if args.workers is not None:
        mapper.WORKER_COUNT = args.workers
    mapper.iterate_all_geometries(mapper.ITERATION_COUNT)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hashi", description="Hashiwokakero generator, solver, and categoriser."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    _add_generate(sub)
    _add_solve(sub)
    _add_score(sub)
    _add_render(sub)
    _add_produce(sub)
    _add_book(sub)
    _add_calibrate(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
