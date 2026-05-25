# Phase 3 — Repository restructure

The functionality is solid; the layout is not. Everything lives in a flat `hashi/` directory next to runtime outputs, output paths are hard-coded relative to `__file__`, every script has its own per-module argparse, and the same concept appears under multiple names (`production.py` vs `dataset_production.py`, `visualiser.py` vs `alternative.py`). Phase 3 reshapes the project into a discoverable, importable Python package with a single CLI surface — without changing any behaviour.

## Principles

1. **One canonical path per concept.** Each piece of functionality lives in exactly one file with a clear name. Old duplicates are removed or merged.
2. **Library code is separate from outputs.** Generated puzzles, PDFs, and images do not sit inside the package directory.
3. **A single CLI entry point.** All user-facing operations are subcommands of one `hashi` command. Per-module `__main__` blocks go away; their argparse logic moves into the CLI layer.
4. **Subpackages by functional area.** Code is grouped by what it does (solve, generate, render, categorise, produce), not by file type.
5. **Optional dependencies stay optional.** pygame in particular should not be required for the solver or categoriser to run.
6. **Spelling cleanup.** `cathegorise` (typo) becomes `categorize` everywhere — module, function, factor constants, doc references.

## Target tree

```
hashiwokakero/
├── pyproject.toml              # packaging + entry point + deps
├── README.md
├── LICENSE
├── Makefile                    # thin wrapper around `hashi <subcommand>`
├── hashi/                      # the importable package
│   ├── __init__.py
│   ├── __main__.py             # python -m hashi → cli.main()
│   ├── cli.py                  # argparse subcommands, dispatches to library calls
│   ├── core.py                 # Node, direction helpers, grid utilities
│   ├── solver.py               # solve(), Solution
│   ├── generator.py            # generate_till_full
│   ├── formats.py              # CSV save/load  (was export.py)
│   ├── render.py               # matplotlib renderer  (was alternative.py)
│   ├── production.py           # bucketed mass production (was production.py)
│   ├── categorize/
│   │   ├── __init__.py         # re-exports: get_difficulty_value, etc.
│   │   ├── categorize.py       # categoriser logic  (was cathegorise.py)
│   │   └── mapper.py           # calibration runner  (was difficulty_mapper.py)
│   └── data/                   # packaged data, shipped with the install
│       ├── difficulty_map.json
│       └── fonts/
│           └── SpaceMono-Regular.ttf
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # fixture path helper
│   ├── test_solver.py          # was hashi_test.py
│   └── fixtures/
│       ├── basic/              # was basic_puzzles/
│       ├── difficult/          # was difficult_puzzles/
│       └── testdata/           # was hashi/testdata/
├── docs/
│   ├── phase1_solver.md
│   ├── phase2_cathegoriser.md
│   ├── phase3_restructure.md   # this document
│   └── backlog.md
└── output/                     # gitignored runtime artifacts
    ├── puzzles/
    ├── images/
    ├── pdfs/
    └── database/               # easy/intermediate/hard subdirs go here
```

### Files being deleted outright

- `hashi/visualiser.py` — pygame viewer (deprecated header already says so).
- `hashi/ui_elements.py` — pygame button widgets.
- `hashi/dataset_production.py` — ID-based dataset flow we're not keeping.
- `hashi/dataset_labeler.py` — empty placeholder.
- `hashi/pdf_alternative.py` — only used by `dataset_production.py`.
- `hashi/pdf_out.py` — pygame-era PDF output, superseded.
- `hashi/arg_parser.py` — folded into `cli.py`.
- `database/difficulty_map.json` — stale legacy format.

## Subpackage roles

- **`hashi.core`** — the domain primitives. `Node`, `direction_to_vector`, `nodes_to_direction`, `is_in_grid`. Pure logic, no I/O, no rendering dependencies. Imported by everything else.
- **`hashi.solver`** — the solver and the `Solution` dataclass. No CLI, no I/O. Accepts a grid, returns solutions. The optional `progress_callback` from Phase 1 stays.
- **`hashi.generator`** — `generate_till_full(w, h)` and its helpers. The matplotlib/pygame imports in `main()` come out; rendering is somebody else's job.
- **`hashi.formats`** — CSV serialisation (`save_grid`, `import_empty_grid`, `import_solution_grid`). The pygame-dependent `output_image` moves to `render.image`.
- **`hashi.categorize`** — `get_difficulty_value`, `inspect_puzzle`, `compute_metrics`, the factor weight constants. `mapper.py` keeps the calibration runner with its multiprocessing pool, progress display, and budget. The categoriser reads `difficulty_map.json` from `hashi/data/` via `importlib.resources.files()` instead of `__file__`-relative paths.
- **`hashi.render`** — three rendering backends:
  - `image.py` — matplotlib static PNG output (the active renderer).
  - `pdf.py` — multi-puzzle PDF books.
  - `interactive.py` — the pygame viewer. Imports pygame inside the module; the rest of the package never triggers it.
- **`hashi.production`** — batch puzzle generation. `dataset.py` produces ID-based CSV+PNG batches with manifest JSON. `book.py` produces categorised PDFs (the old `production.py` flow). Both use the solver + categoriser + render machinery.
- **`hashi.cli`** — one `main()` function with argparse subparsers. Each subcommand does its argument parsing and calls library functions. The per-module `arg_parser.py` helpers are deleted; their logic either moves into `cli.py` or is replaced by direct argparse there.

## CLI surface

One command, subcommands for each user-facing operation. Names are short verbs.

```
hashi generate WIDTH HEIGHT [-o OUTPUT.csv]
hashi solve PATH.csv [--all] [--show]
hashi score PATH.csv
hashi render PATH.csv [--format image|pdf|interactive] [-o OUTPUT]
hashi calibrate [--samples N] [--max-brutal N] [--workers N]
hashi produce WIDTH HEIGHT COUNT [-d OUTPUT_DIR] [--categorize]
hashi book INPUT_DIR [-o OUTPUT.pdf]
```

Notes:
- `solve --all` toggles `stop_at_first=False`.
- `solve --show` invokes the matplotlib renderer on the result (convenience).
- `score` prints the normalised difficulty value to stdout (and optionally the metric breakdown).
- `calibrate` is `make map` today. Environment-variable overrides (`HASHI_MAP_WORKERS`, `HASHI_MAP_MAX_BRUTAL`) become CLI flags; env vars still work as fallbacks.
- `produce` always runs the categoriser; the `--categorize` flag is wrong by default — produce always emits scored output. If we want unscored fast generation, that's a separate `--no-score` flag.
- `book` is downstream of `produce` — it takes a directory of solved puzzles and assembles a PDF.

The `Makefile` becomes a friendly shorthand:

```
make produce   →  hashi produce $(W) $(H) $(P) -d $(DATABASE_DIR)
make map       →  hashi calibrate
make test      →  python -m pytest tests/
```

## Decisions to settle

### D1: Flat package vs `src/` layout

Recommendation: **flat package** (`hashi/` at repo root, as shown above).

`src/` layout is more pedantically "correct" but adds friction for a single-developer project. The flat layout is what the project already uses; we keep the muscle memory. If we ever publish to PyPI we can switch then.

### D2: CLI framework

Recommendation: **stdlib argparse**, with subparsers.

Pros: no new dependencies, the project already uses argparse, plenty good for ~7 subcommands. If the CLI grows hairy we can swap in [`typer`](https://typer.tiangolo.com/) later without breaking the package API.

### D3: Spelling — `categorize` vs `categorise`

Recommendation: **`categorize`** (American).

Code convention in the Python ecosystem leans American (`color`, `optimize`, etc.). One canonical spelling everywhere. The current `cathegorise` is a typo and has to be corrected anyway; might as well land on the most common form. The doc filename `phase2_cathegoriser.md` should be renamed too — or left as a historical artifact and a new `phase2_categorize.md` symlink/copy added.

### D4: pygame — keep, isolate, or delete

Recommendation: **isolate**.

The matplotlib renderer (`alternative.py`) is the active one; the pygame viewer in `visualiser.py` already carries a deprecated header. Move pygame code to `render/interactive.py`, make pygame an *optional* dependency in `pyproject.toml`, and have `hashi render --format interactive` raise a helpful error if pygame is not installed. Nobody who only wants to solve or score puzzles should be forced to install pygame.

### D5: `production.py` vs `dataset_production.py`

These serve different purposes:
- `production.py` — old categorised bucketing (easy / intermediate / hard) directly to `database/`.
- `dataset_production.py` — newer ID-based dataset with CSV + PNG + PDF + manifest JSON.

Recommendation: **keep both, rename for clarity**. `production/book.py` (book-style PDF output) and `production/dataset.py` (ML/data pipeline output). They share helpers (generation, solving, categorisation) but have distinct end goals.

### D6: Output directory layout

Recommendation: **single `output/` at repo root**, gitignored, with subdirs per artifact type.

The current setup has runtime outputs scattered: `hashi/puzzles/`, `hashi/images/`, `hashi/pdfs/`, `database/`. Moving everything under `output/` (and gitignoring it) makes the package directory pure code, and the repo state much clearer.

There's also a stray `database/difficulty_map.json` (old flat-tuple format, predates the recent rewrite) that should be deleted as part of the move.

### D7: `pyproject.toml` vs `requirements.txt`

Recommendation: **`pyproject.toml`**.

It defines the package, the CLI entry point (`hashi = "hashi.cli:main"`), and the dependencies in one place. `requirements.txt` becomes unnecessary or stays as a convenience generated from `pip-compile`.

Skeleton:

```toml
[project]
name = "hashi"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "matplotlib",
    "reportlab",   # or pypdf/whatever pdf_alternative uses
]

[project.optional-dependencies]
interactive = ["pygame"]

[project.scripts]
hashi = "hashi.cli:main"
```

## Migration steps

Order matters — keep the test suite green at every step.

### 3.1 Move package data into the package

- Create `hashi/data/` (already exists in the wrong place — same name, but it's mixed with output).
- Move `difficulty_map.json` from `hashi/` into `hashi/data/`.
- Update `categorize.py` to use `importlib.resources.files("hashi.data") / "difficulty_map.json"` instead of `__file__`-relative paths.
- Move `hashi/data/SpaceMono-Regular.ttf` already lives in the right place; leave it.

### 3.2 Move outputs out

- Create `output/` at the repo root with subdirs `puzzles/`, `images/`, `pdfs/`, `database/`.
- Move existing artifacts from `hashi/puzzles/`, `hashi/images/`, `hashi/pdfs/`, `database/` into the new locations.
- Update any code that hard-codes `puzzles/` or `database/easy/` etc. to use the new paths via a config constant (e.g. `OUTPUT_DIR` in `hashi/__init__.py`).
- Add `output/` to `.gitignore`.
- Delete the stale `database/difficulty_map.json` outright.

### 3.3 Subpackage split: categorize

- Create `hashi/categorize/__init__.py`.
- Move `cathegorise.py` → `categorize/categorize.py`, rename functions where they carry the typo (`get_diffiulty_map` → `get_difficulty_map`, `save_diffiulty_map` → `save_difficulty_map`).
- Move `difficulty_mapper.py` → `categorize/mapper.py`.
- Update all imports in solver / generator / tests.
- Re-export the public names from `categorize/__init__.py` so `from hashi.categorize import get_difficulty_value` still works.

### 3.4 Subpackage split: render

- Create `hashi/render/__init__.py`.
- `alternative.py` → `render/image.py`. Internal function names (`draw_grid`, `save_grid_to_image`) stay.
- `pdf_alternative.py` → `render/pdf.py`.
- `visualiser.py` + `ui_elements.py` → `render/interactive.py` (concatenate, drop the deprecated old block, leave a single coherent file).
- Move the pygame import inside `interactive.py`; remove any pygame imports from other modules.

### 3.5 Subpackage split: production

- Create `hashi/production/__init__.py`.
- `dataset_production.py` → `production/dataset.py`.
- `production.py` → `production/book.py`.
- Delete `dataset_labeler.py` (empty file — placeholder that was never filled in).
- Delete `pdf_out.py` if it's superseded by `render/pdf.py` (confirm by inspection).

### 3.6 Rename one-off modules

- `export.py` → `formats.py`.
- `node.py` → `core.py`. (Decide whether to inline `arg_parser` here too — it's tiny and tied to the file format.)
- `arg_parser.py` → fold into `cli.py` and delete.

### 3.7 Build the CLI

- Create `hashi/cli.py` with an argparse `main()` and one subparser per command listed above.
- Each subcommand handler is ~10 lines: parse args, call library, print result.
- Remove every `if __name__ == "__main__":` block from individual modules (move their logic into the corresponding CLI subcommand).
- Create `hashi/__main__.py`:
  ```python
  from hashi.cli import main
  main()
  ```

### 3.8 Add `pyproject.toml`

- Create the file with the skeleton above.
- Run `pip install -e .` locally to verify the `hashi` script is installed and works.
- Move dependencies out of `requirements.txt` and into `pyproject.toml`.

### 3.9 Update tests

- Move `tests/hashi_test.py` → `tests/test_solver.py`.
- Move `tests/basic_puzzles/` → `tests/fixtures/basic/`, same for `difficult_puzzles/`.
- Update the `sys.path` hack at the top of the test file with a clean `from hashi.solver import solve` once the package is installable.
- Add `tests/conftest.py` with a `FIXTURES_DIR` constant so individual tests don't have to compute paths.

### 3.10 Update `Makefile`

- Replace direct `python3 hashi/foo.py` calls with `hashi <subcommand>` invocations.
- Keep the `make` targets the user already uses (`test`, `map`, `produce`) but route them through the CLI.

### 3.11 Update docs

- README: brief description, install instructions (`pip install -e .`), CLI overview.
- Keep `docs/phase1_solver.md` and `docs/phase2_cathegoriser.md` as historical phase records — references to `cathegorise.py` inside them are fine since they describe past state.
- `docs/backlog.md` already exists; nothing to do unless we close out items.

## Deliverables

When Phase 3 is done:

- `pip install -e .` produces a `hashi` command on PATH.
- `hashi --help` lists every subcommand with a one-line description.
- `make test` still passes.
- No module under `hashi/` carries an `if __name__ == "__main__"` block.
- No pygame import outside `hashi/render/interactive.py`.
- `hashi/` contains only code and packaged data; no runtime outputs.
- `cathegorise` is gone — replaced by `categorize` everywhere.

The next phase (mass production with categoriser, originally outlined as Phase 3 in the earlier plan) now becomes Phase 4 — and it's mostly mechanical because the rebuilt CLI already exposes `produce` as a first-class subcommand.
