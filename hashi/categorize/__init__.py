"""
Difficulty categorisation for hashi puzzles.

Public surface:
    get_difficulty_value(grid, by_rule_steps, brutal_steps) -> float in [0, 1]
    inspect_puzzle(grid, by_rule_steps, brutal_steps) -> PuzzleInformation
    compute_metrics(info) -> dict of raw metric values

Mass-calibration runner is in hashi.categorize.mapper.
"""

from hashi.categorize.categorize import (
    BELOW_SEVEN_FACTOR,
    BRUTAL_STEP_FACTOR,
    BY_RULE_STEP_FACTOR,
    FACTOR_WEIGHTS,
    ISLAND_AMOUNT_FACTOR,
    ISLAND_WEIGHT_FACTOR,
    MAP_PATH,
    METRIC_KEYS,
    PuzzleInformation,
    bucket,
    compute_metrics,
    get_difficulty_map,
    get_difficulty_value,
    inspect_puzzle,
    save_difficulty_map,
    score_from_metrics,
)

__all__ = [
    "BELOW_SEVEN_FACTOR",
    "BRUTAL_STEP_FACTOR",
    "BY_RULE_STEP_FACTOR",
    "FACTOR_WEIGHTS",
    "ISLAND_AMOUNT_FACTOR",
    "ISLAND_WEIGHT_FACTOR",
    "MAP_PATH",
    "METRIC_KEYS",
    "PuzzleInformation",
    "bucket",
    "compute_metrics",
    "get_difficulty_map",
    "get_difficulty_value",
    "inspect_puzzle",
    "save_difficulty_map",
    "score_from_metrics",
]
