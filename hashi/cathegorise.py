from node import Node

ISLAND_WEIGHT_FACTOR: float = 0.3
STEP_WEIGHT_FACTOR: float = 1 - ISLAND_WEIGHT_FACTOR

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
    step_count_weight: float = step_count / island_amount
    # TODO: calculate difficulty and return


