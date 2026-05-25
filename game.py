"""
Pure game logic — no pygame dependency, safe to import from a solver.
"""
from __future__ import annotations
from typing import FrozenSet

from puzzles import PUZZLES

DIRECTIONS = {
    "up":    (-1,  0),
    "down":  ( 1,  0),
    "left":  ( 0, -1),
    "right": ( 0,  1),
}


class KestoGame:
    def __init__(self, puzzle_id: str) -> None:
        p = PUZZLES[puzzle_id]
        self.puzzle_id = puzzle_id
        self.rows: int = p["rows"]
        self.cols: int = p["cols"]
        self.obstacles: frozenset[tuple[int,int]] = frozenset(map(tuple, p["obstacles"]))
        self.targets:   frozenset[tuple[int,int]] = frozenset(map(tuple, p["targets"]))
        self._initial_oranges: list[tuple[int,int]] = [tuple(o) for o in p["oranges"]]
        self.oranges: list[tuple[int,int]] = list(self._initial_oranges)
        self.moves: int = 0
        self.history: list[list[tuple[int,int]]] = []
        self.solved: bool = False

    # ------------------------------------------------------------------ state

    @property
    def state(self) -> FrozenSet[tuple[int,int]]:
        """Hashable, order-independent snapshot — use as a solver dict key."""
        return frozenset(self.oranges)

    # ------------------------------------------------------------------ moves

    def move(self, direction: str) -> bool:
        """Slide all orange blocks in *direction*. Returns True if anything moved."""
        if self.solved:
            return False

        dr, dc = DIRECTIONS[direction]

        # Process blocks that move first so they don't block later ones.
        def lead_order(i: int) -> int:
            r, c = self.oranges[i]
            return -r if direction == "down" else r if direction == "up" else \
                   -c if direction == "right" else c

        new_oranges = list(self.oranges)
        occupied = set(new_oranges)

        for idx in sorted(range(len(new_oranges)), key=lead_order):
            r, c = new_oranges[idx]
            occupied.discard((r, c))
            nr, nc = r + dr, c + dc
            if (0 <= nr < self.rows and 0 <= nc < self.cols
                    and (nr, nc) not in self.obstacles
                    and (nr, nc) not in occupied):
                r, c = nr, nc
            new_oranges[idx] = (r, c)
            occupied.add((r, c))

        if new_oranges == self.oranges:
            return False

        self.history.append(list(self.oranges))
        self.oranges = new_oranges
        self.moves += 1
        self.solved = set(self.oranges) == self.targets
        return True

    def undo(self) -> bool:
        if not self.history:
            return False
        self.oranges = self.history.pop()
        self.moves -= 1
        self.solved = False
        return True

    def reset(self) -> None:
        self.oranges = list(self._initial_oranges)
        self.moves = 0
        self.history.clear()
        self.solved = False
