"""

"""

from node import Node
from generator import generate_till_full
from export import save_grid
from solver import solve
from cathegorise import determine_difficulty

# DIRECTORIES
import os
""" --STRUCTURE--
project/
    hashi/
        production.py
        ...
    database/
        easy/
        intermediate/
        hard/
"""
DATABASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '../database'))
EASY_DIR: str = os.path.join(DATABASE_DIR, "easy")
INTERMEDIATE_DIR: str = os.path.join(DATABASE_DIR, "intermediate")
HARD_DIR: str = os.path.join(DATABASE_DIR, "hard")
assert os.path.isdir(DATABASE_DIR)
assert os.path.isdir(EASY_DIR)
assert os.path.isdir(INTERMEDIATE_DIR)
assert os.path.isdir(HARD_DIR)
easy_puzzle_count: int = len(os.listdir(EASY_DIR))
intermediate_puzzle_count: int = len(os.listdir(INTERMEDIATE_DIR))
hard_puzzle_count: int = len(os.listdir(HARD_DIR))


def is_completed(grid: list[list[Node]]) -> bool:
    """
    Checks if the grid is completed.
    """
    for row in grid:
        for node in row:
            if node.needed != 0:
                return False
    return True


def save_according_to_difficulty(grid: list[list[Node]], difficulty: int) -> None:
    """
    Saves the grid according to its difficulty.
    """
    global easy_puzzle_count, intermediate_puzzle_count, hard_puzzle_count
    puzzle_path = None
    if difficulty < 0.3:
        puzzle_path = os.path.join(EASY_DIR, f"puzzle_{easy_puzzle_count}.csv")
        easy_puzzle_count += 1
    elif difficulty < 0.6:
        puzzle_path = os.path.join(INTERMEDIATE_DIR, f"puzzle_{intermediate_puzzle_count}.csv")
        intermediate_puzzle_count += 1
    else:
        puzzle_path = os.path.join(HARD_DIR, f"puzzle_{hard_puzzle_count}.csv")
        hard_puzzle_count += 1
    assert puzzle_path is not None
    save_grid(grid, puzzle_path)


def produce(amount: int) -> None:
    """
    Steps:
    1. Generate a full grid
    2. Solve it and determine the difficulty
    3. Save it according to the difficulty
    """

    while amount > 0:
        grid = generate_till_full()
        solved_grid, step_count = solve(grid)
        if not is_completed(solved_grid): return # if the grid is not solvable, don't save it
        difficulty = determine_difficulty(solved_grid, step_count)
        save_according_to_difficulty(solved_grid, difficulty)
        amount -= 1


def main() -> None:
    pass


if __name__ == "__main__":
    main()
