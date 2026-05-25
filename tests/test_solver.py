"""
Solver smoke tests — every fixture under tests/fixtures/{basic,difficult}/ must
solve, and at least one of the returned solutions must match the recorded
solution grid in the CSV.
"""

import os
from unittest import TestCase, main

from hashi.core import Node
from hashi.formats import import_empty_grid, import_solution_grid
from hashi.solver import solve

from conftest import BASIC_PUZZLE_DIR, DIFFICULT_PUZZLE_DIR


def compare_nodes(a: Node, b: Node) -> bool:
    return (
        a.x == b.x
        and a.y == b.y
        and a.n_type == b.n_type
        and a.i_count == b.i_count
        and a.b_thickness == b.b_thickness
        and a.b_dir == b.b_dir
    )


class Tester(TestCase):
    def solver_test(self, path: str) -> None:
        filename = os.path.basename(path)
        empty_grid = import_empty_grid(path)
        solution_grid = import_solution_grid(path)
        grid_w = len(empty_grid)
        grid_h = len(empty_grid[0])
        solutions = solve(empty_grid, stop_at_first=False)
        self.assertGreater(len(solutions), 0, f"No solution found for {filename}")

        # Puzzles may have multiple valid solutions — accept any match.
        matched = False
        for solution in solutions:
            solved_grid = solution.grid
            all_match = True
            for x in range(grid_w):
                if not all_match:
                    break
                for y in range(grid_h):
                    if not compare_nodes(solution_grid[x][y], solved_grid[x][y]):
                        all_match = False
                        break
            if all_match:
                matched = True
                break
        self.assertTrue(
            matched, f"No solution for {filename} matched the recorded solution grid"
        )

    def test_solve_basic(self) -> None:
        for filename in sorted(os.listdir(BASIC_PUZZLE_DIR)):
            if filename.endswith(".csv"):
                self.solver_test(str(BASIC_PUZZLE_DIR / filename))

    def test_solve_difficult(self) -> None:
        for filename in sorted(os.listdir(DIFFICULT_PUZZLE_DIR)):
            if filename.endswith(".csv"):
                self.solver_test(str(DIFFICULT_PUZZLE_DIR / filename))


if __name__ == "__main__":
    main()
