from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from PIL import Image

def dimension_to_config(width: int, height: int):
  """
  Returns configuration for PDF layout based on puzzle dimensions.
  Returns dict with keys: 'cols', 'rows', 'padding_x', 'padding_y'
  """
  # Placeholder values - experiment and fill actual values later
  configs = {
    (10, 10): {'cols': 2, 'rows': 2, 'padding_x': 0, 'padding_y': 0},
    (10, 15): {'cols': 2, 'rows': 2, 'padding_x': 0, 'padding_y': 20},
    (15, 10): {'cols': 1, 'rows': 3, 'padding_x': 0, 'padding_y': 12},
    (15, 15): {'cols': 2, 'rows': 2, 'padding_x': 12, 'padding_y': 0},
    (20, 20): {'cols': 2, 'rows': 2, 'padding_x': 6, 'padding_y': 0},
  }

  # Default configuration if dimension not found
  default_config = {'cols': 1, 'rows': 2, 'padding_x': 0, 'padding_y': 0}
  
  return configs.get((width, height), default_config)


def create_pdf_with_ids(output_filename: str, puzzle_info: list[tuple[str, str]], width: int, height: int):
  """
  puzzle_info: list of (filename, id) tuples
  Uses grid layout with equal-sized cells and separate x/y padding.
  Embeds PNGs at high quality.
  """
  page_size = A5
  pdf = canvas.Canvas(output_filename, pagesize=page_size)
  
  # Get configuration based on puzzle dimensions
  config = dimension_to_config(width, height)
  cols = config['cols']
  rows = config['rows']
  padding_x = config['padding_x']
  padding_y = config['padding_y']
  
  puzzles_per_page = cols * rows
  cell_width = page_size[0] / cols
  cell_height = page_size[1] / rows
  
  for i in range(0, len(puzzle_info), puzzles_per_page):
    for j in range(puzzles_per_page):
      idx = i + j
      if idx >= len(puzzle_info):
        break
      puzzle_filename, puzzle_id = puzzle_info[idx]
      row = j // cols
      col = j % cols
      x = col * cell_width
      y = page_size[1] - (row + 1) * cell_height
      # Open image and get its size in pixels
      image = Image.open(puzzle_filename)
      img_width_px, img_height_px = image.size
      # Calculate the size in points for the image at 300 DPI
      dpi = 300
      img_width_pt = img_width_px * 72 / dpi
      img_height_pt = img_height_px * 72 / dpi
      # Center the image in the cell with separate x/y padding
      available_width = cell_width - 2 * padding_x
      available_height = cell_height - 2 * padding_y
      scale = min(available_width / img_width_pt, available_height / img_height_pt)
      draw_width = img_width_pt * scale
      draw_height = img_height_pt * scale
      x_offset = (cell_width - draw_width) / 2
      y_offset = (cell_height - draw_height) / 2
      #pdf.setFont("Helvetica-Bold", 18)
      #pdf.drawCentredString(x + cell_width / 2, y + cell_height + 20, puzzle_id)
      pdf.drawImage(
        puzzle_filename,
        x + x_offset,
        y + y_offset,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask='auto'
      )
    pdf.showPage()
  pdf.save()
