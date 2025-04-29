import os
import pickle

from plugin_oracle.util.mod import Mod

class MDB:
    _fname: str = '/db.pkl'

    def __init__(self) -> None:
        self.mods: dict[bytes, Mod] = {}
        self.fsets: dict[bytes, set[bytes]] = {}
        self._isets: dict[bytes, set[bytes]] = {}

    def fset(self, hash: bytes, inv: bool = True) -> set[bytes] | None:
        if not inv:
            return self._isets.get(hash, None)
        return self.fsets.get(hash, None)
    
    def mod(self, hash: bytes, create: bool = False) -> Mod | None:
        m = self.mods.get(hash, None)
        if m is None:
            if not create:
                return None
            m = Mod(hash)
            self.mods[hash] = m
            self.fsets[hash] = self.fsets.get(hash, set())
            self.fsets[hash].update(self.mods.keys())
            self.fsets[hash].discard(hash)
            for k in self.mods.keys():
                if k != hash:
                    self.fsets[k].add(hash)
            self._isets[hash] = self._isets.get(hash, set())
            self._isets[hash].update(self.mods.keys())
            self._isets[hash].discard(hash)
            for k in self.mods.keys():
                if k != hash:
                    self._isets[k].add(hash)
        return m

    def mod_req(self, hash: bytes) -> Mod:
        mod = self.mod(hash, True)
        if mod is None:
            raise ValueError(f"Mod with hash {hash} not found")
        return mod
    
    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        # Serialize as a tuple: (mods, fsets)
        dat: tuple[list[Mod], dict[bytes, set[bytes]], dict[bytes, set[bytes]]] = (list(self.mods.values()), self.fsets, self._isets)
        with open(path + MDB._fname, 'wb') as f:
            pickle.dump(dat, f)

    def load(self, path: str) -> None:
        path += MDB._fname
        if os.path.exists(path):
            with open(path, 'rb') as f:
                dat: tuple[list[Mod], dict[bytes, set[bytes]], dict[bytes, set[bytes]]] = pickle.load(f) # pyright: ignore [reportAny]
                mods, fsets, isets = dat
                self.mods = {m.hash: m for m in mods}
                self.fsets = fsets
                self._isets = isets

