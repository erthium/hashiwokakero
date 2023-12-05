import pygame
from ui_elements import Button, ProcessElements
from node import Node


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
            else: button_text = "|" * grid[i][j].b_thickness if grid[i][j].b_dir == 1 else "-" * grid[i][j].b_thickness
            
            new_button = Button(root, i * cell_size[0], j * cell_size[1], cell_size[0], cell_size[1], text=button_text,font_size=24)
            all_buttons.append(new_button)
    while loop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop = False
        root.fill((255, 255, 255))
        for button in all_buttons:
            button.render()
        pygame.display.update()


def main():
    import sys, os
    cl_args = sys.argv[1:]
    if len(cl_args) != 1:
        print("Usage: python3 grid_visualizer.py <path_to_grid_file>")
        return
    path = cl_args[0]
    if not os.path.isfile(path) or not path.endswith(".csv"):
        print("ERROR: File does not exist")
        return
    grid = []
    with open(path, 'r') as file:
        pass
    

if __name__ == "__main__":
    main()

