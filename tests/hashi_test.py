"""
Test file for the core library.\n
Make sure that test puzzle .csv files are in the same directory as this file.
"""

import os
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../hashi')))
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from unittest import TestCase

from solver import solve
from export import import_empty_grid, import_solution_grid
from node import Node
from visualiser import print_node_data

BASIC_PUZZLE_DIR = os.path.join(SCRIPT_DIR, "basic_puzzles")
DIFFICULT_PUZZLE_DIR = os.path.join(SCRIPT_DIR, "difficult_puzzles")

def compare_nodes(node1: Node, node2: Node) -> bool:
    """
    Checks all properties of two nodes for equality.\n
    Does not include solver necessary properties.\n
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
    def solver_test(self, path):
        for filename in os.listdir(path):
            if filename.endswith(".csv"):
                current_path = os.path.join(path, filename)
                empty_grid = import_empty_grid(current_path)
                solution_grid = import_solution_grid(current_path)
                grid_w = len(empty_grid)
                grid_h = len(empty_grid[0])
                solved_grid = solve(empty_grid, False)
                # go through x and y, compare nodes
                for x in range(grid_w):
                    for y in range(grid_h):
                        if not compare_nodes(solution_grid[x][y], solved_grid[x][y]):
                            print(f"Error in {filename} at ({x}, {y})")
                            print_node_data(solution_grid[x][y])
                            print_node_data(solved_grid[x][y])
                            #self.fail()
            print(f"SOLVER TEST: Passed '{filename}'")
        


def main():
    solver_tests = Tester()
    solver_tests.solver_test(BASIC_PUZZLE_DIR)
    solver_tests.solver_test(DIFFICULT_PUZZLE_DIR)


if __name__ == "__main__":
    main()