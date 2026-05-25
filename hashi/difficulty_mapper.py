"""
Generates many puzzles per square geometry, solves each, and records 5th/95th
percentile bounds for the five difficulty metrics. The resulting map is the
calibration input for cathegorise.get_difficulty_value.

Schema written to difficulty_map.json:
    {
        "5x5":  {"island_weight": [lo, hi], "island_amount_weight": [lo, hi], ...},
        "10x10": {...},
        ...
    }

Geometry coverage: square grids only, 5x5 through 50x50 in steps of 5.
Expanding to non-square or finer steps is tracked in docs/backlog.md.
"""

import multiprocessing as mp
import os
import queue as _queue
import random
import time

from node import Node
from generator import generate_till_full
from cathegorise import (
    METRIC_KEYS,
    inspect_puzzle,
    compute_metrics,
    save_diffiulty_map,
)
from solver import solve


ITERATION_COUNT: int = 1000
SQUARE_GEOMETRIES: list[tuple[int, int]] = [(s, s) for s in range(5, 51, 5)]
# Leave a couple of cores free for the OS / IDE on a 20-core box; the user can
# set HASHI_MAP_WORKERS to override.
WORKER_COUNT: int = int(os.environ.get("HASHI_MAP_WORKERS", max(1, mp.cpu_count() - 2)))
# Per-puzzle brute-force budget: abandon puzzles whose solver exceeds this many
# brute moves. Adversarial generations can spiral into millions of steps and
# would otherwise stall the run for minutes per outlier. Dropping the worst few
# percent of samples does not move the 5/95 percentile bounds meaningfully.
MAX_BRUTAL_STEPS: int = int(os.environ.get("HASHI_MAP_MAX_BRUTAL", "10000"))


def _percentile(sorted_values: list[float], pct: float) -> float:
    """
    Linear-interpolated percentile from a pre-sorted list. pct in [0, 100].
    """
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = rank - lower_index
    return sorted_values[lower_index] * (1 - fraction) + sorted_values[upper_index] * fraction


def _strip_bridges(grid: list[list[Node]]) -> None:
    """
    Resets a generated grid to its empty form: removes all bridges and zeroes
    every island's current_in. Required because generate_till_full leaves
    construction bridges in place, but solve() expects an empty grid.
    """
    for row in grid:
        for node in row:
            if node.n_type == 2:
                node.make_empty()
            elif node.n_type == 1:
                node.current_in = 0


# Per-worker shared queue; populated by the Pool initialiser so individual
# worker functions don't have to receive it as a task argument.
_WORKER_UPDATE_QUEUE = None
# Throttle solver-side callback updates to ~once per second per worker.
_PROGRESS_THROTTLE_S = 1.0


class _BrutalBudgetExceeded(Exception):
    """
    Raised from the worker's progress callback to abort a pathological puzzle
    whose brute-force step count has exceeded MAX_BRUTAL_STEPS. The worker
    catches it, marks the puzzle as abandoned, and continues with the next.
    """
    def __init__(self, rule_steps: int, brutal_steps: int):
        super().__init__(rule_steps, brutal_steps)
        self.rule_steps = rule_steps
        self.brutal_steps = brutal_steps


def _pool_init(update_queue) -> None:
    """
    Pool initialiser. Stashes the shared queue into the worker's module global
    so _solve_one_puzzle can publish phase/step updates without round-tripping
    the queue through every task arg.
    """
    global _WORKER_UPDATE_QUEUE
    _WORKER_UPDATE_QUEUE = update_queue


def _solve_one_puzzle(
    args: tuple[int, int, int, int],
) -> tuple[int, dict[str, float] | None, str | None]:
    """
    Worker entry point. Generates one puzzle, solves it, returns a triple of
    (task_id, metrics_or_None, reason_or_None) where `reason` is None on
    success and a short string ("unsolvable", "abandoned at brutal=…") on
    failure modes.

    Publishes phase/step updates on the shared queue so the main process can
    show what each in-flight worker is doing.

    A fresh per-task seed is critical: multiprocessing workers inherit the
    parent's RNG state at fork, so without re-seeding every worker would
    produce the same stream of puzzles.
    """
    width, height, seed, task_id = args
    random.seed(seed)

    started = time.time()
    if _WORKER_UPDATE_QUEUE is not None:
        _WORKER_UPDATE_QUEUE.put((task_id, "generate", started, 0, 0))

    grid = generate_till_full(width, height)
    _strip_bridges(grid)

    solve_started = time.time()
    if _WORKER_UPDATE_QUEUE is not None:
        _WORKER_UPDATE_QUEUE.put((task_id, "solve", solve_started, 0, 0))

    # Throttled solver-side progress publishing.
    last_pushed = [solve_started]

    def _on_solver_progress(rule_steps: int, brutal_steps: int) -> None:
        # Soft budget: abort the puzzle if brute search blows past the limit.
        if brutal_steps > MAX_BRUTAL_STEPS:
            raise _BrutalBudgetExceeded(rule_steps, brutal_steps)
        now = time.time()
        if now - last_pushed[0] >= _PROGRESS_THROTTLE_S:
            last_pushed[0] = now
            if _WORKER_UPDATE_QUEUE is not None:
                try:
                    _WORKER_UPDATE_QUEUE.put_nowait(
                        (task_id, "solve", solve_started, rule_steps, brutal_steps)
                    )
                except Exception:
                    pass

    abandoned_at: int | None = None
    try:
        solutions = solve(
            grid, stop_at_first=True, progress_callback=_on_solver_progress
        )
    except _BrutalBudgetExceeded as exc:
        solutions = []
        abandoned_at = exc.brutal_steps

    if _WORKER_UPDATE_QUEUE is not None:
        _WORKER_UPDATE_QUEUE.put((task_id, "done", started, 0, 0))

    if abandoned_at is not None:
        return (task_id, None, f"abandoned at brutal={abandoned_at}")
    if not solutions:
        return (task_id, None, "unsolvable")
    solution = solutions[0]
    info = inspect_puzzle(grid, solution.rule_steps, solution.brutal_steps)
    return (task_id, compute_metrics(info), None)


def _render_progress(label: str, done: int, amount: int, last_info: str) -> None:
    """
    Overwrites the current terminal line with a status snapshot.
    """
    print(f"\r\033[K  {label}: {done}/{amount} · {last_info}", end="", flush=True)


def _format_oldest_active(active: dict[int, tuple[str, float, int, int]]) -> str:
    """
    Picks the longest-running active worker and formats its status for display.
    """
    if not active:
        return "idle"
    task_id, (phase, started_at, rule, brutal) = min(
        active.items(), key=lambda kv: kv[1][1]
    )
    elapsed = time.time() - started_at
    if phase == "generate":
        return f"#{task_id}: generating · {elapsed:.1f}s"
    if phase == "solve":
        if rule == 0 and brutal == 0:
            return f"#{task_id}: solving · {elapsed:.1f}s"
        return (
            f"#{task_id}: solving · rule={rule} brutal={brutal} · {elapsed:.1f}s"
        )
    return f"#{task_id}: {phase} · {elapsed:.1f}s"


def _drain_updates(
    update_queue, active: dict[int, tuple[str, float, int, int]]
) -> None:
    """
    Pulls any pending worker updates off the queue and mutates the active-worker
    map in place. 'done' messages remove the worker from the map.
    """
    while True:
        try:
            task_id, phase, started_at, rule, brutal = update_queue.get_nowait()
        except _queue.Empty:
            return
        if phase == "done":
            active.pop(task_id, None)
        else:
            active[task_id] = (phase, started_at, rule, brutal)


def gather_geometry_metrics(
    width: int, height: int, amount: int, label: str = ""
) -> dict[str, list[float]]:
    """
    Generates `amount` puzzles at the given geometry across a worker pool,
    solves each, and returns the raw observed values of every metric.

    Workers publish phase/step updates through a shared queue so the main
    process can surface what each in-flight worker is doing — useful when
    one puzzle hits the long tail of brute-force search and stalls the
    counter for many seconds.
    """
    observations: dict[str, list[float]] = {key: [] for key in METRIC_KEYS}

    seed_source = random.SystemRandom()
    tasks = [
        (width, height, seed_source.randrange(2**31), task_id)
        for task_id in range(amount)
    ]

    workers = min(WORKER_COUNT, amount)
    done = 0
    last_completion = time.time()
    last_info = "starting…"
    active: dict[int, tuple[str, float, int, int]] = {}

    manager = mp.Manager()
    update_queue = manager.Queue()

    if label:
        _render_progress(label, done, amount, last_info)

    with mp.Pool(
        processes=workers,
        initializer=_pool_init,
        initargs=(update_queue,),
    ) as pool:
        result_iter = pool.imap_unordered(_solve_one_puzzle, tasks, chunksize=1)
        while done < amount:
            try:
                result = result_iter.next(timeout=0.5)
            except mp.TimeoutError:
                # No worker finished a task in the last 0.5s. Pull any in-flight
                # updates and show the slowest active worker so the user can see
                # what is actually taking time.
                _drain_updates(update_queue, active)
                if label:
                    idle = time.time() - last_completion
                    oldest = _format_oldest_active(active)
                    last_info = f"{oldest} · idle {idle:.1f}s"
                    _render_progress(label, done, amount, last_info)
                continue

            task_id, metrics, reason = result
            active.pop(task_id, None)
            _drain_updates(update_queue, active)

            gap_ms = (time.time() - last_completion) * 1000
            last_completion = time.time()
            done += 1

            if metrics is None:
                last_info = f"{reason} · gap {gap_ms:.0f}ms"
            else:
                last_info = (
                    f"rule={int(metrics['by_rule_steps'])} "
                    f"brutal={int(metrics['brutal_steps'])} · "
                    f"gap {gap_ms:.0f}ms"
                )
                for key in METRIC_KEYS:
                    observations[key].append(metrics[key])

            if label:
                _render_progress(label, done, amount, last_info)

    manager.shutdown()
    return observations


def geometry_ranges(observations: dict[str, list[float]]) -> dict[str, list[float]]:
    """
    Converts per-metric observation lists into 5th/95th percentile ranges.
    """
    ranges: dict[str, list[float]] = {}
    for key in METRIC_KEYS:
        values = sorted(observations[key])
        lo = _percentile(values, 5.0)
        hi = _percentile(values, 95.0)
        ranges[key] = [lo, hi]
    return ranges


def iterate_all_geometries(amount: int) -> dict[str, dict[str, list[float]]]:
    """
    Walks the locked geometry list, gathers samples, computes percentile ranges,
    and returns the full map. Persists incrementally so a long run can be inspected
    (or resumed manually) before completion.
    """
    difficulty_map: dict[str, dict[str, list[float]]] = {}

    import time
    total_start = time.time()
    for width, height in SQUARE_GEOMETRIES:
        key = f"{width}x{height}"
        geom_start = time.time()
        observations = gather_geometry_metrics(width, height, amount, label=key)
        difficulty_map[key] = geometry_ranges(observations)
        save_diffiulty_map(difficulty_map)
        elapsed = time.time() - geom_start
        # Overwrite the progress line with the final summary for this geometry.
        print(f"\r\033[K  {key} done in {elapsed:.1f}s. Ranges: " + ", ".join(
            f"{m}={difficulty_map[key][m][0]:.3f}..{difficulty_map[key][m][1]:.3f}"
            for m in METRIC_KEYS
        ), flush=True)

    print(f"All geometries mapped in {time.time() - total_start:.1f}s.", flush=True)
    return difficulty_map


def main():
    iterate_all_geometries(ITERATION_COUNT)


if __name__ == "__main__":
    main()
