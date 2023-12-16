"""
Generator Algorithm
-------------------
islands = []
choose a random node and add to islands
for _ in range(step_per_cycle):
    get a random node from islands
    get a random possible direction 
    get a random bridge thickness (1, 2)
    get a random bridge length
    establish the bridge
print the grid
get input from user
Y -> continue another cycle
n -> exit
"""

"""
Saving Puzzles
--------------

inside puzzles/puzzle.{i}.csv:

width;;height;;empty_grid;;solution_grid

w;;h;;000010502007....0050;;0012513106133610....0125120

empty_grid: 
    0 -> empty
    any other positive integer -> island

solution_grid: 
    0 -> empty
    positive integers -> island
    negative integers -> bridge
        -1 -> horizontal single
        -2 -> horizontal double
        -3 -> vertical single
        -4 -> vertical double
"""

"""
Terminology
-----------

Full Grid: A grid that satisfies given w and h dimensions and has no empty edges.

Cycle Step: Iteration count of the generator algorithm. Since generation is random, 
it may not reach that iteration count. Still is important if the user wants to stop 
generating at some point

Max Puzzle: A puzzle which cannot be extended anymore, which has no node that could 
potentially have another bridge in an empty direction.
"""

from node import Node
from random import randint, choice
from visualiser import draw_grid
from export import save_grid


def get_random_direction(grid: list[list[Node]], x: int, y: int) -> int:
    """0->left, 1->up, 2->right, 3->down, -1->no possible direction"""
    assert grid[x][y].n_type == 1
    assert x >= 0 and x < len(grid)
    assert y >= 0 and y < len(grid[0])
    possible_directions = []
    if x > 1 and grid[x-1][y].n_type == 0 and grid[x-2][y].n_type == 0:
        possible_directions.append(0)
    if y > 1 and grid[x][y-1].n_type == 0 and grid[x][y-2].n_type == 0:
        possible_directions.append(1)
    if x < len(grid)-2 and grid[x+1][y].n_type == 0 and grid[x+2][y].n_type == 0:
        possible_directions.append(2)
    if y < len(grid[0])-2 and grid[x][y+1].n_type == 0 and grid[x][y+2].n_type == 0:
        possible_directions.append(3)
    if len(possible_directions) == 0: return -1
    return choice(possible_directions)

def get_random_bridge_thickness(grid: list[list[Node]], x: int, y: int) -> int:
    assert grid[x][y].n_type == 1
    assert x >= 0 and x < len(grid)
    assert y >= 0 and y < len(grid[0])
    if  8 - grid[x][y].i_count > 1:
        return choice([1, 2])
    return 1

def direction_to_vector(direction: int) -> tuple[int, int]:
    assert direction >= 0 and direction < 4
    return [(-1, 0), (0, -1), (1, 0), (0, 1)][direction]

def get_random_bridge_length(grid: list[list[Node]], x: int, y: int, direction: int) -> int:
    assert grid[x][y].n_type == 1
    assert x >= 0 and x < len(grid)
    assert y >= 0 and y < len(grid[0])
    assert direction >= 0 and direction < 4
    dir_vector = direction_to_vector(direction)
    max_length = 1
    check_x = x + dir_vector[0] * (max_length + 2)
    check_y = y + dir_vector[1] * (max_length + 2)
    while True:
        if check_x < 0 or check_x >= len(grid) or check_y < 0 or check_y >= len(grid[0]):
            break
        if grid[check_x][check_y].n_type != 0:
            break
        max_length += 1
        check_x += dir_vector[0]
        check_y += dir_vector[1]
    return randint(1, max_length)

step_per_cycle = 100
def generate(w: int, h: int) -> list[list[Node]]:
    """
    Generates a puzzle with given w and h dimensions.
    Returns a 2D list of nodes.
    Output may not be full, meaning one edge line of the grid may be empty.
    Use generate_till_full() to generate a surely full grid.
    """
    grid = [[Node(i, j) for j in range(h)] for i in range(w)]
    islands = []
    islands.append(grid[randint(0, w-1)][randint(0, h-1)])
    islands[0].make_island(0)
    is_dead_end = False
    while True:
        for _ in range(step_per_cycle):
            if len(islands) == 0:
                is_dead_end = True
                break
            current_node = choice(islands)
            direction = get_random_direction(grid, current_node.x, current_node.y)
            if direction == -1: # no possible direction
                islands.remove(current_node)
                continue
            thickness = get_random_bridge_thickness(grid, current_node.x, current_node.y)
            length = get_random_bridge_length(grid, current_node.x, current_node.y, direction)
            dir_vector = direction_to_vector(direction)
            x = current_node.x
            y = current_node.y
            last_node = grid[x + dir_vector[0] * (length + 1)][y + dir_vector[1] * (length + 1)]
            # check if selected node has direct ortogonal island neighbour
            adjacent_island_found = False
            for dir in [0, 1]:
                vector = direction_to_vector(dir)
                if last_node.x + vector[0] >= 0 and last_node.x + vector[0] < len(grid) and last_node.y + vector[1] >= 0 and last_node.y + vector[1] < len(grid[0]):
                    if grid[last_node.x + vector[0]][last_node.y + vector[1]].n_type == 1:
                        adjacent_island_found = True
                if last_node.x - vector[0] >= 0 and last_node.x - vector[0] < len(grid) and last_node.y - vector[1] >= 0 and last_node.y - vector[1] < len(grid[0]):
                    if grid[last_node.x - vector[0]][last_node.y - vector[1]].n_type == 1:
                        adjacent_island_found = True
            if adjacent_island_found:
                continue
            #print(f'Node {x}x{y} - dir: {direction} - thck: {thickness} - len: {length}')
            for i in range(length):
                grid[x + dir_vector[0] * (i + 1)][y + dir_vector[1] * (i + 1)].make_bridge(thickness, direction % 2)
            last_node.make_island(thickness)
            islands.append(last_node)
            current_node.i_count += thickness
        #draw_grid(grid)
        #if is_dead_end or input("Continue? (Y/n): ").lower() == 'n':
        break
    return grid


def check_if_grid_full(grid: list[list[Node]]) -> bool:
    w = len(grid)
    h = len(grid[0])
    if [grid[i][0].n_type for i in range(w)].count(0) == w:
        return False
    if [grid[i][h-1].n_type for i in range(w)].count(0) == w:
        return False
    if [grid[0][i].n_type for i in range(h)].count(0) == h:
        return False
    if [grid[w-1][i].n_type for i in range(h)].count(0) == h:
        return False
    return True


def generate_till_full(w: int, h: int) -> list[list[Node]]:
    """
    Keeps generating a puzzle until it is full.
    Returns a 2D list of nodes.
    """
    grid: list[list[Node]] = None
    while True:
        grid = generate(w, h)
        if check_if_grid_full(grid):
            break
    return grid


def show_grid(grid: list[list[Node]]):
    for line in grid:
        for node in line:
            print(node.n_type, end="  ")
        print('\n')



def main():
    grid = generate_till_full(10, 10)
    draw_grid(grid)
    save_grid(grid, "puzzles/test.csv")
        

if __name__ == "__main__":
    main()