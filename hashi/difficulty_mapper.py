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
from cathegorise import inspect_puzzle, PuzzleInformation
from solver import solve, Solution
from visualiser import draw_grid

ITERATION_COUNT: int = 1


def genearate_and_cathegorise(width: int, height: int, amount: int) -> dict:
    """
    Generates a grid and solves it.
    """
    geometry_values = {}
    geometry_values["width"] = width
    geometry_values["height"] = height
    geometry_values["island_weight"] = [float("inf"), float("-inf")]
    geometry_values["island_amount_weight"] = [float("inf"), float("-inf")]
    geometry_values["below_seven_weight"] = [float("inf"), float("-inf")]
    geometry_values["by_rule_steps"] = [float("inf"), float("-inf")]
    geometry_values["average_brutal_steps"] = [float("inf"), float("-inf")]

    for _ in range(amount):
        grid: list[list[Node]] = generate_till_full(width, height)
        #draw_grid(grid)
        all_solutions: list[Solution] = solve(grid)
        by_rule_steps: int = all_solutions[0].rule_steps
        brutal_steps_list: list[int] = [solution.brutal_steps for solution in all_solutions]
        info: PuzzleInformation = inspect_puzzle(grid, by_rule_steps, brutal_steps_list)

        # island_weight
        island_weigth = info.total_island_count / info.island_amount
        if island_weigth < geometry_values["island_weight"][0]:
            geometry_values["island_weight"][0] = island_weigth
        if island_weigth > geometry_values["island_weight"][1]:
            geometry_values["island_weight"][1] = island_weigth

        # island_amount_weight
        island_amount_weight = info.island_amount / (info.grid_width + info.grid_height) / 2
        if island_amount_weight < geometry_values["island_amount_weight"][0]:
            geometry_values["island_amount_weight"][0] = island_amount_weight
        if island_amount_weight > geometry_values["island_amount_weight"][1]:
            geometry_values["island_amount_weight"][1] = island_amount_weight

        # below_seven_weight
        below_seven_weight = info.island_amount - (info.total_seven_count + info.total_eight_count)
        if below_seven_weight < geometry_values["below_seven_weight"][0]:
            geometry_values["below_seven_weight"][0] = below_seven_weight
        if below_seven_weight > geometry_values["below_seven_weight"][1]:
            geometry_values["below_seven_weight"][1] = below_seven_weight

        # by_rule_steps
        if by_rule_steps < geometry_values["by_rule_steps"][0]:
            geometry_values["by_rule_steps"][0] = by_rule_steps
        if by_rule_steps > geometry_values["by_rule_steps"][1]:
            geometry_values["by_rule_steps"][1] = by_rule_steps

        # average_brutal_steps
        average_brutal_steps = sum(brutal_steps_list) / len(brutal_steps_list)
        if average_brutal_steps < geometry_values["average_brutal_steps"][0]:
            geometry_values["average_brutal_steps"][0] = average_brutal_steps
        if average_brutal_steps > geometry_values["average_brutal_steps"][1]:
            geometry_values["average_brutal_steps"][1] = average_brutal_steps

    return geometry_values


def iterate_all_geometries(amount: int) -> None:
    all_geometry_data: list[dict] = []

    for width in range(5, 51, 5):
        for height in range(5, 51, 5):
            print(f"Generating {width}x{height} puzzles...")
            geometry_values = genearate_and_cathegorise(width, height, amount)
            all_geometry_data.append(geometry_values)
            #save_diffiulty_map(all_geometry_data)


def main():
    iterate_all_geometries(ITERATION_COUNT)


if __name__ == "__main__":
    main()
