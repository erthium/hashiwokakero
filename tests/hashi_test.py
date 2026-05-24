"""
Test file for the core library.\n
Structure will be changed in the future.
"""

import os
import sys
SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../hashi')))
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from unittest import TestCase, main

from solver import solve
from export import import_empty_grid, import_solution_grid
from node import Node

BASIC_PUZZLE_DIR: str = os.path.join(SCRIPT_DIR, "basic_puzzles")
DIFFICULT_PUZZLE_DIR: str = os.path.join(SCRIPT_DIR, "difficult_puzzles")


def compare_nodes(node1: Node, node2: Node) -> bool:
    """
    Checks necessary properties of two nodes for equality.\n
    Does NOT include solver necessary properties.\n
    Returns True if all properties are equal, False otherwise. 
    """
    if node1.x != node2.x: return False
    if node1.y != node2.y: return False
    if node1.n_type != node2.n_type: return False
    if node1.i_count != node2.i_count: return False
    if node1.b_thickness != node2.b_thickness: return False
    if node1.b_dir != node2.b_dir: return False
    return True


class Tester(TestCase):
    def solver_test(self, path:str) -> None:
        """
        Tries to solve a puzzle and compares the result with the solution.\n
        Prints the name of the file and whether it passed or failed.
        """
        filename = os.path.basename(path)
        empty_grid = import_empty_grid(path)
        solution_grid = import_solution_grid(path)
        grid_w = len(empty_grid)
        grid_h = len(empty_grid[0])
        solutions = solve(empty_grid, stop_at_first=False)
        self.assertGreater(len(solutions), 0, f"No solution found for {filename}")

        # a puzzle may have multiple valid solutions; accept a match against any of them
        matched = False
        for solution in solutions:
            solved_grid = solution.grid
            all_match = True
            for x in range(grid_w):
                if not all_match: break
                for y in range(grid_h):
                    if not compare_nodes(solution_grid[x][y], solved_grid[x][y]):
                        all_match = False
                        break
            if all_match:
                matched = True
                break
        self.assertTrue(matched, f"No solution for {filename} matched the recorded solution grid")


    def test_solve_basic(self) -> None:
        """
        Solves all basic puzzles.
        """
        for filename in os.listdir(BASIC_PUZZLE_DIR):
            if filename.endswith(".csv"):
                path = os.path.join(BASIC_PUZZLE_DIR, filename)
                self.solver_test(path)


    def test_solve_difficult(self) -> None:
        """
        Solves all difficult puzzles.
        """
        for filename in os.listdir(DIFFICULT_PUZZLE_DIR):
            if filename.endswith(".csv"):
                path = os.path.join(DIFFICULT_PUZZLE_DIR, filename)
                self.solver_test(path)


if __name__ == "__main__":
   main()
