import pygame
from ui_elements import Button, ProcessElements
from node import Node
from export import import_empty_grid, import_solution_grid

def print_node_data(node: Node) -> None:
    print(f"Node at ({node.x}, {node.y})")
    print(f"Type: {node.n_type}")
    print(f"Island count: {node.i_count}")
    print(f"Bridge thickness: {node.b_thickness}")
    print(f"Bridge direction: {node.b_dir}", end="\n\n")


def draw_grid(grid: list[list[Node]]) -> None:
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


def main():
    import sys, os
    if len(sys.argv) != 3:
        print("Usage: python3 grid_visualizer.py <-e||-s> <path_to_grid_file>")
        return
    path = sys.argv[2]
    if not os.path.isfile(path):
        print("ERROR: File does not exist")
        return
    if sys.argv[1] == "-e":
        grid = import_empty_grid(path)
    elif sys.argv[1] == "-s":
        grid = import_solution_grid(path)
    else:
        print("Usage: python3 grid_visualizer.py <-e||-s> <path_to_grid_file>")
        return
    draw_grid(grid)
        
    

if __name__ == "__main__":
    main()
