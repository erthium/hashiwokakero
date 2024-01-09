"""
This script creates <amount> puzzles for each geometry, and checks 
how many steps does it take solve them to map step_count boundries
to be able to determine difficulty while generating further puzzles.
It increase both width and height by 5 each time.
From 5x5 to 50x50

TODO: We might want to map the step count with island amount instead of geometry.
"""

from node import Node
from generator import generate_till_full
from export import save_grid
from solver import solve


ITERATION_COUNT: int = 10_000

# paths
import os
SCRIPT_DIR: str = os.path.dirname(__file__)
PROJECT_DIR: str = os.path.abspath(os.path.join(SCRIPT_DIR, '../'))
DATABASE_DIR: str = os.path.join(PROJECT_DIR, "database")
MAP_PATH: str = os.path.join(DATABASE_DIR, "difficulty_map.json")

# format: list of geometry, min and max step count -> [5, 5, 63, 267]
hash_table: list[list[int, int, int, int]] = []


def get_table(json_path: str) -> list[list[int, int, int, int]]:
    """
    Loads the entire table from a json file.
    """
    import json
    with open(json_path, "r") as file:
        return json.load(file)


def save_table(json_path: str) -> None:
    """
    Dumps the entire table to a json file.\n
    Rewrite the entire file each time.
    """
    import json
    with open(json_path, "w") as file:
        json.dump(hash_table, file)


def genearate_and_solve(width: int, height: int, amount: int) -> list[int, int]:
    """
    Generates a grid and solves it.
    """
    min = 100000
    max = 0
    for _ in range(amount):
        grid = generate_till_full(width, height)
        _, step_count = solve(grid)
        if step_count < min:
            min = step_count
        if step_count > max:
            max = step_count
    return [min, max]


def iterate_all_geometries(json_path: str, amount: int) -> None:
    for width in range(5, 51, 5):
        for height in range(5, 51, 5):
            print(f"Generating {width}x{height} puzzles...")
            step_count = genearate_and_solve(width, height, amount)
            hash_table.append([width, height, min(step_count), max(step_count)])
            save_table(json_path)


def main():
    iterate_all_geometries(MAP_PATH, ITERATION_COUNT)


if __name__ == "__main__":
    main()
