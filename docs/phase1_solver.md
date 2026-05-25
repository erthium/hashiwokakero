# Phase 1 — Completing the Solver

The solver currently exists as an in-progress refactor in the staged changes. The goal of Phase 1 is to leave the solver in a state where it correctly returns all (or the first) valid solutions for any well-formed hashi grid, tracks rule and brute-force step counts cleanly so the categoriser can consume them, and passes the test suite.

## Design intent

The puzzle, by its nature, may admit more than one valid solution (especially when rules alone do not suffice). The intended solver flow:

1. Apply deterministic rules until no rule fires.
2. If the grid is fully solved, return the single solution.
3. Otherwise, enter brute-force: pick one possible move, apply it, then re-run the rules. If the resulting state is consistent and the puzzle becomes solved, record the solution. If it becomes inconsistent, undo the move (and the rule-driven moves it triggered) and try the next candidate. Recurse until all moves are exhausted.
4. The solver exposes a switch — either stop at the first solution found, or exhaust the search and return every valid solution.

The "try a move, then let rules run" structure is deliberate: it matches how a human solver actually works, and it produces a more informative step trail for difficulty estimation (rule steps measure deductive depth, brute-force moves measure where deduction broke down).

### This is rules-first search, not full brute force

It is worth being explicit: at no point does the solver enumerate every combination of bridges across the grid. Each level of `solve_brutally` makes **one** speculative move, then hands the grid back to the rule engine to deduce as far as it can. The recursion only deepens when the rules made progress but could not finish, *and* the state is still consistent.

Concretely:

- `get_moves()` only enumerates candidate moves for **currently open islands** with **currently valid directions**, so the branching factor shrinks every time a rule fires.
- After every brute move, `solve_by_rules` typically closes many other islands deterministically — collapsing a huge swath of the state space before the next brute move is even considered.
- `is_solution_wrong()` at the top of `solve_brutally` prunes any branch where the rules have produced a disconnected dead group, so doomed states are abandoned immediately rather than explored.
- With `STOP_AT_FIRST_SOLUTION=True`, the entire search exits the moment one valid solution is recorded.

The effective search depth equals the number of forced choices the rules genuinely cannot deduce — on a well-formed hashi puzzle, typically 0–3. A pure brute-force solver would be `O(moves^depth)` over the entire grid; this design pays that cost only on the residual ambiguity the rules leave behind.

## Step counting rules

- `_step_count_rules` increments every time the rule loop inspects an open island, regardless of whether a bridge is built. This already works.
- `_step_count_brutal` increments **only** when a brute-force `make_move` is applied. Take-backs do **not** count — they are bookkeeping, not exploration.
- Each `Solution` carries its own `brutal_steps` snapshot at the moment it was recorded, so different solutions of the same puzzle can have different brutal counts.

## Solver switch

A module-level constant (or function argument) `STOP_AT_FIRST_SOLUTION: bool` controls termination:

- `True` (default for the categoriser path) — the first valid solution returned terminates the search; `brutal_steps` of that solution becomes the canonical difficulty signal.
- `False` (for inspection/debugging or puzzles where uniqueness matters) — the search exhausts every branch and returns the full list.

The cleanest shape is a keyword argument on the public `solve()` function, defaulting to `True`, with the value threaded through to `solve_brutally` via a module-global that `collect_garbage` resets.

---

## Steps

### 1.1 Strip debug artifacts from the solver

Remove the unconditional `print()` / `draw_grid()` calls in the solver:

- [hashi/solver.py:335-336](../hashi/solver.py#L335-L336) — inside `de_establish_bridge`
- [hashi/solver.py:351](../hashi/solver.py#L351) — inside `take_back_move`
- [hashi/solver.py:473-474](../hashi/solver.py#L473-L474) — inside `_solve_brutally_by_depth` (the unused depth-limited variant)
- [hashi/solver.py:541, 544-546](../hashi/solver.py#L541-L546) — inside `solve_brutally`

The `log_moves=True` branch in `establish_bridge` ([hashi/solver.py:229-233](../hashi/solver.py#L229-L233)) stays — it is real logic, not debug noise, because the by-rule move log is needed for brute-force backtracking.

If diagnostic output is wanted later, gate it on a single module-level `DEBUG` flag rather than scattering prints.

### 1.2 Delete the dead "First method"

The commented-out recursive variant at [hashi/solver.py:509-531](../hashi/solver.py#L509-L531) is no longer the chosen design. Remove it and the surrounding triple-quoted blocks so `solve_brutally` reads cleanly.

Also remove `_solve_brutally_by_depth` ([hashi/solver.py:466-489](../hashi/solver.py#L466-L489)) and the module-level `depth` counter ([hashi/solver.py:465](../hashi/solver.py#L465)) — they belong to the dead approach.

### 1.3 Make `solve_brutally` properly recursive

The current active body tries exactly one brute move and then runs rules — it does not recurse, so any puzzle that requires two or more unforced moves silently fails (this is almost certainly why the "Somehow brute force did not work" branch at [hashi/solver.py:588-591](../hashi/solver.py#L588-L591) ever fires).

New structure:

```
solve_brutally():
    if STOP_AT_FIRST_SOLUTION and _correct_solutions:
        return

    get_moves()
    if is_solution_wrong():
        return

    for move in snapshot of _current_moves:
        local_rule_log = []
        make_move(node_a, node_b, thickness)        # brute step; counted
        solve_by_rules(log_moves=True)              # appends to _by_rule_move_log
        local_rule_log = _by_rule_move_log[:]
        _by_rule_move_log = []

        if is_solution_correct():
            copy_correct_solution()
            if STOP_AT_FIRST_SOLUTION:
                undo(local_rule_log); take_back_move()
                return
        elif not is_solution_wrong():
            solve_brutally()                        # recurse

        undo(local_rule_log)                        # backtrack: rules first…
        take_back_move()                            # …then the brute move
```

Notes on this structure:

- `_by_rule_move_log` is module-global and shared, so the recursive call must snapshot and clear it before recursing, and the parent must own its own snapshot for undo. Without this, deeper recursions silently corrupt the parent's undo trail.
- `get_moves()` regenerates `_current_moves` from the live grid, so the iteration variable must be a snapshot (`for move in list(_current_moves):` or capture before the loop) — recursion will overwrite `_current_moves`.
- `is_solution_wrong()` short-circuits a branch that has split the islands into a disconnected group with no open island left — pruning here is what keeps the search tractable.
- The undo must always run, even on the early return when a solution is found, so the parent's grid state is preserved for its own iteration.

### 1.4 Stop counting take-backs as brute steps

[hashi/solver.py:344, 353](hashi/solver.py#L344-L353) — `make_move` and `take_back_move` both increment `_step_count_brutal`. Remove the increment in `take_back_move`. Brute steps become a count of *exploratory* moves only, which is the signal the categoriser actually wants.

### 1.5 Add the `STOP_AT_FIRST_SOLUTION` switch

Two layers:

- A module-level `_stop_at_first: bool` global, reset by `collect_garbage`, read by `solve_brutally`.
- A keyword argument on the public `solve(grid, stop_at_first: bool = True)` that writes the global at entry.

The categoriser and mass-production paths leave the default; tooling that wants to enumerate solutions passes `stop_at_first=False`. When the flag is `True`, both the top-level `solve_brutally` call and every recursive call check `_correct_solutions` and bail immediately if non-empty.

### 1.6 Clean up the `solve()` return path

[hashi/solver.py:578-596](../hashi/solver.py#L578-L596) — once 1.3 is in place, the "Somehow brute force did not work" branch should be unreachable for well-formed puzzles. Replace it with a single behaviour: if `_correct_solutions` is empty after brute force, return an empty list. Callers (including `main()` at [hashi/solver.py:599-604](../hashi/solver.py#L599-L604)) need to handle that — `main()` currently indexes `[0]` unconditionally and will crash on an unsolvable input. Either guard the index or assert non-empty with a clear message.

### 1.7 Decouple the solver from pygame

`solver.py` imports `draw_grid` and `print_node_data` from `visualiser`, which forces pygame to load on every solver run (including in tests, where `pygame` is not installed). After 1.1 and 1.2, neither symbol is referenced in solver logic — only in `main()`. Two options:

- Move the import inside `main()` so library use of the solver no longer touches pygame.
- Or, since `alternative.py` is the matplotlib visualiser used elsewhere, drop the import entirely and let `main()` use that.

Either way, `make test` should no longer require pygame to be installed.

### 1.8 Fix the test harness

[tests/hashi_test.py:48](../tests/hashi_test.py#L48) destructures `solved_grid, _, _ = solve(empty_grid)`, but `solve()` now returns `list[Solution]`. Change to:

```python
solutions = solve(empty_grid)
self.assertGreater(len(solutions), 0, f"No solution found for {filename}")
solved_grid = solutions[0].grid
```

The categoriser-path default (`stop_at_first=True`) is fine for the test — we are only checking that *a* valid solution matches the recorded solution grid. If any of the test puzzles have multiple valid solutions, this comparison will be flaky; in that case the test should compare against any solution in the list, not just `[0]`.

### 1.9 Validate against the new test puzzles

The 8 CSVs in [hashi/testdata/](../hashi/testdata/) are uncommitted generator output. Run the solver against each and confirm:

- Every puzzle returns at least one solution.
- For at least one puzzle, brute force actually fires (otherwise we have not exercised the recursive path).
- Step counts look reasonable: rule_steps grows with grid size, brutal_steps is small or zero on easy puzzles.

If any puzzle fails, that is a real solver bug — surface it before moving on.

### 1.10 Run the full test suite

`make test` should pass against both `tests/basic_puzzles/` and `tests/difficult_puzzles/` (the existing fixtures). If a difficult-puzzle case fails, it is either a genuine solver bug or a puzzle with multiple solutions where the recorded solution is not the one we find first — the fix depends on which.

---

## Deliverables for Phase 1

- `solver.py` cleaned of debug noise and the dead First method.
- `solve_brutally` recursive, with snapshotted rule logs and correct backtracking.
- `_step_count_brutal` counting only forward moves.
- `solve(grid, stop_at_first=True)` public signature with the switch wired through.
- `solver.py` no longer importing pygame at module load.
- `hashi_test.py` updated to the new return type; `make test` green.
- Confirmation that all 8 puzzles in `testdata/` solve, with at least one exercising the brute-force path.

Once these are done, the solver produces the data the categoriser needs (per-solution `rule_steps` and `brutal_steps`), and Phase 2 — fixing the difficulty map format and weights — can begin.
