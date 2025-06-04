import os
import pickle
import random
from typing import TypeVar, Generic, Protocol
from copy import deepcopy

from plugin_oracle.util.mod.mod import Mod

class HasHashAndInd(Protocol):
    hash: bytes
    name: str

T = TypeVar('T', bound=HasHashAndInd)

class MSet(Generic[T]):
    def __init__(self) -> None:
        self._U: dict[bytes, T] = {}
        self._fsets: dict[bytes, dict[bytes, float]] = {}
        self._bound: tuple[list[bytes], list[bytes]] = ([], [])
        self._e: float = 0.2

    @property
    def U(self) -> dict[bytes, T]:
        return self._U

    @property
    def min(self) -> list[bytes]:
        return self._bound[0]

    @property
    def max(self) -> list[bytes]:
        return self._bound[1]
    
    def __getitem__(self, hash: bytes) -> tuple[T, dict[bytes, float]]:
        return (self._U[hash], self._fsets[hash])
    
    def __contains__(self, hash: bytes) -> bool:
        return hash in self._U

    def addU(self, v: T) -> None:
        if v.hash in self._U:
            return
        self._U[v.hash] = v
        self._fsets[v.hash] = self._fsets.get(v.hash, {})
        self._fsets[v.hash].update({k: 1.0 for k in self._U.keys()})
        del self._fsets[v.hash][v.hash]
        for k in self._U.keys():
            if k != v.hash:
                self._fsets[k][v.hash] = 1.0
    
    def permutation(self, perm: list[bytes], state: bool) -> None:
        if any(hash not in self._U for hash in perm):
            raise ValueError('Unfiltered permutation encountered')
        if state:
            if perm < self._bound[0] or self._bound[0] == []:
                self._bound = (perm, self._bound[1])
            if perm > self._bound[1] or self._bound[1] == []:
                self._bound = (self._bound[0], perm)
        if state:
            for i in range(len(perm)):
                fset = self._fsets[perm[i]]
                for j in range(i):
                    fset[perm[j]] *= self._e
        else:
            l = len(perm)
            tU = set(self._U.keys())
            tlen = len(tU)
            for i in range(l):
                tU.discard(perm[i])
                fset = self._fsets[perm[i]]
                tlen -= 1
                for j in fset.keys():
                    if j in tU:
                        fset[j] += ((1 - self._e) / (tlen * (tlen - 1)))
                        if fset[j] > 1.0:
                            fset[j] = 1.0
    
    def edrop(self) -> 'MSet[T]':
        out = MSet[T]()
        out._U = self._U.copy() # pyright: ignore [reportConstantRedefinition]
        out._fsets = deepcopy(self._fsets)
        for k in out._U.keys():
            fset = out._fsets[k]
            follow = list(fset.keys())
            for m in follow:
                if fset[m] < (1 - self._e):
                    del fset[m]
        out._bound = self._bound
        return out
    
    def rtoposort(self, seed: int = 0) -> list[bytes] | None:
        adj = self._fsets
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
            for m in adj.get(n, {}):
                indegree[m] -= 1
                if indegree[m] == 0:
                    queue.append(m)
        random.seed()
        if len(L) != len(indegree):
            return None
        return L
    
    def toposort(self) -> list[bytes] | None:
        adj = self._fsets
        indegree = {k: 0 for k in adj}
        for vs in adj.values():
            for v in vs:
                indegree[v] = indegree.get(v, 0) + 1
        queue = [k for k, deg in indegree.items() if deg == 0]
        L: list[bytes] = []
        while queue:
            n = queue.pop()
            L.append(n)
            for m in adj.get(n, {}):
                indegree[m] -= 1
                if indegree[m] == 0:
                    queue.append(m)
        if len(L) != len(indegree):
            return None
        return L
    
    def assemble(self) -> None | list[tuple[bytes, bytes]]:
        leximin: list[bytes] = self._bound[0]
        leximax: list[bytes] = self._bound[1]
        if leximin == [] or leximax == []:
            return None
        anc: dict[bytes, list[None | bytes]] = {b: [None, None] for b in leximin}
        # Boolean markers for validation.
        hv: dict[bytes, bool] = {b: False for b in leximin}
        stack: list[bytes] = []

        # First pass: based on leximin.
        for b in leximin:
            while stack and stack[-1] < b:
                _ = stack.pop()
            if stack:
                anc[b][0] = stack[-1]
            stack.append(b)

        stack.clear()

        # Second pass: based on leximax.
        for b in leximax:
            while stack and stack[-1] > b:
                _ = stack.pop()
            hv[b] = True
            # If a parent was set in first pass but hasn't been marked yet, it's inconsistent.
            r = anc[b][0]
            if r is not None and not hv.get(r, False):
                return None
            if stack:
                if anc[b][0] is not None:
                    anc[b][1] = stack[-1]
                else:
                    anc[b][0] = stack[-1]
            stack.append(b)

        # Reset hv markers.
        for b in leximin:
            hv[b] = False

        # Third pass: validate that all assigned parents appear earlier.
        for b in leximin:
            hv[b] = True
            for parent in anc[b]:
                if parent is not None and not hv[parent]:
                    return None

        # Build the edge list: for every byte b, each non-None parent becomes an edge (parent -> b).
        elist: list[tuple[bytes, bytes]] = []
        for b in leximin:
            for parent in anc[b]:
                if parent is not None:
                    elist.append((parent, b))
        return elist

class MDB:
    _fname: str = '/db_1.pkl'

    def __init__(self) -> None:
        self.mod: MSet[Mod] = MSet[Mod]()
    
    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        dat = self.mod
        with open(path + MDB._fname, 'wb') as f:
            pickle.dump(dat, f)
    
    def load(self, path: str) -> None:
        path += MDB._fname
        if os.path.exists(path):
            with open(path, 'rb') as f:
                dat: MSet[Mod] = pickle.load(f)  # pyright: ignore [reportAny]
                self.mod = dat