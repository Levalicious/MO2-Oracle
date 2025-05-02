import os
import pickle
import random
from typing import TypeVar, Generic, Protocol

from plugin_oracle.util.mod.mod import Mod

class HasHashAndInd(Protocol):
    hash: bytes
    name: str

T = TypeVar('T', bound=HasHashAndInd)

class MSet(Generic[T]):
    def __init__(self) -> None:
        self._U: dict[bytes, T] = {}
        self._fsets: dict[bytes, set[bytes]] = {}
        self._isets: dict[bytes, set[bytes]] = {}
        self._bound: tuple[list[bytes], list[bytes]] = ([], [])

    @property
    def U(self) -> dict[bytes, T]:
        return self._U

    @property
    def min(self) -> list[bytes]:
        return self._bound[0]

    @property
    def max(self) -> list[bytes]:
        return self._bound[1]
    
    def __getitem__(self, hash: bytes) -> tuple[T | None, set[bytes] | None, set[bytes] | None]:
        return (self._U.get(hash, None), self._fsets.get(hash, None), self._isets.get(hash, None))

    def addU(self, v: T) -> None:
        if v.hash in self._U:
            return
        self._U[v.hash] = v
        self._fsets[v.hash] = self._fsets.get(v.hash, set())
        self._fsets[v.hash].update(self._U.keys())
        self._fsets[v.hash].discard(v.hash)
        for k in self._U.keys():
            if k != v.hash:
                self._fsets[k].add(v.hash)
        self._isets[v.hash] = self._isets.get(v.hash, set())
        self._isets[v.hash].update(self._U.keys())
        self._isets[v.hash].discard(v.hash)
        for k in self._U.keys():
            if k != v.hash:
                self._isets[k].add(v.hash)
    
    def permutation(self, perm: list[bytes], state: bool) -> None:
        if any(hash not in self._U for hash in perm):
            raise ValueError('Unfiltered permutation encountered')
        if state:
            if perm < self._bound[0]:
                self._bound = (perm, self._bound[1])
            if perm > self._bound[1]:
                self._bound = (self._bound[0], perm)

        for i in range(len(perm)):
            fset = self._fsets[perm[i]] if state else self._isets[perm[i]]
            for j in range(i):
                fset.discard(perm[j])
    
    def rtoposort(self, state: bool, seed: int = 0) -> list[bytes] | None:
        adj = self._fsets if state else self._isets
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
    
    def toposort(self, state: bool) -> list[bytes] | None:
        adj = self._fsets if state else self._isets
        indegree = {k: 0 for k in adj}
        for vs in adj.values():
            for v in vs:
                indegree[v] = indegree.get(v, 0) + 1
        queue = [k for k, deg in indegree.items() if deg == 0]
        L: list[bytes] = []
        while queue:
            n = queue.pop()
            L.append(n)
            for m in adj.get(n, set()):
                indegree[m] -= 1
                if indegree[m] == 0:
                    queue.append(m)
        if len(L) != len(indegree):
            return None
        return L

class MDB:
    _fname: str = '/db_0.pkl'

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