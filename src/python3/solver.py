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

