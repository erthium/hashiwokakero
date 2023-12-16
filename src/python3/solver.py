"""
Solver Algorithm
----------------
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

from time import sleep
from node import Node
from visualiser import draw_grid, print_node_data
from export import import_empty_grid, import_solution_grid

def direction_to_vector(direction: int) -> tuple[int, int]:
    assert direction >= 0 and direction < 4
    return [(-1, 0), (0, -1), (1, 0), (0, 1)][direction]


def bridge_out_info(grid: list[list[Node]], x: int, y: int) -> dict[int, int]:
    """
    {0->left, 1->up, 2->right, 3->down}
    """
    assert grid[x][y].n_type == 1
    assert x >= 0 and x < len(grid)
    assert y >= 0 and y < len(grid[0])
    output = {}
    is_c_one = grid[x][y].needed == 1
    # first, calculate the input count
    for direction in [0, 1, 2, 3]:
        following_input_bridge = False
        dir_vector = direction_to_vector(direction)
        check_x = x + dir_vector[0]
        check_y = y + dir_vector[1]
        found_target = False
        while check_x >= 0 and check_x < len(grid) and check_y >= 0 and check_y < len(grid[0]) and not found_target:
            hit_node = grid[check_x][check_y]
            if hit_node.n_type == 0:
                check_x += dir_vector[0]
                check_y += dir_vector[1]
            elif hit_node.n_type == 1:
                # Find the max possible input to the hit node
                if following_input_bridge and hit_node.needed >= 1:
                        output[direction] = 1
                else:
                    if is_c_one:
                        if hit_node.needed >= 1:
                            output[direction] = 1
                    else:
                        if hit_node.needed >= 1:
                            output[direction] = 2 if hit_node.needed >= 2 else hit_node.needed
                found_target = True
            elif hit_node.n_type == 2:
                if grid[check_x][check_y].b_dir == direction % 2:
                    if grid[check_x][check_y].b_thickness == 1:
                        following_input_bridge = True
                        check_x += dir_vector[0]
                        check_y += dir_vector[1]
                    else:
                        found_target = True
                else:
                    found_target = True
    #print(f"Output info: {output}")
    return output

def establish_bridge(grid: list[list[Node]], x: int, y: int, direction: int, thickness: int) -> None:
    assert grid[x][y].n_type == 1
    assert x >= 0 and x < len(grid)
    assert y >= 0 and y < len(grid[0])
    # increase the current_in of both nodes by thickness
    # make the nodes in between bridges
    grid[x][y].current_in += thickness
    dir_vector = direction_to_vector(direction)
    check_x = x + dir_vector[0]
    check_y = y + dir_vector[1]
    while grid[check_x][check_y].n_type != 1:
        if grid[check_x][check_y].n_type == 2:
            assert grid[check_x][check_y].b_dir == direction % 2
            assert grid[check_x][check_y].b_thickness == 1
            assert grid[check_x][check_y].b_thickness + thickness == 2
            grid[check_x][check_y].b_thickness += thickness
        else:
            grid[check_x][check_y].make_bridge(thickness, direction % 2)
        check_x += dir_vector[0]
        check_y += dir_vector[1]
    grid[check_x][check_y].current_in += thickness
    #print(f"Established bridge of thickness {thickness} in direction {direction} from ({x}, {y}) to ({check_x}, {check_y})")


def solve(grid: list[list[Node]]) -> bool:
    """
    Get an empty grid and applies essential principles to solve it.\n
    Return True if solvable, False if unsolvable.\n
    If grid is half-solved, nodes need to be marked with 
    current out and bridges need to be marked as bridges.
    """
    # get all open islands
    open_islands: list[Node] = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j].n_type == 1:
                open_islands.append(grid[i][j])
    
    any_operation_done: bool = True
    while any_operation_done: # if no operation was done, puzzle is unsolvable
        any_operation_done = False
        for i in range(len(open_islands) - 1, 0, -1): # check every open island each cycle
            island  = open_islands[i]
            #print_node_data(island)
            #draw_grid(grid)
            # if island is already closed, skip
            # occurs when an island send a bridge to this one, and not closed it
            if island.needed == 0:
                open_islands.pop(i)
                continue

            # get current node info
            direction_info: dict[int, int] = bridge_out_info(grid, island.x, island.y)
            max_out = sum(direction_info.values())
            dir = len(list(direction_info.keys()))
            
            #print(f"Island at ({island.x}, {island.y})")
            #print(f"Dirs: {direction_info}")
            #print(f"Max out: {max_out}")
            
            # main part of the algorithm
            ## if needed == max_out, build all bridges
            if island.needed == max_out:
                for direction, thickness in direction_info.items():
                    establish_bridge(grid, island.x, island.y, direction, thickness)
                open_islands.remove(island)
                any_operation_done = True

            ## if only one direction is possible, build bridge
            elif dir == 1:
                for direction, thickness in direction_info.items():
                    establish_bridge(grid, island.x, island.y, direction, thickness)
                    open_islands.remove(island)
                    any_operation_done = True

            ## if island has to send at least 1 bridge in all directions...
            elif island.needed // 2 == dir - 1:
                if island.needed % 2 == 1:
                    for direction, thickness in direction_info.items():
                        establish_bridge(grid, island.x, island.y, direction, 1)
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
                                establish_bridge(grid, island.x, island.y, direction, 1)
                                any_operation_done = True
    return open_islands



def main():
    path = "puzzles/puzzle_3.csv"
    grid_to_solve = import_empty_grid(path)
    open_islands = solve(grid_to_solve)
    for island in open_islands:
        print_node_data(island)
    draw_grid(grid_to_solve)
    #solution_grid = import_solution_grid(path)




if __name__ == "__main__":
    main()
