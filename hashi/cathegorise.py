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

from node import Node
from difficulty_mapper import get_table, MAP_PATH


ISLAND_WEIGHT_FACTOR: float = 0.3
STEP_WEIGHT_FACTOR: float = 0.7
STEP_COUNT_MAP: list[list[int, int, int, int]] = get_table(MAP_PATH)


def get_geometry_count_boundries(width: int, height: int) -> list[int, int]:
    """
    Gets a geometry and returns the step count boundries.\n
    Returns a list of two integers, min and max.\n
    Returns [-1, -1] if geometry is not found in map.
    """
    for geometry in STEP_COUNT_MAP:
        if geometry[0] == width and geometry[1] == height:
            return [geometry[2], geometry[3]]
    return [-1, -1]


def determine_difficulty(grid: list[list[Node]], step_count: int) -> float:
    """
    Gets a grid and returns a difficulty rating.\n
    Rating is an integer between 0 and 1.
    """
    grid_width: int = len(grid)
    grid_height: int = len(grid[0])
    island_amount: int = 0 # amount of islands
    total_island_count: int = 0 # total amount of bridges needed
    for x in range(grid_width):
        for y in range(grid_height):
            if grid[x][y].n_type == 1:
                island_amount += 1
                total_island_count += grid[x][y].i_count
    island_count_weight: float = total_island_count / island_amount / 8
    min_step, max_step = get_geometry_count_boundries(grid_width, grid_height)
    step_count_weight: float = (step_count - min_step) / (max_step - min_step)
    output = island_count_weight * ISLAND_WEIGHT_FACTOR + step_count_weight * STEP_WEIGHT_FACTOR
    return output


