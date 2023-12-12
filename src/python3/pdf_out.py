from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A5, A6
from PIL import Image

page_size = A5
page_ratio = page_size[0] / page_size[1]

def draw_puzzle(canvas, puzzle_filename, x, y, width, height):
    # Open the puzzle image using Pillow
    image = Image.open(puzzle_filename)

    # Resize the image to fit the puzzle space while preserving the aspect ratio
    image.thumbnail((width, height))

    # Calculate the position to center the image within the puzzle space
    x_offset = (width - image.width) / 2
    y_offset = (height - image.height) / 2

    # Draw the image on the PDF canvas
    canvas.drawInlineImage(image, x + x_offset, y + y_offset, image.width, image.height)


def create_pdf(output_filename, puzzle_filenames, rows=2):
    pdf = canvas.Canvas(output_filename, pagesize=page_size)
    cols = len(puzzle_filenames) // rows
    puzzle_offset = (20, 100)
    puzzle_width = (page_size[0] - ((cols + 1) * puzzle_offset[0])) / cols
    puzzle_height = (page_size[1] - ((rows + 1) * puzzle_offset[1])) / rows

    for i, puzzle_filename in enumerate(puzzle_filenames):
        row = i // cols
        col = i % cols

        x = col * puzzle_width + (col + 1) * puzzle_offset[0]
        y = page_size[1] - (row + 1) * puzzle_height - (row + 1) * puzzle_offset[1]

        # Draw puzzle image on the PDF
        draw_puzzle(pdf, puzzle_filename, x, y, puzzle_width, puzzle_height)

        if i % (rows * cols) == (rows * cols) - 1:
            pdf.showPage()  # Start a new page

    pdf.save()

puzzle_filenames = ["images/test.png"]
create_pdf("output.pdf", puzzle_filenames, rows=1)
