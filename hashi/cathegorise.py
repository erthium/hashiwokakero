"""
This module contains functions to cathegorise a puzzle.

To determine difficulty, two factors are taken into account:

1. Total island count / amount of islands: as the i_count of 
islands get lower in average, the difficulty increases.
2. Step count to solve

For the first factor, it is easy to put in a range from 0 to 1.

For the second factor, it is not so easy. The step count can be
any positive integer. What to do about it?
"""

""" --- TODO ---
- Not sure how exactly to use island amount factor, more islands sometimes make it easier, sometimes harder
We might be able to link them with island weigth factor
"""

from dataclasses import dataclass
from node import Node
import os

SCRIPT_DIR: str = os.path.dirname(__file__)
MAP_PATH: str = os.path.join(SCRIPT_DIR, "difficulty_map.json")


ISLAND_WEIGHT_FACTOR: float = 0.61
ISLAND_AMOUNT_FACTOR: float = 0.33
BELOW_SEVEN_FACTOR: float = 0.06


def get_diffiulty_map() -> list[list[int, int, int, int]]:
    """
    Loads the entire table from a json file.
    """
    import json
    with open(MAP_PATH, "r") as file:
        return json.load(file)


def save_diffiulty_map(difficulty_map: list[list[int, int, int, int]]) -> None:
    """
    Dumps the entire table to a json file.\n
    Rewrite the entire file each time.
    """
    import json
    with open(MAP_PATH, "w") as file:
        json.dump(difficulty_map, file)


@dataclass
class PuzzleInformation:
    grid_width: int
    grid_height: int
    island_amount: int
    total_island_count: int
    total_seven_count: int
    total_eight_count: int


def get_island_amount_boundries(width: int, height: int) -> list[int, int]:
    """
    Gets a geometry and returns the island amount boundries.\n
    Returns a list of two integers, min and max.\n
    Returns [-1, -1] if geometry is not found in map.
    """
    min_count: int = 2
    max_count: int = width * height / 3
    return [min_count, max_count]


def inspect_puzzle(grid: list[list[Node]]) -> PuzzleInformation:
    grid_width: int = len(grid)
    grid_height: int = len(grid[0])
    island_amount: int = 0 # amount of islands
    total_island_count: int = 0 # sum of all island counts
    total_seven_count: int = 0
    total_eight_count: int = 0
    for x in range(grid_width):
        for y in range(grid_height):
            if grid[x][y].n_type == 1:
                island_amount += 1
                total_island_count += grid[x][y].i_count
                if grid[x][y].i_count == 7:
                    total_seven_count += 1
                if grid[x][y].i_count == 8:
                    total_eight_count += 1
    return PuzzleInformation(grid_width, grid_height, island_amount, total_island_count, total_seven_count, total_eight_count)


def get_difficulty_value(grid: list[list[Node]]) -> float:
    """
    Gets a grid and returns a difficulty rating.\n
    Rating is an float between 0 and 1.
    """
    info: PuzzleInformation = inspect_puzzle(grid)

    island_weigth = info.total_island_count / info.island_amount
    island_weigth_calculated = island_weigth * ISLAND_WEIGHT_FACTOR

    island_amount_weight = info.island_amount / (info.grid_width + info.grid_height) / 2
    island_amount_weight_calculated = island_amount_weight * ISLAND_AMOUNT_FACTOR

    below_seven_weight = info.island_amount - (info.total_seven_count + info.total_eight_count)
    below_seven_weight_calculated = below_seven_weight * BELOW_SEVEN_FACTOR

    difficulty = island_weigth_calculated + island_amount_weight_calculated + below_seven_weight_calculated
    return difficulty


def get_difficulty(grid: list[list[Node]]) -> int:
    """
    Gets a grid and returns a difficulty rating.\n
    Return value is an integer between 1 and 3.\n
    1: Easy\n
    2: Medium\n
    3: Hard
    """
    difficulty = get_difficulty_value(grid)
    difficulty_map = get_diffiulty_map()
    for entry in difficulty_map:
        if entry[0] == len(grid) and entry[1] == len(grid[0]):
            min_difficulty = entry[2]
            max_difficulty = entry[3]
            easy_boundry = (max_difficulty - min_difficulty) / 3 + min_difficulty
            intermediate_boundry = (max_difficulty - min_difficulty) / 3 * 2 + min_difficulty
            if difficulty < easy_boundry:
                return 1
            elif difficulty < intermediate_boundry:
                return 2
            else:
                return 3
    raise ValueError("Geometry not found in difficulty map.")
