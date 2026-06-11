"""
This script is used to create an alternative visualisation of the hashi puzzle using matplotlib.
The quality needs to be improved since this output will be printed on a book.
"""

import matplotlib.pyplot as plt

from hashi.core import Node


# Define constant color values with alpha channel
ISLAND_TEXT_COLOR = (0.46, 0.46, 0.46)
ISLAND_COLOR = (0.46, 0.46, 0.46)
BRIDGE_COLOR = (0.46, 0.46, 0.46)
EMPTY_CELL_COLOR = (1, 1, 1, 0.3)
GRID_LINE_COLOR = (0.92, 0.92, 0.92, 0.2)

# Drawing size constants
ISLAND_RADIUS = 0.4
BRIDGE_WIDTH_SINGLE = 0.08
BRIDGE_WIDTH_DOUBLE_OFFSET = 0.32  # Distance between double bridge lines (center to center)
ISLAND_FONT_SIZE = 18
GRID_LINE_WIDTH = 1.8  # Width of the grid lines

# Grid number display and placement
SHOW_X_NUMBERS = False  # Set to False to hide x-axis numbers
SHOW_Y_NUMBERS = False  # Set to False to hide y-axis numbers
X_NUMBERS_ON_TOP = True  # Set to True to show x-axis numbers on top
Y_NUMBERS_ON_RIGHT = False  # Set to True to show y-axis numbers on right


def draw_grid_on_axis(grid: list[list[Node]], ax: plt.Axes, island_font_size: float = ISLAND_FONT_SIZE) -> None:
  """
  Draws the grid on a caller-provided matplotlib axis. Used by `draw_grid`
  for standalone rendering and by `hashi.book` for multi-puzzle PDF pages.
  """
  grid_width = len(grid)
  grid_height = len(grid[0])
  ax.set_aspect('equal')
  ax.set_xlim(-1, grid_width)
  ax.set_ylim(-1, grid_height)
  ax.invert_yaxis()
  ax.set_xticks(range(grid_width))
  ax.set_yticks(range(grid_height))
  if SHOW_X_NUMBERS:
    ax.set_xticklabels([str(x) for x in range(grid_width)])
  else:
    ax.set_xticklabels("")
    ax.tick_params(axis='x', which='both', length=0)
  if SHOW_Y_NUMBERS:
    ax.set_yticklabels([str(y) for y in range(grid_height)])
  else:
    ax.set_yticklabels("")
    ax.tick_params(axis='y', which='both', length=0)

  if X_NUMBERS_ON_TOP:
    ax.xaxis.tick_top()
  else:
    ax.xaxis.tick_bottom()
  if Y_NUMBERS_ON_RIGHT:
    ax.yaxis.tick_right()
  else:
    ax.yaxis.tick_left()
  ax.grid(True, color=GRID_LINE_COLOR, linewidth=GRID_LINE_WIDTH, zorder=0)

  empty_cells = []
  bridges = []
  islands = []
  for i in range(grid_width):
    for j in range(grid_height):
      node = grid[i][j]
      if node.n_type == 1:
        islands.append((i, j, node))
      elif node.n_type == 2:
        bridges.append((i, j, node))
      else:
        empty_cells.append((i, j))

  for i, j in empty_cells:
    ax.add_patch(plt.Rectangle((i - ISLAND_RADIUS, j - ISLAND_RADIUS), 2 * ISLAND_RADIUS, 2 * ISLAND_RADIUS, color=EMPTY_CELL_COLOR, zorder=1))

  visited = set()
  for i, j, node in bridges:
    if (i, j) in visited:
      continue
    visited.add((i, j))
    thickness = node.b_thickness if hasattr(node, 'b_thickness') else 1
    if node.b_dir == 0:
      end_i = i
      while end_i + 1 < grid_width and grid[end_i + 1][j].n_type == 2 and grid[end_i + 1][j].b_dir == 0:
        end_i += 1
        visited.add((end_i, j))
      if thickness == 2:
        ax.add_patch(plt.Rectangle((i - 0.5 - ISLAND_RADIUS, j - BRIDGE_WIDTH_DOUBLE_OFFSET / 2), end_i - i + 1 + 2 * ISLAND_RADIUS, BRIDGE_WIDTH_SINGLE, color=BRIDGE_COLOR, zorder=2))
        ax.add_patch(plt.Rectangle((i - 0.5 - ISLAND_RADIUS, j + BRIDGE_WIDTH_DOUBLE_OFFSET / 2 - BRIDGE_WIDTH_SINGLE), end_i - i + 1 + 2 * ISLAND_RADIUS, BRIDGE_WIDTH_SINGLE, color=BRIDGE_COLOR, zorder=2))
      else:
        ax.add_patch(plt.Rectangle((i - 0.5 - ISLAND_RADIUS, j - BRIDGE_WIDTH_SINGLE / 2), end_i - i + 1 + 2 * ISLAND_RADIUS, BRIDGE_WIDTH_SINGLE, color=BRIDGE_COLOR, zorder=2))
    elif node.b_dir == 1:
      end_j = j
      while end_j + 1 < grid_height and grid[i][end_j + 1].n_type == 2 and grid[i][end_j + 1].b_dir == 1:
        end_j += 1
        visited.add((i, end_j))
      if thickness == 2:
        ax.add_patch(plt.Rectangle((i - BRIDGE_WIDTH_DOUBLE_OFFSET / 2, j - 0.5 - ISLAND_RADIUS), BRIDGE_WIDTH_SINGLE, end_j - j + 1 + 2 * ISLAND_RADIUS, color=BRIDGE_COLOR, zorder=2))
        ax.add_patch(plt.Rectangle((i + BRIDGE_WIDTH_DOUBLE_OFFSET / 2 - BRIDGE_WIDTH_SINGLE, j - 0.5 - ISLAND_RADIUS), BRIDGE_WIDTH_SINGLE, end_j - j + 1 + 2 * ISLAND_RADIUS, color=BRIDGE_COLOR, zorder=2))
      else:
        ax.add_patch(plt.Rectangle((i - BRIDGE_WIDTH_SINGLE / 2, j - 0.5 - ISLAND_RADIUS), BRIDGE_WIDTH_SINGLE, end_j - j + 1 + 2 * ISLAND_RADIUS, color=BRIDGE_COLOR, zorder=2))

  for i, j, node in islands:
    ax.add_patch(plt.Circle((i, j), ISLAND_RADIUS, color=(1, 1, 1, 1), zorder=3))
    ax.add_patch(plt.Circle((i, j), ISLAND_RADIUS, color=ISLAND_COLOR, zorder=3, fill=False, linewidth=4))
    ax.text(i, j, str(node.i_count), fontsize=island_font_size, ha='center', va='center', color=ISLAND_TEXT_COLOR, zorder=4)


def draw_grid(grid: list[list[Node]]) -> plt.Figure:
  """
  Draws a grid as its own standalone figure. Use draw_grid_on_axis when
  composing multiple puzzles on one figure (book pages).
  """
  grid_width = len(grid)
  grid_height = len(grid[0])
  fig, ax = plt.subplots(figsize=(grid_width + 2, grid_height + 2))
  draw_grid_on_axis(grid, ax)
  return fig


def save_grid_to_image(fig: plt.Figure, file_path: str):
  """
  Saves the matplotlib figure to an image file.
  """
  fig.savefig(file_path, bbox_inches='tight', dpi=300)  # Save with tight bounding box and high DPI
  plt.close(fig)  # Close the figure to free memory
  print(f"Grid saved to {file_path}")


def show_grid(fig: plt.Figure):
  """
  Displays the matplotlib figure.
  """
  plt.show()  # Show the grid in a window


def clear_grid(fig: plt.Figure):
  """
  Clears the matplotlib figure.
  """
  fig.clf()  # Clear the figure


