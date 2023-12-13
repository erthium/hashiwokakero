from node import Node
import pygame
import os

ABS_DIR: str = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FONT_PATH: str = ABS_DIR + '/data/SpaceMono-Regular.ttf'


def save_grid(grid: list[list[Node]], path: str = None) -> bool:
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


def import_solution_grid(path: str) -> list[list[Node]]:
    if not os.path.isfile(path) or not path.endswith(".csv"):
        print("ERROR: File does not exist.")
        return None
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


def direction_to_vector(direction: int) -> tuple[int, int]:
    assert direction >= 0 and direction < 4
    return [(-1, 0), (0, -1), (1, 0), (0, 1)][direction]


def grid_to_surface(root: pygame.Surface, grid: list[list[Node]], cell_unit: int) -> None:
    """
    Draws the background grid, bridges and islands to the passed surface.
    """
    pygame.init()
    font: pygame.font.Font = pygame.font.Font(DEFAULT_FONT_PATH, int(cell_unit / 2))
    grid_width = len(grid)
    grid_height = len(grid[0])
    root_size = root.get_size()
    line_thickness = int(cell_unit / 15)
    all_islands: list[Node] = []
    for i in range(grid_width):
        for j in range(grid_height):
            if grid[i][j].n_type == 1:
                all_islands.append(grid[i][j])

    # draw the grid
    root.fill((255, 255, 255))
    cursor = int(cell_unit / 2), int(cell_unit / 2)
    for j in range(grid_width):
        pygame.draw.line(root, (220, 220, 220), (cursor[0] + j * cell_unit, 0), (cursor[0] + j * cell_unit, root_size[1]), line_thickness // 2)
    for i in range(grid_height):
        pygame.draw.line(root, (220, 220, 220), (0, cursor[1] + i * cell_unit), (root_size[0], cursor[1] + i * cell_unit), line_thickness // 2)

    #draw the bridges
    drawn_bridges = []
    for i in range(grid_width):
        for j in range(grid_height):
            if grid[i][j].n_type == 2 and [i, j] not in drawn_bridges:
                bridge_direction = grid[i][j].b_dir
                current = [i, j]
                nodes_of_bridge = [current,]
                vector = direction_to_vector(bridge_direction)
                thickness = grid[i][j].b_thickness
                forward_found = False
                backward_found = False
                index = 1
                while not (forward_found and backward_found):
                    if not forward_found:
                        forward = [current[0] + vector[0] * index, current[1] + vector[1] * index]
                        if forward[0] >= 0 and forward[0] < grid_width and forward[1] >= 0 and forward[1] < grid_height:
                            nodes_of_bridge.append(forward)
                            if grid[forward[0]][forward[1]].n_type == 1:
                                forward_found = True
                                
                    if not backward_found:
                        backward = [current[0] - vector[0] * index, current[1] - vector[1] * index]
                        if backward[0] >= 0 and backward[0] < grid_width and backward[1] >= 0 and backward[1] < grid_height:
                            nodes_of_bridge.insert(0, backward)
                            if grid[backward[0]][backward[1]].n_type == 1:
                                backward_found = True
                    index += 1
                drawn_bridges.extend(nodes_of_bridge)
                start_pos = (nodes_of_bridge[0][0] * cell_unit + cell_unit // 2, nodes_of_bridge[0][1] * cell_unit + cell_unit // 2)
                end_pos = (nodes_of_bridge[-1][0] * cell_unit + cell_unit // 2, nodes_of_bridge[-1][1] * cell_unit + cell_unit // 2)
                if thickness == 1:
                    pygame.draw.line(root, (0, 0, 0), start_pos, end_pos, line_thickness)
                else:
                    opposite_direction = (bridge_direction + 1)
                    if opposite_direction % 2 == 0:
                        pygame.draw.line(root, (0, 0, 0), (start_pos[0] + cell_unit / 15, start_pos[1]), (end_pos[0] + cell_unit // 15, end_pos[1]), line_thickness)
                        pygame.draw.line(root, (0, 0, 0), (start_pos[0] - cell_unit / 15, start_pos[1]), (end_pos[0] - cell_unit // 15, end_pos[1]), line_thickness)
                    else:
                        pygame.draw.line(root, (0, 0, 0), (start_pos[0], start_pos[1] + cell_unit / 15), (end_pos[0], end_pos[1] + cell_unit // 15), line_thickness)
                        pygame.draw.line(root, (0, 0, 0), (start_pos[0], start_pos[1] - cell_unit / 15), (end_pos[0], end_pos[1] - cell_unit // 15), line_thickness)


    # draw the islands
    for island in all_islands:
        position = (cell_unit // 2 + island.x * cell_unit, cell_unit // 2 + island.y * cell_unit)
        pygame.draw.circle(root, (0, 0, 0), position, int(cell_unit / 2.3))
        pygame.draw.circle(root, (255, 255, 255), position, int(cell_unit / 2.5))
        text_surface = font.render(str(island.i_count), False, (0, 0, 0))
        text_size = text_surface.get_size()
        root.blit(text_surface, (position[0] - text_size[0] / 2, position[1] - text_size[1] / 2))


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


def parse_args() -> list[list[Node]]:
    import sys, os
    if len(sys.argv) != 3:
        print("Usage: python3 visualiser.py <-e||-s> <path_to_grid_file>")
        return -1
    path = sys.argv[2]
    if not os.path.isfile(path):
        print("ERROR: File does not exist")
        return -1
    if sys.argv[1] == "-e":
        grid = import_empty_grid(path)
    elif sys.argv[1] == "-s":
        grid = import_solution_grid(path)
    else:
        print("Usage: python3 export.py <-e||-s> <path_to_grid_file>")
        return -1
    return grid


def main():
    grid = parse_args()
    if grid == -1:
        return
    output_image(grid, "images/test.png", 300)


if __name__ == "__main__":
    main()
