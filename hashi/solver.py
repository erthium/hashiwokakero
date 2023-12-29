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
## general
_grid: list[list[Node]] = None
_grid_w: int = None
_grid_h: int = None
_open_islands: list[Node] = None
## tree search variables
_group_count: int = None
_groups: list[list[Node]] = None
_moves: list[list[Node, Node, int]] = None # [Node, Node, thickness]
_move_log: list[list[Node, Node, int]] = None # [Node, Node, thickness]
_depth_indexes: list[int] = None


def collect_garbage(func):
    """
    To reset global variables after each solve call.\n
    Only to be used in the main -public- solve function.
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        global _grid, _grid_w, _grid_h, _open_islands, _group_count, _groups, _moves, _move_log, _depth_indexes
        _grid = None
        _grid_w = None
        _grid_h = None
        _open_islands = None
        _group_count = None
        _groups = None
        _moves = None
        _move_log = None
        _depth_indexes = None
        return result
    return wrapper


def bridge_out_info(x: int, y: int) -> dict[int, int]:
    """
    Takes an island node and returns a dictionary of possible bridge directions and their output count.\n
    Output Format: {0->left, 1->up, 2->right, 3->down}
    """
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
    """
    Takes an island node and builds a bridge in the given direction and thickness.\n
    Also increases the current_in of the target node by thickness.\n
    Assumes the bridge is possible, and the node is an island.\n
    Works if there is already a single bridge in the direction.\n
    Returns nothing.
    """
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
            assert _grid[check_x][check_y].b_dir == direction % 2, f"Bridge direction is {direction % 2}, but should be {_grid[check_x][check_y].b_dir}"
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
    Do not use directly, use solve() instead.\n
    Apply essential principles to the grid.\n
    If no operation is done after iterating through all open islands, the puzzle is unsolvable by essential rules.\n
    If no open islands are left, the puzzle is solved.\n
    Returns nothing.
    """
    global _grid, _open_islands
    # get all open islands
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


def get_moves() -> None:
    """
    Do not use directly, use solve() instead.\n
    TODO: Could be optimized by creating a new function like bridge_out_info, but returning hit Nodes directly.\n 
    """
    global _moves
    _moves = []
    for island in _open_islands:
        for direction, thickness in bridge_out_info(island.x, island.y).items():
            dir_vector = direction_to_vector(direction)
            check_x = island.x + dir_vector[0]
            check_y = island.y + dir_vector[1]
            while _grid[check_x][check_y].n_type != 1:
                check_x += dir_vector[0]
                check_y += dir_vector[1]
            # check if move is already in moves
            already_in_moves = False
            for move in _moves:
                if move[1].x == island.x and move[1].y == island.y and move[0].x == check_x and move[0].y == check_y: 
                    already_in_moves = True
                    break
            if not already_in_moves:
                _moves.append([island, _grid[check_x][check_y], thickness])


def take_back_move() -> None:
    # pop the last move from move log
    # de-establish the bridge according to the move
    global _move_log, _depth_indexes
    move = _move_log.pop()
    _depth_indexes.pop()
    direction = -1
    if move[0].x == move[1].x: direction = 0 if move[0].y < move[1].y else 2
    else: direction = 1 if move[0].x < move[1].x else 3
    dir_vector = direction_to_vector(direction)
    check_x = move[0].x + dir_vector[0]
    check_y = move[0].y + dir_vector[1]
    is_following_bridge = _grid[check_x][check_y].b_thickness != move[2]
    while _grid[check_x][check_y].n_type != 1:
        if is_following_bridge: 
            _grid[check_x][check_y].b_thickness -= 1
        else:
            _grid[check_x][check_y].make_empty()
        check_x += dir_vector[0]
        check_y += dir_vector[1]
    move[0].current_in -= move[2]
    move[0].current_in -= move[2]
    # for debug purposes
    assert _grid[check_x][check_y].n_type == 1
    assert _grid[check_x][check_y].x == move[1].x and _grid[check_x][check_y].y == move[1].y
    get_moves()


def get_groups() -> None:
    """
    Searches through the entire grid and sets the list of open islands in each connected island group.\n
    Also sets the '_group_count: int' global variable.\n
    _groups Format: [ [N, N, N], [N, N], [N, N, N, N, N], ...]\n
    If there is a group with no open islands, the solution is wrong.\n
    If the list is empty and _group_count is 1, the puzzle is solved.
    """
    global _grid, _group_count, _groups
    _group_count = 0
    _groups = []
    grid_w = len(_grid)
    grid_h = len(_grid[0])
    visited = [[False for i in range(grid_h)] for j in range(grid_w)]
    for i in range(grid_w):
        for j in range(grid_h):
            if _grid[i][j].n_type == 1 and not visited[i][j]:
                _group_count += 1
                _groups.append([])
                stack = [(i, j)]
                while len(stack) != 0:
                    x, y = stack.pop()
                    if not visited[x][y]:
                        visited[x][y] = True
                        if _grid[x][y].needed != 0:
                            _groups[-1].append(_grid[x][y])
                        for direction in [0, 1, 2, 3]:
                            dir_vector = direction_to_vector(direction)
                            check_x = x + dir_vector[0]
                            check_y = y + dir_vector[1]
                            if is_in_grid(check_x, check_y, grid_w, grid_h):
                                if _grid[check_x][check_y].n_type == 2 and not visited[check_x][check_y] and _grid[check_x][check_y].b_dir == direction % 2:
                                    while _grid[check_x][check_y].n_type != 1:
                                        visited[check_x][check_y] = True
                                        check_x += dir_vector[0]
                                        check_y += dir_vector[1]
                                    stack.append((check_x, check_y))


def is_unsolvable() -> bool:
    """
    Calculates the island groups and checks if any of them have no open islands.\n
    Returns True if the puzzle is unsolvable, False otherwise.
    """
    get_groups()
    for group in _groups:
        if len(group) == 0:
            return True
    return False
    

def solve_brutally() -> None:
    """
    Do not use directly, use solve() instead.\n
    """
    global _grid, _open_islands, _move_log, _depth_indexes
    depth = -1
    get_moves()
    while len(_moves) > 0:
        get_moves()
        depth += 1
        if len(_depth_indexes) <= depth:
            _depth_indexes.append(0)
        else: 
            _depth_indexes[depth] += 1
        if _depth_indexes[depth] >= len(_moves):
            take_back_move()
            depth -= 1
            continue
        move = _moves[_depth_indexes[depth]]
        _move_log.append(move)
        direction = -1
        if move[0].x == move[1].x: direction = 2 if move[0].y < move[1].y else 0
        else: direction = 3 if move[0].x < move[1].x else 1
        establish_bridge(move[0].x, move[0].y, direction, move[2])
        if is_unsolvable():
            take_back_move()
            depth -= 1
            continue
        

@collect_garbage
def solve(grid: list[list[Node]]) -> list[list[Node]]:
    """
    Solve the given grid by trying rules and brute forcing when it is stuck.\n
    Return the solved grid.
    """
    global _grid, _grid_h, _grid_w, _open_islands, _move_log, _depth_indexes
    _grid = grid
    _grid_w = len(grid)
    _grid_h = len(grid[0])
    _open_islands = []
    _move_log = []
    _depth_indexes = []
    for i in range(len(_grid)):
        for j in range(len(_grid[0])):
            if _grid[i][j].n_type == 1:
                _open_islands.append(_grid[i][j])
    solve_by_rules()
    if len(_open_islands) != 0:
        solve_brutally()
    return deepcopy(grid)


def main():
    import sys
    grid_to_solve: list[list[Node]] = parse_args_empty(sys.argv)
    solve(grid_to_solve)
    draw_grid(grid_to_solve)
    #solution_grid = import_solution_grid(path)


if __name__ == "__main__":
    main()
