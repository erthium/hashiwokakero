"""
This module contains functions to cathegorise a puzzle.

To determine difficulty, five factors are taken into account:

1. Island Weight: The average island count of all islands.
2. Island Amount: The amount of islands in the grid relative to the maximum possible amount.
3. Below Seven: The amount of islands with count less than seven.
4. By Rule Steps: The amount of steps taken by the solver by rule.
5. Average Brutal Steps: The average amount of steps taken by the solver by brutal force.
"""


from dataclasses import dataclass
from node import Node
import os

SCRIPT_DIR: str = os.path.dirname(__file__)
MAP_PATH: str = os.path.join(SCRIPT_DIR, "difficulty_map.json")


ISLAND_WEIGHT_FACTOR: float = 0.61
ISLAND_AMOUNT_FACTOR: float = 0.33
BELOW_SEVEN_FACTOR: float = 0.06
BY_RULE_STEP_FACTOR: float = 0.0
BRUTAL_STEP_FACTOR: float = 0.0


@dataclass
class PuzzleInformation:
    grid_width: int
    grid_height: int
    island_amount: int
    total_island_count: int
    total_seven_count: int
    total_eight_count: int
    by_rule_steps: int
    brutal_steps_list: list[int]


def get_diffiulty_map() -> list[dict]:
    """
    Loads the entire table from a json file.
    """
    import json
    with open(MAP_PATH, "r") as file:
        return json.load(file)


def save_diffiulty_map(difficulty_map: list[dict]) -> None:
    """
    Dumps the entire table to a json file.\n
    Rewrite the entire file each time.
    """
    import json
    with open(MAP_PATH, "w") as file:
        json.dump(difficulty_map, file)


def get_island_amount_boundries(width: int, height: int) -> list[int, int]:
    """
    Gets a geometry and returns the island amount boundries.\n
    Returns a list of two integers, min and max.\n
    Returns [-1, -1] if geometry is not found in map.
    """
    min_count: int = 2
    max_count: int = width * height / 3
    return [min_count, max_count]


def inspect_puzzle(grid: list[list[Node]], by_rule_steps, brutal_steps_list) -> PuzzleInformation:
    """
    Inspects a grid and returns a PuzzleInformation object.\n
    Used to determine core values of a puzzle to cathegorise it.
    """
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
    return PuzzleInformation(grid_width, grid_height, island_amount, total_island_count, total_seven_count, total_eight_count, by_rule_steps, brutal_steps_list)


def get_difficulty_value(grid: list[list[Node]], by_rule_steps, brutal_steps_list) -> float:
    """
    Gets a grid, by_rule_steps and brutal_steps_list and returns a difficulty rating.\n
    Rating is a normalised value, a float between 0 and 1.\n
    Assumes that the difficulty map file exists.
    """
    info: PuzzleInformation = inspect_puzzle(grid, by_rule_steps, brutal_steps_list)
    difficulty_map = get_diffiulty_map()

    island_weigth = info.total_island_count / info.island_amount
    min_island_weight = difficulty_map["island_weight"][0]
    max_island_weight = difficulty_map["island_weight"][1]
    normalized_island_weight = (island_weigth - min_island_weight) / (max_island_weight - min_island_weight)
    island_weight_difficulty = normalized_island_weight * ISLAND_WEIGHT_FACTOR

    island_amount_weight = info.island_amount / (info.grid_width + info.grid_height) / 2
    min_island_amount_weight = difficulty_map["island_amount_weight"][0]
    max_island_amount_weight = difficulty_map["island_amount_weight"][1]
    normalized_island_amount_weight = (island_amount_weight - min_island_amount_weight) / (max_island_amount_weight - min_island_amount_weight)
    island_amount_weight_difficulty = normalized_island_amount_weight * ISLAND_AMOUNT_FACTOR

    below_seven_weight = info.island_amount - (info.total_seven_count + info.total_eight_count)
    min_below_seven_weight = difficulty_map["below_seven_weight"][0]
    max_below_seven_weight = difficulty_map["below_seven_weight"][1]
    normalized_below_seven_weight = (below_seven_weight - min_below_seven_weight) / (max_below_seven_weight - min_below_seven_weight)
    below_seven_weight_difficulty = normalized_below_seven_weight * BELOW_SEVEN_FACTOR

    min_by_rule_steps = difficulty_map["by_rule_steps"][0]
    max_by_rule_steps = difficulty_map["by_rule_steps"][1]
    normalized_by_rule_steps = (by_rule_steps - min_by_rule_steps) / (max_by_rule_steps - min_by_rule_steps)
    by_rule_steps_difficulty = normalized_by_rule_steps * BY_RULE_STEP_FACTOR

    average_brutal_steps = sum(brutal_steps_list) / len(brutal_steps_list)
    min_average_brutal_steps = difficulty_map["average_brutal_steps"][0]
    max_average_brutal_steps = difficulty_map["average_brutal_steps"][1]
    normalized_average_brutal_steps = (average_brutal_steps - min_average_brutal_steps) / (max_average_brutal_steps - min_average_brutal_steps)
    average_brutal_steps_difficulty = normalized_average_brutal_steps * BRUTAL_STEP_FACTOR

    difficulty =    island_weight_difficulty + \
                    island_amount_weight_difficulty + \
                    below_seven_weight_difficulty + \
                    by_rule_steps_difficulty + \
                    average_brutal_steps_difficulty

    return difficulty
