""" --DEPRECATED--
def draw_grid_old(grid: list[list[Node]]) -> None:
    pygame.init()

    grid_width = len(grid)
    grid_height = len(grid[0])
    window_size = (800, 800)
    cell_size = (window_size[0] // grid_width, window_size[1] // grid_height)

    root = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Hashiwokakero Grid Visualizer")
    loop = True
    all_buttons = []
    for i in range(grid_width):
        for j in range(grid_height):
            button_text = ""
            if grid[i][j].n_type == 0: pass
            elif grid[i][j].n_type == 1: button_text = str(grid[i][j].i_count)
            else: button_text = ("|" if grid[i][j].b_dir == 1 else "-") * grid[i][j].b_thickness 
            
            new_button = Button(root, i * cell_size[0], j * cell_size[1],
                                cell_size[0], cell_size[1],
                                text=button_text,font_size=24,
                                click_function=print_node_data, args=(grid[i][j],))
            all_buttons.append(new_button)
    
    while loop:
        ALL_EVENTS: list[pygame.event.Event] = pygame.event.get()
        PRESSED: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        MOUSE_POS: tuple[int, int] = pygame.mouse.get_pos()
        for event in ALL_EVENTS:
            if event.type == pygame.QUIT:
                loop = False
        root.fill((255, 255, 255))
        ProcessElements(ALL_EVENTS, PRESSED, MOUSE_POS, all_buttons)
        for button in all_buttons:
            button.render()        
        pygame.display.update()
"""

import pygame
from ui_elements import Button, ProcessElements
from node import Node
from export import import_empty_grid, import_solution_grid, grid_to_surface, parse_args


def print_node_data(node: Node) -> None:
    """
    Debug necessary function, to check if drawn output is correct.
    """
    print(f"Node at ({node.x}, {node.y})")
    print(f"Type: {node.n_type}")
    print("-------------------------")
    print(f"Island count: {node.i_count}")
    print(f"Island current_in: {node.current_in}")
    print(f"Island needed: {node.needed}")
    print("-------------------------")
    print(f"Bridge thickness: {node.b_thickness}")
    print(f"Bridge direction: {node.b_dir}")
    print("-------------------------\n")


def draw_grid(grid: list[list[Node]]) -> None:
    """
    Takes a 2D list of nodes and draws it on the screen with Pygame.
    """
    pygame.init()
    grid_width = len(grid)
    grid_height = len(grid[0])
    ratio = grid_width / grid_height
    if ratio > 1:
        window_size = (800, int(800 / ratio))
    else:
        window_size = (int(800 * ratio), 800)
    cell_size = window_size[0] // grid_width
    root = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Hashiwokakero Grid Visualizer")
    loop = True
    while loop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop = False
        grid_to_surface(root, grid, cell_size)
        pygame.display.update()
        """
        user_input = input("Enter node coordinates (x y): ")
        if user_input == "" or user_input == " " or user_input == "q":
            loop = False
        node = list(map(int ,user_input.split()))
        if len(node) == 2:
            print_node_data(grid[node[0]][node[1]])
        """
    pygame.quit()


def main():
    import sys
    grid = parse_args(sys.argv)
    if grid == -1:
        return
    draw_grid(grid)


if __name__ == "__main__":
    main()
