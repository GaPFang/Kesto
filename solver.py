"""A* solver — finds the shortest move sequence for a Kesto puzzle."""
import heapq
from game import KestoGame

DIRS = ["up", "down", "left", "right"]


def _heuristic(oranges: list, targets: frozenset) -> int:
    """Admissible lower bound: each ply moves every block one step, so the
    minimum plies needed is at least the distance of the furthest orange from
    its nearest target."""
    return max(
        min(abs(r - tr) + abs(c - tc) for (tr, tc) in targets)
        for (r, c) in oranges
    )


def solve(puzzle_id: str) -> list[str] | None:
    """Return the shortest list of moves to solve *puzzle_id*, or None if unsolvable."""
    game = KestoGame(puzzle_id)
    if game.solved:
        return []

    targets = game.targets
    start   = game.state
    g0, h0  = 0, _heuristic(list(game.oranges), targets)

    # heap entries: (f, g, tie_counter, state, oranges)
    counter = 0
    heap = [(g0 + h0, g0, counter, start, list(game.oranges))]

    g_score: dict[frozenset, int] = {start: 0}
    parent:  dict[frozenset, tuple[frozenset, str] | None] = {start: None}

    while heap:
        _, g, _, state, oranges = heapq.heappop(heap)

        if g > g_score.get(state, float("inf")):
            continue  # stale entry

        for d in DIRS:
            child = KestoGame(puzzle_id)
            child.oranges = list(oranges)
            child.move(d)
            cstate = child.state

            if cstate == state:
                continue

            ng = g + 1
            if ng >= g_score.get(cstate, float("inf")):
                continue

            g_score[cstate] = ng
            parent[cstate] = (state, d)

            if child.solved:
                return _reconstruct(parent, cstate)

            counter += 1
            h = _heuristic(list(child.oranges), targets)
            heapq.heappush(heap, (ng + h, ng, counter, cstate, list(child.oranges)))

    return None


def _reconstruct(parent: dict, state: frozenset) -> list[str]:
    moves = []
    while parent[state] is not None:
        prev, move = parent[state]
        moves.append(move)
        state = prev
    moves.reverse()
    return moves


if __name__ == "__main__":
    import sys
    import time
    from puzzles import PUZZLES

    pid = sys.argv[1] if len(sys.argv) > 1 else next(iter(PUZZLES))
    print(f"Solving puzzle {pid} ...")
    t0 = time.perf_counter()
    result = solve(pid)
    elapsed = time.perf_counter() - t0
    if result is None:
        print(f"No solution found. ({elapsed*1000:.1f} ms)")
    else:
        print(f"Solved in {len(result)} moves in {elapsed*1000:.1f} ms: {result}")
