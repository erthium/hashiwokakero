# Phase 2 — Designing the Categoriser

Phase 2 is about deciding **how** the categoriser computes difficulty, not just wiring up the existing formulas. The pre-refactor state of the project has a categoriser whose contract does not match its data file, several formulas that are likely bugs, and zero weight on the solver-derived signals that Phase 1 just unlocked. We re-design first, then implement.

## What "difficulty" should mean

There are two coherent definitions, and they imply different normalisations:

1. **Within-geometry difficulty** — every (width, height) gets its own easy/hard distribution. An "easy 10×10" feels comparable to an "easy 30×30" in terms of cognitive challenge for its size; a "hard 10×10" sits at the top of the 10×10 distribution.
2. **Absolute difficulty** — one global distribution across all geometries. A 5×5 is almost always "easy" and a 50×50 is almost always "hard" because the raw counts dominate.

For a puzzle book or training dataset, **within-geometry** is the useful definition — you want variety of geometries at each difficulty tier. Recommendation: per-geometry normalisation. The current code in `difficulty_mapper.py` already gathers per-geometry boundaries, so this aligns with the staged design intent.

## Existing problems to address

Before re-designing, three concrete issues in the staged code must be fixed:

- **Storage format mismatch.** `cathegorise.get_difficulty_value` indexes `difficulty_map["island_weight"]` (dict keyed by metric), but the on-disk `difficulty_map.json` is a flat list of `[w, h, lower, upper]` tuples from an earlier design. Neither matches what `difficulty_mapper.genearate_and_cathegorise` builds (per-geometry dict of metric → `[min, max]`). All three need to agree.
- **`save_diffiulty_map` is commented out** at [difficulty_mapper.py:86](../hashi/difficulty_mapper.py#L86), so the new format is never persisted.
- **`island_amount_weight` formula is almost certainly wrong:**
  ```python
  info.island_amount / (info.grid_width + info.grid_height) / 2
  ```
  This computes `island_amount / (2*(w+h))`. For a 10×10 with 30 islands that's `30/40 = 0.75`. For a 20×20 with 120 islands that's `120/80 = 1.5`. The metric is not a "weight" in any meaningful sense, and it does not scale with grid area. The intent was almost certainly **island density**, i.e. `island_amount / (w * h)`, which is bounded in [0, 1]. Fix this before regenerating the map.

## Decisions to settle in Phase 2

### D1: Categoriser input — structural only, or solver-augmented?

Two options for what `get_difficulty_value` consumes:

- **Structural-only:** island count, island sizes, density. Cheap; can be computed without solving.
- **Solver-augmented:** add `rule_steps` and `brutal_steps` from the solver.

Recommendation: **solver-augmented**. Mass production already runs the solver per puzzle (to verify solvability and uniqueness), so the marginal cost of capturing the step counts is zero. And `brutal_steps > 0` is by far the strongest "this puzzle requires guessing" signal in the data — exactly what we want difficulty to capture.

### D2: Weight allocation across the five factors

**Decision (locked):** starting weights below; re-tune later if the spot-check in step 2.10 shows poor separation.

Currently:
```
ISLAND_WEIGHT  = 0.61   (avg island count)
ISLAND_AMOUNT  = 0.33   (density)
BELOW_SEVEN    = 0.06   (count of islands with i_count < 7)
BY_RULE_STEP   = 0.00
BRUTAL_STEP    = 0.00
```

These were set when the solver did not report step counts. Now that it does, the weights should shift. `brutal_steps` is the cleanest behavioural signal — a puzzle that requires guesswork is hard, full stop. `rule_steps` mostly tracks puzzle size (already captured by geometry), so it deserves modest weight at best.

Recommended starting point (sum to 1):

```
BRUTAL_STEP    = 0.45   (behavioural — strongest signal)
ISLAND_WEIGHT  = 0.20   (intrinsic structural)
ISLAND_AMOUNT  = 0.20   (intrinsic structural)
BELOW_SEVEN    = 0.10   (small-island prevalence)
BY_RULE_STEP   = 0.05   (mostly a size proxy)
```

These are starting weights, not final ones — Phase 2 ends with a tuning step where we generate a sample of puzzles, eyeball the resulting bucket distribution, and adjust if the brackets look skewed.

### D3: Range estimator — min/max, or percentile?

True min/max is fragile to outliers: one anomalous puzzle stretches the range and squashes every normalised score into a narrow band. Percentile-based ranges (e.g. 5th/95th) are robust and produce more uniform difficulty scores.

Recommendation: **percentile ranges (5th and 95th)**, with values outside the range clamped to `[0, 1]` after normalisation. This is the standard fix for outlier-bounded normalisation.

### D4: Sample size per geometry

**Decision (locked):** 200 iterations per geometry.

`ITERATION_COUNT` is currently 1, which makes the map effectively meaningless. 200 samples are enough for stable 5th/95th percentiles and small enough to keep total runtime tractable when paired with the square-only geometry list in D5 (10 geometries × 200 = 2,000 solves).

### D5: Geometry coverage

**Decision (locked):** square geometries only — `5×5, 10×10, 15×15, 20×20, 25×25, 30×30, 35×35, 40×40, 45×45, 50×50`.

These match the geometries the project actually ships. Mapping non-square or off-step geometries is deferred to the backlog (see [backlog.md](backlog.md) — *Expand difficulty map geometry coverage*).

For any geometry not in the map (e.g. `12×17`, or `10×15` until we decide to add it), `get_difficulty_value` falls back to **nearest-geometry lookup** — the dict key minimising `|w - target_w| + |h - target_h|`. Simpler than 2D interpolation across five metrics, and consistent with the square-only design.

### D6: Storage schema

Three internally-consistent options:

Option A — dict keyed by `"WxH"`:
```json
{
  "5x5":  {"island_weight": [1.48, 2.96], "island_amount_weight": [...], ...},
  "5x10": {...},
  ...
}
```

Option B — list of geometry dicts (closest to what `genearate_and_cathegorise` already returns):
```json
[
  {"width": 5, "height": 5, "island_weight": [1.48, 2.96], ...},
  {"width": 5, "height": 10, ...},
  ...
]
```

Option C — keep the old flat-tuple list (incompatible with the new factor design — rejected).

Recommendation: **Option A**. O(1) lookup by geometry string, no scan needed. Trivial to read and edit by hand if a value ever needs tweaking.

### D7: Bucket thresholds — deferred

**Decision (locked):** Phase 2 outputs only the normalised difficulty value (a float in `[0, 1]`) per puzzle. No bucketing into easy/intermediate/hard.

The bucketing decision (fixed thresholds vs quantile-based vs labels named differently) is deferred to a later phase, once we have a corpus of scored puzzles and can choose thresholds from observation rather than guesswork. Tracked in [backlog.md](backlog.md) — *Difficulty bucketing (easy/intermediate/hard mapping)*.

### D8: Categorising multi-solution puzzles

`solve(grid, stop_at_first=True)` returns one solution and its `brutal_steps`. For production we want unique-solution puzzles, but the **uniqueness check** belongs in Phase 3 (it requires `stop_at_first=False` and is expensive). For Phase 2, the categoriser treats whatever `stop_at_first=True` returns as canonical — that's the path the mapper uses too, so the calibration and the lookup see consistent data.

### D9: `brutal_steps_list` vs single `brutal_steps`

`get_difficulty_value` currently takes a `brutal_steps_list: list[int]` and averages it. But `solve(stop_at_first=True)` returns a single solution. The list shape was inherited from the multi-solution path.

Recommendation: change the signature to accept a single `brutal_steps: int`. If the caller ever wants multi-solution categorisation they can pass `min(s.brutal_steps for s in solutions)` or similar — but the categoriser itself takes one number. This also aligns with the difficulty map, which stores ranges over single values, not averages.

---

## Steps

### 2.1 Fix `island_amount_weight` (semantic bug)

[hashi/cathegorise.py:109](../hashi/cathegorise.py#L109) — change to true density:

```python
island_amount_weight = info.island_amount / (info.grid_width * info.grid_height)
```

Apply the same correction in `difficulty_mapper.genearate_and_cathegorise` at [difficulty_mapper.py:49](../hashi/difficulty_mapper.py#L49). Both code paths must compute the metric the same way.

### 2.2 Switch the storage schema (D6)

- `genearate_and_cathegorise` returns its existing per-geometry dict unchanged.
- `iterate_all_geometries` accumulates into a dict keyed by `f"{w}x{h}"` instead of a list, and writes it once at the end.
- `save_diffiulty_map` / `get_diffiulty_map` already use plain `json.dump/load`, so no API change.

### 2.3 Switch ranges to percentile (D3)

In `genearate_and_cathegorise`, replace the running min/max with a list per metric that accumulates every observation. After the inner loop:

```python
import numpy as np
result["island_weight"] = [
    float(np.percentile(observations["island_weight"], 5)),
    float(np.percentile(observations["island_weight"], 95)),
]
# … same for every metric
```

If pulling in numpy is unwanted, use `statistics.quantiles(data, n=20)` and take index 0 and 18, or write a 10-line percentile helper. Numpy is the standard choice.

### 2.4 Categoriser signature change (D9)

`get_difficulty_value(grid, by_rule_steps, brutal_steps_list)` → `get_difficulty_value(grid, by_rule_steps, brutal_steps)`. Remove the `sum/len` averaging. Update every caller (`difficulty_mapper.py`, eventually `production.py`).

### 2.5 Per-geometry lookup + clamp (D1, D3)

In `get_difficulty_value`:

```python
key = f"{info.grid_width}x{info.grid_height}"
geom_ranges = difficulty_map.get(key) or _nearest_geometry(difficulty_map, info.grid_width, info.grid_height)

def _normalise(value, lo, hi):
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))
```

`_nearest_geometry` is a tiny helper that picks the dict key minimising `|w - target_w| + |h - target_h|` for unmatched geometries (D5 fallback).

### 2.6 Rebalance factor weights (D2)

Update the module-level constants in `cathegorise.py` to the recommended split:

```python
BRUTAL_STEP_FACTOR    = 0.45
ISLAND_WEIGHT_FACTOR  = 0.20
ISLAND_AMOUNT_FACTOR  = 0.20
BELOW_SEVEN_FACTOR    = 0.10
BY_RULE_STEP_FACTOR   = 0.05
```

Add an `assert` that the five factors sum to `1.0 ± 1e-6` so future edits can't silently violate it.

### 2.7 Restrict geometry coverage to squares (D5)

Rewrite `iterate_all_geometries` to walk a fixed list of square geometries rather than the cartesian product:

```python
SQUARE_GEOMETRIES = [(s, s) for s in range(5, 51, 5)]
```

This produces 10 geometries (5×5 through 50×50). The dict-keyed map from step 2.2 then has 10 entries.

### 2.8 Run the mapper end-to-end

- Set `ITERATION_COUNT = 200`.
- `make map` solves 10 × 200 = 2,000 puzzles, percentile-normalises each geometry, writes `difficulty_map.json`.
- Expected runtime: dominated by 35×35+ geometries — order of tens of minutes to ~an hour.
- If a single geometry blows the budget, lower the upper bound for now and add a backlog entry to revisit (`Expand difficulty map geometry coverage`).

### 2.9 Spot-check categorisation

Generate ~30 puzzles per geometry at three sizes (10×10, 20×20, 30×30), run them through `get_difficulty_value`, and inspect the resulting normalised values. Sanity checks:

- The distribution of scores should cover most of `[0, 1]` — not collapse into a narrow band.
- A puzzle the solver finishes by rules alone (`brutal_steps = 0`) should score noticeably lower than one with `brutal_steps ≥ 5` at the same geometry.
- Scores should be roughly comparable across geometries (a "medium" 10×10 ≈ a "medium" 30×30 in normalised terms). This is the within-geometry-normalisation design from D1 working as intended.

### 2.10 Tune weights if needed

If the spot-check shows score distributions that don't separate puzzles well (e.g. brute-force puzzles not scoring meaningfully higher than rule-only puzzles of the same geometry), adjust the factor weights in step 2.6 — push more weight onto `BRUTAL_STEP_FACTOR`. Re-run the spot check after each adjustment. Stop when the ordering looks right on a sample of ~50 puzzles per size.

---

## Deliverables for Phase 2

- `cathegorise.py` — fixed `island_amount_weight` formula, per-geometry lookup with nearest-geometry fallback, percentile-clamped normalisation, single-value `brutal_steps` signature, rebalanced weights. **No bucketing** — `get_difficulty_value` returns a normalised float and that is the categoriser's contract.
- `difficulty_mapper.py` — uncommented save, percentile range computation, dict-keyed schema, square-only geometries, `ITERATION_COUNT = 200`.
- `difficulty_map.json` — regenerated from scratch under the new schema, 10 square geometries.
- A sanity-checked categorisation pipeline ready to be plugged into Phase 3's mass production.

Once these are done, the categoriser produces a meaningful `float ∈ [0, 1]` per puzzle. Mapping that float to easy/intermediate/hard labels (or whatever bucket scheme we eventually use) is deferred — see [backlog.md](backlog.md).
