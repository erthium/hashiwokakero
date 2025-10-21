import os
import json
import random
import string

from node import Node
from generator import generate_till_full
from export import save_grid
from alternative import draw_grid, save_grid_to_image
from pdf_alternative import create_pdf_with_ids


# Constants
NUM_PUZZLES = 10  # Set your desired number
PUZZLE_WIDTH = 10   # Example size, adjust as needed
PUZZLE_HEIGHT = 10

font_size_config = {
  (10, 10): 16,
  (10, 15): 20,
  (15, 10): 20,
  (15, 15): 20,
  (20, 20): 24,
}
DEFAULT_FONT_SIZE = 18  # Default font size if not found in config

# Font size from dimension
def dimension_to_font_size(width: int, height: int) -> int:
  """
  Returns font size based on puzzle dimensions.
  """
  return font_size_config.get((width, height), DEFAULT_FONT_SIZE)


# Generate unique 2-letter + 2-digit IDs
def generate_unique_id(existing_ids):
  while True:
    letters = ''.join(random.choices(string.ascii_lowercase, k=2))
    digits = ''.join(random.choices(string.digits, k=2))
    puzzle_id = f"{letters}{digits}"
    if puzzle_id not in existing_ids:
      return puzzle_id


# Remove bridges from the grid
def remove_bridges(grid: list[list[Node]]):
  for row in grid:
    for node in row:
      if node.n_type == 2:
        node.make_empty()
      if node.n_type == 1:
        node.current_in = 0  # Reset current input for islands


def main():
  import argparse
  global NUM_PUZZLES, PUZZLE_WIDTH, PUZZLE_HEIGHT
  parser = argparse.ArgumentParser(description="Generate a dataset of Hashiwokakero puzzles.")
  parser.add_argument('--dataset_dir', type=str, help="Directory to save the dataset")
  parser.add_argument('--num_puzzles', type=int, default=NUM_PUZZLES, help="Number of puzzles to generate")
  parser.add_argument('--width', type=int, default=PUZZLE_WIDTH, help="Width of each puzzle grid")
  parser.add_argument('--height', type=int, default=PUZZLE_HEIGHT, help="Height of each puzzle grid")
  args = parser.parse_args()

  NUM_PUZZLES = args.num_puzzles
  PUZZLE_WIDTH = args.width
  PUZZLE_HEIGHT = args.height

  FONTSIZE = dimension_to_font_size(PUZZLE_WIDTH, PUZZLE_HEIGHT)

  # Create dataset directory if it doesn't exist
  if not args.dataset_dir:
    raise ValueError("Please specify a dataset directory using --dataset_dir")
  DATASET_DIR = args.dataset_dir
  os.makedirs(DATASET_DIR, exist_ok=True)

  # Create subdirectories for csvs and pngs
  CSV_DIR = os.path.join(DATASET_DIR, 'puzzles_csv')
  PNG_DIR = os.path.join(DATASET_DIR, 'puzzles_png')
  os.makedirs(CSV_DIR, exist_ok=True)
  os.makedirs(PNG_DIR, exist_ok=True)

  puzzle_ids = []
  puzzle_info = []  # (image_path, id) tuples for PDF
  existing_ids = set()
  for i in range(NUM_PUZZLES):
    # Generate puzzle
    grid = generate_till_full(PUZZLE_WIDTH, PUZZLE_HEIGHT)

    # Unique ID
    puzzle_id = generate_unique_id(existing_ids)
    existing_ids.add(puzzle_id)
    puzzle_ids.append(puzzle_id)

    # Save CSV
    csv_path = os.path.join(CSV_DIR, f"{puzzle_id}.csv")
    save_grid(grid, csv_path)

    # Remove bridges for the empty grid
    remove_bridges(grid)

    # Save image with ID on top
    image_path = os.path.join(PNG_DIR, f"{puzzle_id}.png")
    fig = draw_grid(grid)
    ## Add ID text to the figure
    fig.suptitle(f"Puzzle ID: {puzzle_id}", fontsize=FONTSIZE, fontweight='bold', y=0.95)
    save_grid_to_image(fig, image_path)
    puzzle_info.append((image_path, puzzle_id))
    print(f"Saved puzzle {puzzle_id} -- {i}")

  # Save IDs to JSON
  ids_json_path = os.path.join(DATASET_DIR, "puzzle_ids.json")
  with open(ids_json_path, 'w') as f:
    json.dump(puzzle_ids, f, indent=2)
  print(f"Saved all puzzle IDs to {ids_json_path}")

  # Create PDF with IDs
  pdf_path = os.path.join(DATASET_DIR, "puzzles.pdf")
  create_pdf_with_ids(pdf_path, puzzle_info, PUZZLE_WIDTH, PUZZLE_HEIGHT)
  print(f"Created PDF at {pdf_path}")

if __name__ == "__main__":
  main()
