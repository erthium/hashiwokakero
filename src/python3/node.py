class Node:
    def __init__(self, x, y):
        self.x: int = x
        self.y: int = y
        self.n_type: int = 0       # 0->empty, 1->island, 2->bridge

        self.i_count: int = -1     # island count 1-8

        self.b_thickness: int = -1    # bridge thickness
        self.b_dir: int = -1       #  0->horizontal, 1->vertical

    def make_island(self, i_count: int) -> None:
        self.n_type = 1
        self.i_count = i_count
    
    def make_bridge(self, b_thickness: int, b_dir: int) -> None:
        self.n_type = 2
        self.b_thickness = b_thickness
        self.b_dir = b_dir
