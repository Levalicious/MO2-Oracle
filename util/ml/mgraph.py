from .bernoulli import Bernoulli
from ..mod.minfo import OMod

class GMod:
    def __init__(self, hash: bytes, onlyhash: bool = False) -> None:
        self.dist: Bernoulli | None = Bernoulli() if not onlyhash else None
        self.hash = hash

class ModPair:
    def __init__(self, m0: GMod, m1: GMod) -> None:
        self.mods = [m0, m1]
        self.dist = Bernoulli()

class MGraph:
    def __init__(self, onlyhash: bool = False) -> None:
        self._onlyhash = onlyhash
        self._nodes: dict[bytes, GMod] = {}
        self._edges: dict[bytes, ModPair] = {}
    
    def add_mod(self, mod: OMod) -> None:
        if mod.hash not in self._nodes:
            e = GMod(mod.hash, self._onlyhash)
            for n in self._nodes.values():
                self._edges[e.hash + n.hash] = ModPair(e, n)
                self._edges[n.hash + e.hash] = ModPair(n, e)
            self._nodes[mod.hash] = e
    
    def enabled(self, mmap: dict[bytes, OMod]) -> 'MGraph':
        g = MGraph()
        for n in self._nodes.values():
            if n.hash in mmap:
                if mmap[n.hash].state:
                    g._nodes[n.hash] = n
        for e in self._edges.values():
            if e.mods[0].hash in mmap and mmap[e.mods[0].hash].state:
                if e.mods[1].hash in mmap and mmap[e.mods[1].hash].state:
                    g._edges[e.mods[0].hash + e.mods[1].hash] = e
        return g
    

        