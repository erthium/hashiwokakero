"""
This module computes a normalised difficulty score for a hashiwokakero puzzle.

The score is a float in [0, 1] derived from five factors:

1. Island weight: average island count across all islands on the grid.
2. Island amount weight: island density (islands / total cells).
3. Below seven weight: count of islands with i_count < 7.
4. By rule steps: deterministic rule-pass steps reported by the solver.
5. Brutal steps: brute-force moves the solver had to make.

Each factor is normalised against a per-geometry range stored in difficulty_map.json
(5th/95th percentile bounds gathered by difficulty_mapper.py), clamped to [0, 1],
then multiplied by the factor weight. The five weighted components sum to the final
difficulty score.

Mapping a normalised score to discrete difficulty labels (easy / intermediate / hard)
is intentionally not handled here — see docs/backlog.md.
"""


from dataclasses import dataclass
from importlib.resources import files
import json

from hashi.core import Node


# Packaged calibration data lives under hashi/data/. Resolved at import time so
# every consumer sees the same path regardless of cwd.
MAP_PATH = str(files("hashi.data") / "difficulty_map.json")


# Factor weights. Must sum to 1.0.
# Solver-derived (brutal + rule) totals 0.65; structural totals 0.35.
# Tuned in Phase 2 after the spot-check showed structural dominating the score
# (a rule-solvable puzzle with crowded small islands was outscoring puzzles
# that actually required brute moves).
BRUTAL_STEP_FACTOR: float    = 0.55
BY_RULE_STEP_FACTOR: float   = 0.10
ISLAND_WEIGHT_FACTOR: float  = 0.15
ISLAND_AMOUNT_FACTOR: float  = 0.15
BELOW_SEVEN_FACTOR: float    = 0.05

_FACTOR_SUM = (
    BRUTAL_STEP_FACTOR
    + ISLAND_WEIGHT_FACTOR
    + ISLAND_AMOUNT_FACTOR
    + BELOW_SEVEN_FACTOR
    + BY_RULE_STEP_FACTOR
)
assert abs(_FACTOR_SUM - 1.0) < 1e-6, f"Difficulty factor weights must sum to 1.0, got {_FACTOR_SUM}"


# Metric keys stored per geometry in difficulty_map.json.
METRIC_KEYS = (
    "island_weight",
    "island_amount_weight",
    "below_seven_weight",
    "by_rule_steps",
    "brutal_steps",
)


@dataclass
class PuzzleInformation:
    grid_width: int
    grid_height: int
    island_amount: int
    total_island_count: int
    total_seven_count: int
    total_eight_count: int
    by_rule_steps: int
    brutal_steps: int


def get_difficulty_map() -> dict:
    """
    Loads the difficulty map from disk.

    Schema: dict keyed by "WxH", each value is a dict of metric -> [lo, hi].
    """
    with open(MAP_PATH, "r") as file:
        return json.load(file)


def save_difficulty_map(difficulty_map: dict) -> None:
    """
    Persists the difficulty map. Overwrites the entire file.
    """
    with open(MAP_PATH, "w") as file:
        json.dump(difficulty_map, file, indent=2)


def inspect_puzzle(grid: list[list[Node]], by_rule_steps: int, brutal_steps: int) -> PuzzleInformation:
    """
    Scans a grid and returns a PuzzleInformation snapshot.
    """
    grid_width: int = len(grid)
    grid_height: int = len(grid[0])
    island_amount: int = 0
    total_island_count: int = 0
    total_seven_count: int = 0
    total_eight_count: int = 0
    for x in range(grid_width):
        for y in range(grid_height):
            if grid[x][y].n_type == 1:
                island_amount += 1
                total_island_count += grid[x][y].i_count
                if grid[x][y].i_count == 7:
                    total_seven_count += 1
                if grid[x][y].i_count == 8:
                    total_eight_count += 1
    return PuzzleInformation(
        grid_width=grid_width,
        grid_height=grid_height,
        island_amount=island_amount,
        total_island_count=total_island_count,
        total_seven_count=total_seven_count,
        total_eight_count=total_eight_count,
        by_rule_steps=by_rule_steps,
        brutal_steps=brutal_steps,
    )


def compute_metrics(info: PuzzleInformation) -> dict[str, float]:
    """
    Extracts the five raw metric values from a PuzzleInformation.

    Shared with difficulty_mapper so the categoriser and the mapper compute
    metrics identically.
    """
    island_weight = info.total_island_count / info.island_amount
    island_amount_weight = info.island_amount / (info.grid_width * info.grid_height)
    below_seven_weight = info.island_amount - (info.total_seven_count + info.total_eight_count)
    return {
        "island_weight": island_weight,
        "island_amount_weight": island_amount_weight,
        "below_seven_weight": float(below_seven_weight),
        "by_rule_steps": float(info.by_rule_steps),
        "brutal_steps": float(info.brutal_steps),
    }


def _normalise(value: float, lo: float, hi: float) -> float:
    """
    Linear clamp-and-rescale into [0, 1]. Degenerate ranges collapse to 0.
    """
    if hi == lo:
        return 0.0
    raw = (value - lo) / (hi - lo)
    if raw < 0.0:
        return 0.0
    if raw > 1.0:
        return 1.0
    return raw


def _nearest_geometry_key(difficulty_map: dict, width: int, height: int) -> str:
    """
    Picks the geometry key in difficulty_map closest to (width, height) by L1 distance.
    """
    best_key = None
    best_distance = None
    for key in difficulty_map.keys():
        w_str, h_str = key.split("x")
        w, h = int(w_str), int(h_str)
        distance = abs(w - width) + abs(h - height)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_key = key
    return best_key


def get_difficulty_value(grid: list[list[Node]], by_rule_steps: int, brutal_steps: int) -> float:
    """
    Returns a normalised difficulty score in [0, 1] for the given solved-puzzle data.

    Looks up per-geometry ranges in difficulty_map.json; falls back to the nearest
    available geometry if the exact (width, height) is not in the map.
    """
    info = inspect_puzzle(grid, by_rule_steps, brutal_steps)
    metrics = compute_metrics(info)
    difficulty_map = get_difficulty_map()

    key = f"{info.grid_width}x{info.grid_height}"
    if key not in difficulty_map:
        key = _nearest_geometry_key(difficulty_map, info.grid_width, info.grid_height)
    geom_ranges = difficulty_map[key]

    weights = {
        "island_weight":        ISLAND_WEIGHT_FACTOR,
        "island_amount_weight": ISLAND_AMOUNT_FACTOR,
        "below_seven_weight":   BELOW_SEVEN_FACTOR,
        "by_rule_steps":        BY_RULE_STEP_FACTOR,
        "brutal_steps":         BRUTAL_STEP_FACTOR,
    }

    difficulty = 0.0
    for metric in METRIC_KEYS:
        lo, hi = geom_ranges[metric]
        normalised = _normalise(metrics[metric], lo, hi)
        difficulty += normalised * weights[metric]
    return difficulty
