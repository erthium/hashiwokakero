"""
Mass production of hashi puzzles.

For each requested puzzle:
    1. Generate a full grid (generate_till_full)
    2. Strip the construction bridges so the solver sees an empty board
    3. Solve and obtain rule_steps / brutal_steps
    4. Score and bucket with the categoriser (per-geometry quantile thresholds)
    5. Save under easy / intermediate / hard / unordered
"""

from __future__ import annotations

import os

from hashi.core import Node
from hashi.generator import generate_till_full
from hashi.formats import save_grid
from hashi.solver import solve
from hashi.categorize import bucket, get_difficulty_value


def _strip_bridges(grid: list[list[Node]]) -> None:
    """
    Removes construction bridges and resets island current_in. Required because
    generate_till_full leaves bridges in place, but solve() expects an empty board.
    """
    for row in grid:
        for node in row:
            if node.n_type == 2:
                node.make_empty()
            elif node.n_type == 1:
                node.current_in = 0


def _bucket_dir(output_dir: str, label: str, categorize: bool) -> str:
    """
    Resolves the subdirectory a freshly-produced puzzle should be written to.
    """
    if not categorize:
        return os.path.join(output_dir, "unordered")
    return os.path.join(output_dir, label)


def _unique_csv_path(directory: str, stem: str) -> str:
    """
    Returns a path 'directory/stem.csv' (or '<stem>_<n>.csv' if stem already taken).
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{stem}.csv")
    if not os.path.isfile(path):
        return path
    n = 0
    while True:
        path = os.path.join(directory, f"{stem}_{n}.csv")
        if not os.path.isfile(path):
            return path
        n += 1


def produce(
    width: int,
    height: int,
    amount: int,
    output_dir: str,
    categorize: bool = True,
) -> None:
    """
    Produces `amount` puzzles at (width, height) and writes them under output_dir.

    output_dir layout when categorize=True:
        output_dir/easy/         puzzles with score < EASY_THRESHOLD
        output_dir/intermediate/ EASY_THRESHOLD <= score < INTERMEDIATE_THRESHOLD
        output_dir/hard/         score >= INTERMEDIATE_THRESHOLD
    When categorize=False:
        output_dir/unordered/    all puzzles, filename keyed on rule_steps
    """
    for i in range(amount):
        grid = generate_till_full(width, height)
        _strip_bridges(grid)
        solutions = solve(grid, stop_at_first=True)
        if not solutions:
            print(f"  [{i + 1}/{amount}] unsolvable — skipping")
            continue
        solution = solutions[0]
        difficulty = get_difficulty_value(
            grid, solution.rule_steps, solution.brutal_steps
        )
        label = bucket(grid, solution.rule_steps, solution.brutal_steps)

        target_dir = _bucket_dir(output_dir, label, categorize)
        if categorize:
            stem = f"puzzle_{difficulty:.5f}"
        else:
            stem = f"puzzle_{solution.rule_steps}"
        path = _unique_csv_path(target_dir, stem)
        save_grid(solution.grid, path)
        print(
            f"  [{i + 1}/{amount}] rule={solution.rule_steps} "
            f"brutal={solution.brutal_steps} score={difficulty:.3f} "
            f"bucket={label} -> {path}"
        )
