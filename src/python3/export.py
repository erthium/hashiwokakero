from node import Node
import os

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

def save_grid(grid: list[list[Node]], path: str = None) -> bool:
    if not check_if_grid_full(grid): 
        print("Grid is not full, generating another one...")
        return False
    if path is None:
        path = f"puzzles/puzzle_{len(os.listdir('puzzles'))}.csv"
    empty_grid: str = ""
    solution_grid: str = ""
    for line in grid:
        for node in line:
            if node.n_type == 1: 
                empty_grid += str(node.i_count)
                solution_grid += str(node.i_count)
            elif node.n_type == 0:
                empty_grid += '0'
                solution_grid += '0'
            else:
                empty_grid += '0'
                bridge_code = (node.b_thickness * -1) + (-2 * (node.b_dir))
                solution_grid += str(bridge_code)

    with open(path, 'w') as file:
        file.write(f"{len(grid)};;{len(grid[0])};;")
        file.write(f"{empty_grid};;")
        file.write(f"{solution_grid}\n")
    return True

def import_solution_grid(path: str) -> list[list[Node]]:
    if not os.path.isfile(path) or not path.endswith(".csv"):
        print("ERROR: File does not exist")
        return
    grid: list[list[Node]] = []
    w = None
    h = None
    temp_sol = None
    solution_grid = []
    with open(path, 'r') as file:
        w, h, _, temp_sol = file.readline().split(";;")
        w = int(w)
        h = int(h)
    #print(temp_sol)
    for i in range(len(temp_sol) - 1):# -1 for the newline character
        if temp_sol[i] == '-':
            solution_grid.append(int(temp_sol[i] + temp_sol[i+1]))
            i += 1
        else: solution_grid.append(int(temp_sol[i]))
    print(solution_grid)
    for i in range(w):
        grid.append([])
        for j in range(h):
            cursor = i * h + j
            grid[i].append(Node(i, j))
            if solution_grid[cursor] > 0:
                grid[i][j].make_island(solution_grid[cursor])
            elif solution_grid[cursor] < 0:
                bridge_info = [(1, 0), (2, 0), (1, 1), (2, 1)][(solution_grid[cursor] * -1) - 1]
                grid[i][j].make_bridge(*bridge_info)
    return grid

def import_empty_grid(path: str) -> list[list[Node]]:
    if not os.path.isfile(path) or not path.endswith(".csv"):
        print("ERROR: File does not exist")
        return
    grid: list[list[Node]] = []
    w = None
    h = None
    empty_grid = None
    with open(path, 'r') as file:
        w, h, empty_grid, _ = file.readline().split(";;")
        w = int(w)
        h = int(h)
        empty_grid = list(map(int, empty_grid))
    for i in range(w):
        grid.append([])
        for j in range(h):
            cursor = i * h + j
            grid[i].append(Node(i, j))
            if empty_grid[cursor] > 0:
                grid[i][j].make_island(empty_grid[cursor])
    return grid