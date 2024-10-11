import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


class Node:
    def __init__(self, x, y):
        self.x: int = x
        self.y: int = y
        self.n_type: int = 0          # 0->empty, 1->island, 2->bridge

        self.i_count: int = -1        # island count 1-8

        self.b_thickness: int = -1    # bridge thickness 1-2
        self.b_dir: int = -1          # 0->horizontal, 1->vertical

        # solver necessary property
        self.current_in: int = 0

    # solver necessary property
    @property
    def needed(self) -> int:
        return self.i_count - self.current_in

    def make_empty(self) -> None:
        self.n_type = 0
        self.i_count = -1
        self.b_thickness = -1
        self.b_dir = -1

    def make_island(self, i_count: int) -> None:
        self.n_type = 1
        self.i_count = i_count
    
    def make_bridge(self, b_thickness: int, b_dir: int) -> None:
        self.n_type = 2
        self.b_thickness = b_thickness
        self.b_dir = b_dir


def direction_to_vector(direction: int) -> tuple[int, int]:
    assert direction >= 0 and direction < 4
    return [(-1, 0), (0, -1), (1, 0), (0, 1)][direction]


def is_in_grid(x: int, y: int, grid_w: int, grid_h: int) -> bool:
    return x >= 0 and x < grid_w and y >= 0 and y < grid_h
