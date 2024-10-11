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
from cathegorise import get_difficulty_value, save_diffiulty_map

ITERATION_COUNT: int = 10_000


def genearate_and_cathegorise(width: int, height: int, amount: int) -> list[int, int]:
    """
    Generates a grid and solves it.
    """
    min = float("inf")
    max = float("-inf")
    for _ in range(amount):
        grid: list[list[Node]] = generate_till_full(width, height)
        puzzle_difficulty = get_difficulty_value(grid)
        if puzzle_difficulty < min:
            min = puzzle_difficulty
        if puzzle_difficulty > max:
            max = puzzle_difficulty
    return [min, max]


def iterate_all_geometries(amount: int) -> None:
    hash_table: list[list[int, int, int, int]] = []
    for width in range(5, 51, 5):
        for height in range(5, 51, 5):
            print(f"Generating {width}x{height} puzzles...")
            min_difficulty, max_difficulty = genearate_and_cathegorise(width, height, amount)
            hash_table.append([width, height, min_difficulty, max_difficulty])
            save_diffiulty_map(hash_table)


def main():
    iterate_all_geometries(ITERATION_COUNT)


if __name__ == "__main__":
    main()
