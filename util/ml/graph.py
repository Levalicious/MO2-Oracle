import random

def random_toposort(adj: dict[bytes, set[bytes]], seed: int = 0) -> list[bytes] | None:
    """Return a random topological sort of the graph, or None if a cycle exists."""
    indegree = {k: 0 for k in adj}
    for vs in adj.values():
        for v in vs:
            indegree[v] = indegree.get(v, 0) + 1
    queue = [k for k, deg in indegree.items() if deg == 0]
    L: list[bytes] = []
    random.seed(seed)
    while queue:
        n = queue.pop(random.randrange(len(queue)))
        L.append(n)
        for m in adj.get(n, set()):
            indegree[m] -= 1
            if indegree[m] == 0:
                queue.append(m)
    random.seed()
    if len(L) != len(indegree):
        return None
    return L