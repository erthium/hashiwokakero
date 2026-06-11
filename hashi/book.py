"""
Assemble a printable PDF book from a directory of bucketed puzzles.

V1 scope (Phase 4, B.D1):

- Only two geometries supported: 10x10 and 10x20.
- 10x20 puzzles get one page each, full page, vertically oriented.
- 10x10 puzzles get two per page, stacked vertically (top + bottom).
- Cell size is uniform across the entire book — chosen to fit a 10x20 layout
  on the page (which is the same as two stacked 10x10s).
- Solutions are at the end of the same PDF, in the same order, with IDs for
  cross-reference.
- IDs are assigned at book-assembly time: E001, E002, … for easy puzzles,
  I001, I002, … for intermediate, H001, H002, … for hard. Section by section.

Generalising beyond this is tracked in docs/backlog.md → "General PDF book layout".
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from hashi.core import Node
from hashi.formats import import_empty_grid, import_solution_grid
from hashi.render import draw_grid_on_axis


# A4 portrait in inches; matplotlib's native unit.
PAGE_WIDTH_IN = 8.27
PAGE_HEIGHT_IN = 11.69

# Reserve space for a small header above each grid.
HEADER_BAND_IN = 0.5
# Gap between two stacked 10x10 puzzles on the same page.
INNER_GAP_IN = 0.3
# Side margins.
SIDE_MARGIN_IN = 1.0

# Bucket → directory name on disk and ID prefix in the book.
BUCKET_DIRS = ("easy", "intermediate", "hard")
BUCKET_PREFIXES = {"easy": "E", "intermediate": "I", "hard": "H"}

# Bucket ordering for the produced book.
BUCKET_ORDER = ("easy", "intermediate", "hard")


@dataclass
class _Puzzle:
    """A puzzle ready to be placed on a page."""
    book_id: str            # E001, I042, H013, …
    bucket: str             # easy / intermediate / hard
    score: float            # parsed from the filename
    geometry: tuple[int, int]  # (width, height)
    empty_grid: list[list[Node]]
    solution_grid: list[list[Node]]


def _parse_score_from_filename(filename: str) -> float:
    """Filename pattern from production.py: puzzle_<score>.csv or puzzle_<score>_<n>.csv."""
    stem = os.path.splitext(filename)[0]
    parts = stem.split("_")
    # Score is the first numeric component after "puzzle".
    for part in parts[1:]:
        try:
            return float(part)
        except ValueError:
            continue
    return 0.0


def _collect_puzzles(input_dir: str) -> list[_Puzzle]:
    """
    Walks input_dir/{easy,intermediate,hard}/*.csv, parses each puzzle, sorts
    by bucket then by score ascending, assigns book IDs in that order, and
    returns the ready-to-render list.

    Skips any puzzle whose geometry is not in the v1 supported set.
    """
    collected: dict[str, list[_Puzzle]] = {b: [] for b in BUCKET_ORDER}
    for bucket in BUCKET_DIRS:
        bucket_dir = os.path.join(input_dir, bucket)
        if not os.path.isdir(bucket_dir):
            continue
        for filename in sorted(os.listdir(bucket_dir)):
            if not filename.endswith(".csv"):
                continue
            path = os.path.join(bucket_dir, filename)
            empty_grid = import_empty_grid(path)
            solution_grid = import_solution_grid(path)
            if empty_grid is None or solution_grid is None:
                continue
            w, h = len(empty_grid), len(empty_grid[0])
            if (w, h) not in {(10, 10), (10, 20)}:
                print(
                    f"  skipping {bucket}/{filename}: geometry {w}x{h} is not supported in v1"
                )
                continue
            score = _parse_score_from_filename(filename)
            collected[bucket].append(
                _Puzzle(
                    book_id="",  # assigned below
                    bucket=bucket,
                    score=score,
                    geometry=(w, h),
                    empty_grid=empty_grid,
                    solution_grid=solution_grid,
                )
            )

    # Sort each bucket by score ascending, then assign sequential IDs.
    ordered: list[_Puzzle] = []
    for bucket in BUCKET_ORDER:
        bucket_puzzles = sorted(collected[bucket], key=lambda p: p.score)
        prefix = BUCKET_PREFIXES[bucket]
        for i, puzzle in enumerate(bucket_puzzles, start=1):
            puzzle.book_id = f"{prefix}{i:03d}"
            ordered.append(puzzle)
    return ordered


def _pack_pages(puzzles: list[_Puzzle]) -> list[list[_Puzzle]]:
    """
    Groups puzzles into page-sized chunks per the v1 layout rules:
      - 10x20 → its own page (one-element list).
      - 10x10 → two per page; the final one pairs alone if odd count.
    Pages are emitted in input order, which is bucket then score.
    """
    pages: list[list[_Puzzle]] = []
    i = 0
    while i < len(puzzles):
        p = puzzles[i]
        if p.geometry == (10, 20):
            pages.append([p])
            i += 1
        elif p.geometry == (10, 10):
            page = [p]
            if i + 1 < len(puzzles) and puzzles[i + 1].geometry == (10, 10):
                page.append(puzzles[i + 1])
                i += 2
            else:
                i += 1
            pages.append(page)
        else:  # Defensive — _collect_puzzles already filters this.
            i += 1
    return pages


def _puzzle_axes_for_full_page(fig: plt.Figure) -> plt.Axes:
    """
    Adds one axis sized for a single 10x20 puzzle filling the page (below the
    header band). Returns the axis.
    """
    usable_w = PAGE_WIDTH_IN - 2 * SIDE_MARGIN_IN
    usable_h = PAGE_HEIGHT_IN - HEADER_BAND_IN - SIDE_MARGIN_IN
    cell = min(usable_w / 10, usable_h / 20)
    grid_w = 10 * cell
    grid_h = 20 * cell
    left = (PAGE_WIDTH_IN - grid_w) / 2
    bottom = SIDE_MARGIN_IN  # leave HEADER_BAND_IN on top
    return fig.add_axes(
        [
            left / PAGE_WIDTH_IN,
            bottom / PAGE_HEIGHT_IN,
            grid_w / PAGE_WIDTH_IN,
            grid_h / PAGE_HEIGHT_IN,
        ]
    )


def _puzzle_axes_for_two_stacked(fig: plt.Figure) -> tuple[plt.Axes, plt.Axes]:
    """
    Adds two axes for two stacked 10x10 puzzles. Cell size is the same as the
    full-page 10x20 layout so islands remain uniform across the book.
    """
    usable_w = PAGE_WIDTH_IN - 2 * SIDE_MARGIN_IN
    usable_h = PAGE_HEIGHT_IN - HEADER_BAND_IN - SIDE_MARGIN_IN - INNER_GAP_IN
    cell = min(usable_w / 10, usable_h / 20)
    grid_side = 10 * cell

    left = (PAGE_WIDTH_IN - grid_side) / 2
    # Top puzzle's bottom edge sits above the gap; bottom puzzle's bottom edge
    # is at SIDE_MARGIN_IN from the page bottom.
    bottom_lower = SIDE_MARGIN_IN
    bottom_upper = bottom_lower + grid_side + INNER_GAP_IN

    ax_upper = fig.add_axes(
        [
            left / PAGE_WIDTH_IN,
            bottom_upper / PAGE_HEIGHT_IN,
            grid_side / PAGE_WIDTH_IN,
            grid_side / PAGE_HEIGHT_IN,
        ]
    )
    ax_lower = fig.add_axes(
        [
            left / PAGE_WIDTH_IN,
            bottom_lower / PAGE_HEIGHT_IN,
            grid_side / PAGE_WIDTH_IN,
            grid_side / PAGE_HEIGHT_IN,
        ]
    )
    return ax_upper, ax_lower


def _render_page(page_puzzles: list[_Puzzle], *, solution: bool) -> plt.Figure:
    """
    Renders one page (either a puzzle page or a solution page). The grid drawn
    is empty_grid for puzzle pages and solution_grid for solution pages.
    """
    fig = plt.figure(figsize=(PAGE_WIDTH_IN, PAGE_HEIGHT_IN))

    if len(page_puzzles) == 1 and page_puzzles[0].geometry == (10, 20):
        p = page_puzzles[0]
        ax = _puzzle_axes_for_full_page(fig)
        grid = p.solution_grid if solution else p.empty_grid
        draw_grid_on_axis(grid, ax)
        header = f"{p.book_id}  ·  {p.geometry[0]}×{p.geometry[1]}"
        if solution:
            header += f"  ·  {p.bucket}  ·  score {p.score:.3f}"
        fig.text(0.5, 1 - HEADER_BAND_IN / (2 * PAGE_HEIGHT_IN), header,
                 ha="center", va="center", fontsize=14)

    else:
        # Two stacked 10x10s (or a single 10x10 alone on its page).
        ax_upper, ax_lower = _puzzle_axes_for_two_stacked(fig)
        for ax, puzzle in zip((ax_upper, ax_lower), page_puzzles):
            grid = puzzle.solution_grid if solution else puzzle.empty_grid
            draw_grid_on_axis(grid, ax)
            # Header above each subgrid.
            bbox = ax.get_position()
            text_y = bbox.y1 + 0.01
            label = f"{puzzle.book_id}  ·  {puzzle.geometry[0]}×{puzzle.geometry[1]}"
            if solution:
                label += f"  ·  {puzzle.bucket}  ·  score {puzzle.score:.3f}"
            fig.text(0.5, text_y, label, ha="center", va="bottom", fontsize=12)

    return fig


def _render_section_divider(title: str) -> plt.Figure:
    """A simple section divider page used between puzzles and solutions."""
    fig = plt.figure(figsize=(PAGE_WIDTH_IN, PAGE_HEIGHT_IN))
    fig.text(0.5, 0.5, title, ha="center", va="center", fontsize=36)
    return fig


def assemble_book(input_dir: str, output_path: str) -> None:
    """
    Builds the PDF: puzzle pages in bucket-then-score order, a "Solutions"
    divider, then the same puzzles' solution pages in the same order.
    """
    puzzles = _collect_puzzles(input_dir)
    if not puzzles:
        raise ValueError(
            f"No supported puzzles found in {input_dir}. "
            "V1 accepts only 10x10 and 10x20 under easy/intermediate/hard subdirs."
        )

    pages = _pack_pages(puzzles)
    counts = {b: sum(1 for p in puzzles if p.bucket == b) for b in BUCKET_ORDER}
    print(
        f"Assembling book: {sum(counts.values())} puzzles "
        f"(easy={counts['easy']} intermediate={counts['intermediate']} hard={counts['hard']}) "
        f"across {len(pages)} puzzle pages."
    )

    with PdfPages(output_path) as pdf:
        for i, page in enumerate(pages, start=1):
            fig = _render_page(page, solution=False)
            pdf.savefig(fig)
            plt.close(fig)
        # Solutions section.
        fig = _render_section_divider("Solutions")
        pdf.savefig(fig)
        plt.close(fig)
        for page in pages:
            fig = _render_page(page, solution=True)
            pdf.savefig(fig)
            plt.close(fig)

    print(f"Wrote book to {output_path}")
