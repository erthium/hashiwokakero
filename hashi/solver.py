""" --Solver Algorithm--

get open_islands into an array
any_operation_done = True
while any_operation_done:
    any_operation_done = False
    for island in open_islands:
        get possible bridge directions -> dir
        get possible output count -> out
        get bridge input count -> in
        island count = c
        current = c - in
        if current = out
            build all bridges
            close node
            any_operation_done = True
        else if dir = 1
            build bridge
            close node
            any_operation_done = True
        else if current // 2 = dir - 1 and current % 2 = 1
            build 1 bridge in all possible directions
            any_operation_done = True
if open_islands is empty -> puzzle is solvable
else -> puzzle is unsolvable
"""

""" --TODO List--
TODO: Add rules for islands with 1 or 2, where they cannot 
consider sending all bridges to an identical island
TODO: Create an algorithm for brute-force solving, to be used
after solving with the base rules and remaining a situation
which may contain multiple solutions
"""

from time import sleep
from node import Node, direction_to_vector, is_in_grid
from visualiser import draw_grid, print_node_data
from export import parse_args_empty
from copy import deepcopy

# global variables
_grid: list[list[Node]] = None
_open_islands: list[Node] = None

# global variable removal decorator
def collect_garbage(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        global _grid, _open_islands
        _grid = None
        _open_islands = None
        return result
    return wrapper


def bridge_out_info(x: int, y: int) -> dict[int, int]:
    """
    {0->left, 1->up, 2->right, 3->down}
    """
    global _grid
    grid_w = len(_grid)
    grid_h = len(_grid[0])
    assert _grid[x][y].n_type == 1
    assert is_in_grid(x, y, grid_w, grid_h)
    output = {}
    is_c_one = _grid[x][y].needed == 1
    # first, calculate the input count
    for direction in [0, 1, 2, 3]:
        following_input_bridge = False
        dir_vector = direction_to_vector(direction)
        check_x = x + dir_vector[0]
        check_y = y + dir_vector[1]
        found_target = False
        while is_in_grid(check_x, check_y, grid_w, grid_h):
            if found_target: break
            hit_node = _grid[check_x][check_y]
            if hit_node.n_type == 0:
                check_x += dir_vector[0]
                check_y += dir_vector[1]
            elif hit_node.n_type == 1:
                # Find the max possible input to the hit node
                if following_input_bridge and hit_node.needed >= 1:
                    output[direction] = 1
                else:
                    # Impossible bridge rule
                    if is_c_one:
                        if hit_node.needed >= 1 and hit_node.i_count != 1:
                            output[direction] = 1
                    elif _grid[x][y].i_count == 2 and hit_node.i_count == 2:
                        if hit_node.needed >= 1:
                            output[direction] = 1
                    else:
                        if hit_node.needed >= 1:
                            output[direction] = 2 if hit_node.needed >= 2 else hit_node.needed
                found_target = True
            elif hit_node.n_type == 2:
                if _grid[check_x][check_y].b_dir == direction % 2:
                    if _grid[check_x][check_y].b_thickness == 1:
                        following_input_bridge = True
                        check_x += dir_vector[0]
                        check_y += dir_vector[1]
                    else:
                        found_target = True
                else:
                    found_target = True
    #print(f"Output info: {output}")
    return output


def establish_bridge(x: int, y: int, direction: int, thickness: int) -> None:
    global _grid
    assert _grid[x][y].n_type == 1
    assert is_in_grid(x, y, len(_grid), len(_grid[0]))
    # increase the current_in of both nodes by thickness
    # make the nodes in between bridges
    _grid[x][y].current_in += thickness
    dir_vector = direction_to_vector(direction)
    check_x = x + dir_vector[0]
    check_y = y + dir_vector[1]
    while _grid[check_x][check_y].n_type != 1:
        if _grid[check_x][check_y].n_type == 2:
            assert _grid[check_x][check_y].b_dir == direction % 2
            assert _grid[check_x][check_y].b_thickness == 1
            assert _grid[check_x][check_y].b_thickness + thickness == 2
            _grid[check_x][check_y].b_thickness += thickness
        else:
            _grid[check_x][check_y].make_bridge(thickness, direction % 2)
        check_x += dir_vector[0]
        check_y += dir_vector[1]
    _grid[check_x][check_y].current_in += thickness
    #print(f"Established bridge of thickness {thickness} in direction {direction} from ({x}, {y}) to ({check_x}, {check_y})")


def solve_by_rules() -> None:
    """
    Do not use directly, use bruteforce_solve() instead.\n
    Get an empty grid and applies essential principles to solve it.\n
    If use_given is False, deepcopies the grid and solves the copy.\n
    Return True if solvable, False if unsolvable.\n
    If grid is half-solved, nodes need to be marked with 
    current out and bridges need to be marked as bridges.
    """
    global _grid, _open_islands
    # get all open islands
    for i in range(len(_grid)):
        for j in range(len(_grid[0])):
            if _grid[i][j].n_type == 1:
                _open_islands.append(_grid[i][j])
    
    any_operation_done: bool = True
    while any_operation_done: # if no operation was done, puzzle is unsolvable
        any_operation_done = False
        for i in range(len(_open_islands) - 1, -1, -1): # check every open island each cycle
            island  = _open_islands[i]
            #print_node_data(island)
            #draw_grid(_grid)
            # if island is already closed, skip
            # occurs when an island send a bridge to this one, and not closed it
            if island.needed == 0:
                _open_islands.pop(i)
                continue

            # get current node info
            direction_info: dict[int, int] = bridge_out_info(island.x, island.y)
            max_out = sum(direction_info.values())
            dir = len(list(direction_info.keys()))
            #print(f"Island at ({island.x}, {island.y})")
            #print(f"Dirs: {direction_info}")
            #print(f"Max out: {max_out}")
            
            # main part of the algorithm
            ## if needed == max_out, build all bridges
            if island.needed == max_out:
                for direction, thickness in direction_info.items():
                    establish_bridge(island.x, island.y, direction, thickness)
                _open_islands.remove(island)
                any_operation_done = True

            ## if only one direction is possible, build bridge
            elif dir == 1:
                for direction, thickness in direction_info.items():
                    establish_bridge(island.x, island.y, direction, thickness)
                    _open_islands.remove(island)
                    any_operation_done = True

            ## if island has to send at least 1 bridge in all directions...
            elif island.needed // 2 == dir - 1:
                if island.needed % 2 == 1:
                    for direction, thickness in direction_info.items():
                        establish_bridge(island.x, island.y, direction, 1)
                        any_operation_done = True
                else:
                    there_is_cause = False
                    for direction, thickness in direction_info.items():
                        if thickness == 1:
                            there_is_cause = True
                            break
                            
                    if there_is_cause:
                        for direction, thickness in direction_info.items():
                            if thickness != 1:
                                establish_bridge(island.x, island.y, direction, 1)
                                any_operation_done = True


def tree_search_solution() -> None:
    global _grid, _open_islands


@collect_garbage
def solve(grid: list[list[Node]]) -> list[list[Node]]:
    """
    Solve the given grid by trying rules and brute forcing when it is stuck.\n
    Return the solved grid.
    """
    global _grid, _open_islands
    _grid = grid
    _open_islands = []
    solve_by_rules()
    if len(_open_islands) != 0:
        tree_search_solution()
    return deepcopy(grid)


def main():
    import sys
    grid_to_solve: list[list[Node]] = parse_args_empty(sys.argv)
    solve(grid_to_solve)
    draw_grid(grid_to_solve)
    #solution_grid = import_solution_grid(path)


if __name__ == "__main__":
    main()
