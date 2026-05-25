from game import KestoGame

g = KestoGame("20260525")
g.move("down")       # returns True if anything moved
g.state             # frozenset of orange positions — use as BFS/DFS dict key
g.solved            # bool
g.undo()
g.reset()
