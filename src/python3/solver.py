from node import Node
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

def direction_to_vector(direction: int) -> tuple[int, int]:
    assert direction >= 0 and direction < 4
    return [(-1, 0), (0, -1), (1, 0), (0, 1)][direction]

def get_bridge_info(grid: list[list[Node]], x: int, y: int) -> dict[int, int]:
    """
    0->left, 1->up, 2->right, 3->down, -1->current bridge input count
    """
    assert grid[x][y].n_type == 1
    assert x >= 0 and x < len(grid)
    assert y >= 0 and y < len(grid[0])
    output = {-1: 0, 0: 0, 1: 0, 2: 0, 3: 0}
    for direction in [0, 1, 2, 3]:
        dir_vector = direction_to_vector(direction)
        check_x = x + dir_vector[0]
        check_y = y + dir_vector[1]
        if grid[check_x][check_y].n_type == 2:
            if grid[check_x][check_y].b_dir % 2 == direction:
                output[-1] += grid[check_x][check_y].b_thickness
                continue
        while check_x >= 0 and check_x < len(grid) and check_y >= 0 and check_y < len(grid[0]):
            hit_node = grid[check_x][check_y]
            if hit_node.n_type == 0:
                check_x += dir_vector[0]
                check_y += dir_vector[1]
            elif hit_node.n_type == 1:
                # Find the max possible input to the hit node
                hit_node_max_input = 0
                for hit_dir in [0, 1, 2, 3]:
                    hit_side = direction_to_vector(hit_dir)
                    if grid[check_x + hit_side[0]][check_y + hit_side[1]].n_type == 0:
                        hit_node_max_input += 1
                output[direction] = hit_node_max_input
                break
            elif hit_node.n_type == 2:
                break



def establish_bridge(grid: list[list[Node]], x: int, y: int, direction: int, thickness: int) -> None:
    assert grid[x][y].n_type == 1
    assert x >= 0 and x < len(grid)
    assert y >= 0 and y < len(grid[0])

def solve(grid: list[list[Node]]) -> bool:
    open_islands = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j].n_type == 1:
                open_islands.append(grid[i][j])
    
    any_operation_done = True
    while any_operation_done:
        any_operation_done = False
        for island in open_islands:
            direction_info = get_bridge_info(grid, island.x, island.y)
            max_out = sum(direction_info.values())
            current_input = direction_info[-1]
            bridges_needed = island.i_count - current_input
            if bridges_needed == max_out:
                for direction, thickness in direction_info.items():
                    establish_bridge(grid, island.x, island.y, direction, thickness)
                open_islands.remove(island)
                any_operation_done = True
            elif len(direction_info.keys()) == 1:
                establish_bridge(grid, island.x, island.y, direction_info.keys()[0], direction_info.values()[0])
                open_islands.remove(island)
                any_operation_done = True
            elif bridges_needed // 2 == len(direction_info.keys()) - 1 and bridges_needed % 2 == 1:
                for direction, _ in direction_info.items():
                    establish_bridge(grid, island.x, island.y, direction, 1)
                any_operation_done = True
    return len(open_islands) == 0



def main():
    pass



if __name__ == "__main__":
    main()

