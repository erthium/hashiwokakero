# Backlog

Items deferred from the active phase plans. Each entry names the source phase, what was deferred, and why we set it aside — so picking it up later doesn't require re-deriving the context.

---

## Difficulty bucketing (easy / intermediate / hard mapping)

**Source:** Phase 2, D7.

Phase 2 produces a normalised difficulty float in `[0, 1]` per puzzle. We did not pick how that float maps to discrete labels (`easy / intermediate / hard`, or any other naming).

When picking this up, decide:

- Fixed thresholds (e.g. `< 0.33 → easy`, `< 0.66 → intermediate`, else `hard`), or quantile thresholds computed from a calibration corpus.
- Number and naming of buckets — three may not be the right count for a book.
- Whether buckets are global or per-geometry. Per-geometry would mean a "hard 5×5" is hard only relative to other 5×5s; global would mean small grids almost never appear in `hard`.

Prerequisite for picking this up: at least one end-to-end production run that produces a corpus of scored puzzles, so the threshold choice can be made from observed distributions rather than guesses.

---

## Expand difficulty map geometry coverage

**Source:** Phase 2, D5.

Phase 2 maps only square geometries: `5×5, 10×10, …, 50×50` (10 geometries). Non-square geometries (e.g. `10×15`, `15×20`) and finer steps fall back to nearest-geometry lookup, which works but is approximate.

When picking this up:

- Add the rectangular geometries the project actually intends to ship (decide which combinations).
- Consider whether the step size should drop from 5 to something finer (e.g. step 2 or 3), or stay at 5.
- Total runtime scales linearly with the number of geometries × `ITERATION_COUNT` — budget accordingly.

The mapper's schema (dict keyed by `"WxH"`) already supports this without code changes; only the geometry list in `iterate_all_geometries` needs to grow.

---

## Bump sample size for difficulty map

**Source:** Phase 2, D4.

`ITERATION_COUNT = 200` is the starting point. If the 5th/95th percentile ranges look noisy or unstable between mapper runs, bump to 500 or 1000. Diminishing returns set in fast for percentile estimation, so 1000 is likely the practical ceiling.

Pair this with the *Expand difficulty map geometry coverage* item — both push total mapper runtime up, and they should be sized together.

---

## Tune categoriser factor weights

**Source:** Phase 2, D2.

Starting weights (locked for v1):

```
BRUTAL_STEP    = 0.45
ISLAND_WEIGHT  = 0.20
ISLAND_AMOUNT  = 0.20
BELOW_SEVEN    = 0.10
BY_RULE_STEP   = 0.05
```

These were chosen on prior, not data. Once a corpus of scored puzzles exists, revisit:

- Are `brutal_steps`-heavy puzzles scoring proportionally higher? If not, raise `BRUTAL_STEP_FACTOR`.
- Does `BELOW_SEVEN_FACTOR` add real signal, or correlate with `ISLAND_WEIGHT_FACTOR`? Could collapse to four factors.
- Is `BY_RULE_STEP_FACTOR` doing anything? It may correlate so heavily with grid size (already implicit in per-geometry normalisation) that it's pure noise.

Empirical tuning needs a ground-truth or proxy signal (human ratings, solve-time data) to be principled. Heuristic tuning by inspection is fine for v1; this entry only opens if v1 produces visibly wrong rankings.

---

## Parallelise the difficulty mapper

**Source:** Phase 2, step 2.8 — implicit.

Each `(geometry, sample)` pair is independent. If runtime becomes the bottleneck (especially after expanding geometry coverage or sample size), the mapper can fan out across processes — `multiprocessing.Pool` over the sample loop is the simplest fit because the solver is pure CPU and holds no shared state.

Not worth doing until single-process runtime hurts.

---

## Difficulty map samples a censored distribution

**Source:** Phase 2, mid-implementation (`MAX_BRUTAL_STEPS` budget).

The mapper aborts any puzzle whose solver exceeds `MAX_BRUTAL_STEPS = 1000` brute-force moves (override via `HASHI_MAP_MAX_BRUTAL`). Abandoned puzzles never enter the observation list, so the 5th/95th percentile bounds are computed over **puzzles solvable within the budget**, not over the full distribution of generated puzzles.

This is the right choice for calibration — pathological puzzles would otherwise contaminate the 95th percentile and stretch the score range so far that normal puzzles all crowd into the low end. But it has implications worth remembering when revisiting the categoriser:

- A puzzle scored at categorisation time with `brutal_steps > 1000` will clamp to 1.0 on the brutal_steps component. That is fine, but the upper bound was calibrated against the 95th percentile of *non-pathological* puzzles, so any puzzle near 1000 already saturates.
- If we ever want to bucket adversarial puzzles distinctly (e.g. an "extreme" tier above "hard"), we will need either a separate calibration without the budget or an explicit overflow signal.
- Bumping `MAX_BRUTAL_STEPS` later will widen the 95th percentile and rescale all difficulty scores — not a free change.

When picking this up: decide whether to keep the censored calibration or sample the full distribution with a longer per-puzzle timeout for the mapper specifically.

---

## Solver: enumerate-mode performance on larger grids

**Source:** Phase 1, validation step.

`solve(grid, stop_at_first=False)` on a 15×15 with a few brute-force moves did not finish within 120s. The default `stop_at_first=True` path is fast and is what Phase 2/3 use, so this does not block any current work — but if a downstream task ever needs full solution enumeration on larger grids (e.g. uniqueness verification for mass-produced book puzzles), this becomes load-bearing.

Likely improvements when picking this up:

- Order candidate moves by a heuristic (most-constrained island first) so the search prunes earlier.
- Add a transposition table or canonical-state cache to skip equivalent states.
- Add an explicit recursion-depth cap so callers can time-box the enumeration.

Uniqueness verification for production puzzles is the most likely trigger for this work — track it together with whatever phase introduces that requirement.
