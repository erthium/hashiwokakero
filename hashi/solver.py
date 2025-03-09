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
TODO: Create an algorithm for brute-force solving, to be used
after solving with the base rules and remaining a situation
which may contain multiple solutions
"""

from dataclasses import dataclass

from node import Node, direction_to_vector, nodes_to_direction, is_in_grid
from visualiser import draw_grid, print_node_data
from arg_parser import parse_args_empty
from copy import deepcopy


# global variables

## general
_grid: list[list[Node]] = None
_grid_w: int = None
_grid_h: int = None
_open_islands: list[Node] = None

## brute force
_group_count: int = None
_groups: list[list[Node]] = None
_current_moves: list = None # list of (Node, Node, thickness) tuples
_current_applied_moves: list = None # list of (Node, Node, thickness) tuples
_correct_solutions: list = None # list of (grid, steps) tuples
_by_rule_move_log: list = None # list of (Node, Node, thickness) tuples

## difficulty prediction
_step_count_rules: int = None
_step_count_brutal: int = None


## Preparation

def collect_garbage(func):
    """
    To reset global variables after each solve call.\n
    Only to be used in the main -public- solve function.
    """
    def wrapper(*args, **kwargs):
        global _grid, _grid_w, _grid_h, _open_islands, _group_count, _groups, _current_moves, _current_applied_moves, _correct_solutions, _by_rule_move_log, _step_count_rules, _step_count_brutal
        _open_islands = []
        _current_moves = []
        _current_applied_moves = []
        _correct_solutions = []
        _by_rule_move_log = []
        _step_count_rules = 0
        _step_count_brutal = 0
        result = func(*args, **kwargs)
        _grid = None
        _grid_w = None
        _grid_h = None
        _open_islands = None
        _group_count = None
        _groups = None
        _current_moves = None
        _current_applied_moves = None
        _correct_solutions = None
        _by_rule_move_log = None
        _step_count_rules = None
        _step_count_brutal = None
        return result
    return wrapper


def copy_grid(grid: list[list[Node]]) -> list[list[Node]]:
    """
    Returns a deep copy of the given grid.
    """
    new_grid = []
    for i in range(len(grid)):
        new_grid.append([])
        for j in range(len(grid[0])):
            new_node = Node(grid[i][j].x, grid[i][j].y)
            new_node.n_type = grid[i][j].n_type
            new_node.i_count = grid[i][j].i_count
            new_node.b_thickness = grid[i][j].b_thickness
            new_node.b_dir = grid[i][j].b_dir
            new_node.current_in = grid[i][j].current_in
            new_grid[i].append(new_node)
    return new_grid


def compare_grids(grid_a: list[list[Node]], grid_b: list[list[Node]]) -> bool:
    """
    Compares two grids and returns True if they are the same, False otherwise.
    """
    for i in range(len(grid_a)):
        for j in range(len(grid_a[0])):
            if grid_a[i][j].n_type != grid_b[i][j].n_type:
                return False
            if grid_a[i][j].n_type == 1:
                if grid_a[i][j].i_count != grid_b[i][j].i_count:
                    return False
            elif grid_a[i][j].n_type == 2:
                if grid_a[i][j].b_thickness != grid_b[i][j].b_thickness or grid_a[i][j].b_dir != grid_b[i][j].b_dir:
                    return False
    return True


@dataclass
class Solution:
    grid: list[list[Node]]
    rule_steps: int
    brutal_steps: int


## Functions for solving by rules

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
    is_c_one = _grid[x][y].i_count == 1
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
                            if hit_node.needed >= 2:
                                if _grid[x][y].needed >= 2:
                                    output[direction] = 2
                                else:
                                    output[direction] = 1
                            else:
                                output[direction] = 1
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


def establish_bridge(x: int, y: int, direction: int, thickness: int, log_moves: bool = False) -> None:
    """
    Takes an island node and builds a bridge in the given direction and thickness.\n
    Also increases the current_in of the target node by thickness.\n
    Assumes the bridge is possible, and the node is an island.\n
    Works if there is already a single bridge in the direction.\n
    Returns nothing.
    """
    global _grid
    assert is_in_grid(x, y, len(_grid), len(_grid[0]))
    assert _grid[x][y].n_type == 1
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
    
    if log_moves:
        global _by_rule_move_log
        _by_rule_move_log.append((_grid[x][y], _grid[check_x][check_y], thickness))
    #print(f"Established bridge of thickness {thickness} in direction {direction} from ({x}, {y}) to ({check_x}, {check_y})")


def solve_by_rules(log_moves: bool = False) -> None:
    """
    Do not use directly, use solve() instead.\n
    Apply essential principles to the grid.\n
    If no operation is done after iterating through all open islands, the puzzle is unsolvable by essential rules.\n
    If no open islands are left, the puzzle is solved.\n
    Returns nothing.
    """
    global _grid, _open_islands, _step_count_rules
    # get all open islands
    any_operation_done: bool = True
    while any_operation_done: # if no operation was done, puzzle is unsolvable
        any_operation_done = False
        for i in range(len(_open_islands) - 1, -1, -1): # check every open island each cycle
            _step_count_rules += 1
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
                    establish_bridge(island.x, island.y, direction, thickness, log_moves)
                _open_islands.remove(island)
                any_operation_done = True

            ## if only one direction is possible, build bridge
            elif dir == 1:
                for direction, thickness in direction_info.items():
                    establish_bridge(island.x, island.y, direction, thickness, log_moves)
                    _open_islands.remove(island)
                    any_operation_done = True

            ## if island has to send at least 1 bridge in all directions...
            elif island.needed // 2 == dir - 1:
                if island.needed % 2 == 1:
                    for direction, thickness in direction_info.items():
                        establish_bridge(island.x, island.y, direction, 1, log_moves)
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
                                establish_bridge(island.x, island.y, direction, 1, log_moves)
                                any_operation_done = True


## Functions for solving by brute force

### Functions for moves


def de_establish_bridge(x: int, y: int, direction: int, thickness: int) -> None:
    """
    Takes an island node and removes a bridge in the given direction and thickness.\n
    Also decreases the current_in of the target node by thickness.\n
    Assumes the bridge is possible, and the node is an island.\n
    Works if there is already a single bridge in the direction.\n
    Returns nothing.
    """
    global _grid
    assert is_in_grid(x, y, len(_grid), len(_grid[0]))
    assert _grid[x][y].n_type == 1
    _grid[x][y].current_in -= thickness
    dir_vector = direction_to_vector(direction)
    check_x = x + dir_vector[0]
    check_y = y + dir_vector[1]
    while _grid[check_x][check_y].n_type != 1:
        assert _grid[check_x][check_y].n_type == 2
        assert _grid[check_x][check_y].b_dir == direction % 2, f"Bridge direction is {direction % 2}, but should be {_grid[check_x][check_y].b_dir}"
        assert _grid[check_x][check_y].b_thickness >= thickness
        if _grid[check_x][check_y].b_thickness == thickness:
            _grid[check_x][check_y].make_empty()
        else:
            _grid[check_x][check_y].b_thickness -= thickness
        check_x += dir_vector[0]
        check_y += dir_vector[1]
    _grid[check_x][check_y].current_in -= thickness


def make_move(node_a: Node, node_b: Node, thickness: int) -> None:
    global _current_applied_moves, _step_count_brutal
    direction = nodes_to_direction(node_a, node_b)
    establish_bridge(node_a.x, node_a.y, direction, thickness)
    _current_applied_moves.append((node_a, node_b, thickness))
    _step_count_brutal += 1


def take_back_move() -> None:
    global _current_applied_moves, _step_count_brutal
    last_move = _current_applied_moves.pop()
    direction = nodes_to_direction(last_move[0], last_move[1])
    de_establish_bridge(last_move[0].x, last_move[0].y, direction, last_move[2])
    _step_count_brutal += 1


def get_moves() -> None:
    global _current_moves
    _current_moves = []
    for island in _open_islands:
        for direction, thickness in bridge_out_info(island.x, island.y).items():
            dir_vector = direction_to_vector(direction)
            check_x = island.x + dir_vector[0]
            check_y = island.y + dir_vector[1]
            while _grid[check_x][check_y].n_type != 1:
                check_x += dir_vector[0]
                check_y += dir_vector[1]

            # if node_a and node_b reversed is already in moves, skip
            already_found = False
            for move in _current_moves:
                node_a = move[0]
                node_b = move[1]
                if island.x == node_b.x and island.y == node_b.y and check_x == node_a.x and check_y == node_a.y:
                    already_found = True
                    break
            if already_found:
                continue

            if thickness == 2:
                _current_moves.append((_grid[island.x][island.y], _grid[check_x][check_y], 1))
                _current_moves.append((_grid[island.x][island.y], _grid[check_x][check_y], 2))
            else:
                _current_moves.append((_grid[island.x][island.y], _grid[check_x][check_y], thickness))

    for move in _current_moves:
        node_a = move[0]
        node_b = move[1]
        thickness = move[2]


### Functions for checking correctness

def _get_groups() -> None:
    """
    Searches through the entire grid and sets the list of open islands in each connected island group.\n
    Also sets the '_group_count: int' global variable.\n
    _groups Format: [ [N, N, N], [N, N], [N, N, N, N, N], ...]\n
    If there is a group with no open islands while _group_count is not 1, the solution is wrong.\n
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


def is_solution_wrong() -> bool:
    """
    Checks if the solution is wrong by checking the groups.\n
    Returns True if the solution is wrong, False otherwise.
    """
    global _group_count, _groups
    _get_groups()
    if _group_count != 1:
        for group in _groups:
            if len(group) == 0:
                return True
    return False


def is_solution_correct() -> bool:
    """
    Checks if the solution is correct by checking the groups.\n
    Returns True if the solution is correct, False otherwise.
    """
    global _group_count, _groups
    _get_groups()
    if _group_count == 1 and len(_groups[0]) == 0:
        return True
    return False


def copy_correct_solution() -> None:
    global _grid, _correct_solutions, _step_count_brutal
    _correct_solutions.append((copy_grid(_grid), _step_count_brutal))


### Main brute force function
depth = 0
def solve_brutally() -> None:
    """
    Do not use directly, use solve() instead.\n
    The main brute force algorithm.\n
    Checks all possible moves, tries them, and if the solution is correct, stops.\n
    Returns nothing.

    |-- Main Flow --|

    - Get all moves
    - For all the moves
        - Make the move
        - Check if the solution is correct
            - If correct, copy the grid to solutions
        - Recursively call the function
        - Take the move back
    """
    """ First method: Try all f** moves
    global depth
    if len(_correct_solutions) != 0:
        return
    depth += 1
    print(f"Depth: {depth} with number of moves: {len(_current_moves)} with solution count: {len(_correct_solutions)}")
    #draw_grid(_grid)
    get_moves()
    if is_solution_wrong():
        depth -= 1
        return
    for move in _current_moves:
        node_a = move[0]
        node_b = move[1]
        thickness = move[2]
        make_move(node_a, node_b, thickness)
        if is_solution_correct():
            copy_correct_solution()
        else:
            solve_brutally()
        take_back_move()
    depth -= 1
    """
    # Second method: try one & send back to solving by rules
    global _by_rule_move_log
    #draw_grid(_grid)
    get_moves()
    if is_solution_wrong():
        return
    for move in _current_moves:
        node_a = move[0]
        node_b = move[1]
        thickness = move[2]
        make_move(node_a, node_b, thickness)
        solve_by_rules(log_moves=True)
        if is_solution_correct():
            copy_correct_solution()
            break
        else:
            for by_rule_move in _by_rule_move_log:
                direction = nodes_to_direction(by_rule_move[0], by_rule_move[1])
                de_establish_bridge(by_rule_move[0].x, by_rule_move[0].y, direction, by_rule_move[2])
        take_back_move()


## Main solve function

@collect_garbage
def solve(grid: list[list[Node]]) -> list[Solution]:
    """
    Solve the given grid by trying rules and brute forcing when it is stuck.\n
    Returns a list of Solution objects.\n
    If the grid is unsolvable, god help us all.
    """
    # Prepare to solve
    global _grid, _grid_h, _grid_w, _open_islands, _step_count_rules, _step_count_brutal, _correct_solutions
    _grid = grid
    _grid_w = len(grid)
    _grid_h = len(grid[0])
    for i in range(len(_grid)):
        for j in range(len(_grid[0])):
            if _grid[i][j].n_type == 1:
                _open_islands.append(_grid[i][j])
    # Solve by rules, if not completed, solve by brute force
    solve_by_rules()
    if len(_open_islands) == 0:
        print("Solved by rules")
        only_solution = Solution(grid=copy_grid(_grid), rule_steps=_step_count_rules, brutal_steps=0)
        return [only_solution]
    else:
        print("Solving by brute force")
        grid_before = copy_grid(_grid)
        solve_brutally()
        grid_after = copy_grid(_grid)

        if len(_correct_solutions) == 0:
            print("Somehow brute force did not work")
            is_the_same = compare_grids(grid_before, grid_after)
            print(f"Grids are the same: {is_the_same}")

        solutions = []
        for solution in _correct_solutions:
            solutions.append(Solution(grid=solution[0], rule_steps=_step_count_rules, brutal_steps=solution[1]))
        return solutions


def main():
    import sys
    grid_to_solve: list[list[Node]] = parse_args_empty(sys.argv)
    all_solutions = solve(grid_to_solve)
    print(f"Number of solutions: {len(all_solutions)}")
    draw_grid(all_solutions[0].grid)


if __name__ == "__main__":
    main()
