from node import Node, direction_to_vector, is_in_grid
from arg_parser import parse_args
import pygame
import os

def save_grid(grid: list[list[Node]], path: str = None) -> bool:
    """
    Takes a 2D grid of nodes and saves it to a csv file.\n
    If no path was given, saves it to puzzles/puzzle_{number_of_puzzles}.csv\n
    Returns True if successful, False otherwise.
    """
    try:
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
                    if node.b_dir == 0:
                        bridge_code = -1 if node.b_thickness == 1 else -2
                    elif node.b_dir == 1:
                        bridge_code = -3 if node.b_thickness == 1 else -4
                    solution_grid += str(bridge_code)

        with open(path, 'w') as file:
            file.write(f"{len(grid)};;{len(grid[0])};;")
            file.write(f"{empty_grid};;")
            file.write(f"{solution_grid}\n")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def import_solution_grid(path: str) -> list[list[Node]]:
    """
    Takes a path to a csv file.\n
    Returns a 2D list of nodes, the solution grid with bridges and islands.
    """
    if not os.path.isfile(path):
        print(f"ERROR: File does not exist in '{path}'")
        return
    if not path.endswith(".csv"):
        print(f"ERROR: File '{path}' is in csv format.")
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
    i = 0
    while i < len(temp_sol) - 1: # -1 for the newline character
        if temp_sol[i] == '-':
            solution_grid.append(int(temp_sol[i] + temp_sol[i+1]))
            i += 1
        else: solution_grid.append(int(temp_sol[i]))
        i += 1
    for i in range(w):
        grid.append([])
        for j in range(h):
            cursor = i * h + j
            grid[i].append(Node(i, j))
            current_node_code = solution_grid[cursor]
            if current_node_code > 0:
                grid[i][j].make_island(current_node_code)
            #bridge_info = [(1, 0), (2, 0), (1, 1), (2, 1)][(solution_grid[cursor] * -1) - 1]
            # let's go for general switch-case for simplicity, since there is only 4 type of bridges
            elif current_node_code == -1:
                grid[i][j].make_bridge(1, 0)
            elif current_node_code == -2:
                grid[i][j].make_bridge(2, 0)
            elif current_node_code == -3:
                grid[i][j].make_bridge(1, 1)
            elif current_node_code == -4:
                grid[i][j].make_bridge(2, 1)
            elif current_node_code < 0:
                print(f"ERROR: Unsupported cell number '{current_node_code}' at index {i}x{j}.")
                return None
    return grid


def import_empty_grid(path: str) -> list[list[Node]]:
    """
    Takes a path to a csv file.\n
    Returns a 2D list of nodes, the empty grid without bridges and only islands.
    """
    if not os.path.isfile(path):
        print(f"ERROR: File does not exist in '{path}'")
        return
    if not path.endswith(".csv"):
        print(f"ERROR: File '{path}' is in csv format.")
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


def output_image(grid: list[list[Node]], path: str, cell_unit: int = 200) -> bool:
    """
    Takes grid, cell size of every node in pixels and path 
    for output; and outputs an image of the grid.\n
    Total image pixel width or height cannot be larger than 20_000.\n
    Supports BMP, TGA, PNG and JPEG format.\n
    Higher cell size leads to better resolution in output image.\n
    Better to have cell_unit as an even number.\n
    Returns True if successful, False otherwise.
    """
    from visualiser import grid_to_surface
    root_width = len(grid) * cell_unit
    root_height = len(grid[0]) * cell_unit
    if root_width > 20_000 or root_height > 20_000:
        print("ERROR: Image size cannot be larger than 20_000 pixels.")
        return False
    root = pygame.Surface((root_width , root_height))
    try:
        grid_to_surface(root, grid, cell_unit)
        pygame.image.save(root, path)
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    return True


def main():
    import sys
    grid = parse_args(sys.argv)
    if grid == -1:
        return
    output_image(grid, "images/test.png", 300)


if __name__ == "__main__":
    main()
