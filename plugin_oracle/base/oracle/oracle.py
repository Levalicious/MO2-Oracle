from random import shuffle
from mobase import IModList, IOrganizer, IModInterface, IPluginList # pyright: ignore [reportMissingModuleSource]
from plugin_oracle.util.mod.mo2 import modhash, esshash, allMods, setHash, getHash, isActive, isEssential
from plugin_oracle.base.db import MDB
from plugin_oracle.util.log import PluginLogger, getLogger
from plugin_oracle.base.sync import pluginsync
from concurrent.futures import ThreadPoolExecutor
from time import time
import os
from plugin_oracle.base.oracle.chresmolyte import Chresmolyte
from hashlib import sha256

from plugin_oracle.util.mod.mod import Mod

class Oracle:
    def __init__(self, path: str = '') -> None:
        self._log: PluginLogger = PluginLogger(getLogger(__name__), {'name': 'Oracle'})
        self.path: str = path
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)
        self.db: MDB = MDB()
        self.chresm: Chresmolyte = Chresmolyte()

    def save(self) -> None:
        self.db.save(self.path)
    
    def load(self) -> None:
        self.db.load(self.path)
        
    def addMod(self, mod: IModInterface, organizer: IOrganizer) -> bytes | None:
        try:
            hash = modhash(mod, organizer)
            setHash(mod, hash)
            return hash
        except:
            self._log.warning(f'Failed to find an installation file for {mod.name()}! Plugin will ignore this mod')
            return None
    
    def _resolve(self, mlist: IModList, organizer: IOrganizer, verbose: bool = False) -> list[tuple[bytes, IModInterface]]:
        def chash(mod: IModInterface) -> tuple[bytes, IModInterface] | None:
            try:
                if not isEssential(mod, mlist):
                    hash = getHash(mod)                
                    if hash is None:
                        hash = modhash(mod, organizer)
                        setHash(mod, hash)
                    return (hash, mod)
                
                if not mod.absolutePath().endswith('/data'):
                    raise Exception('a')

                return (esshash(mod), mod)
            except:
                if verbose:
                    self._log.warning(f'Failed to find an installation file for {mod.name()}! Plugin will ignore this mod')
                return None

        mods = allMods(mlist)
        if len(mods) > 32:
            with ThreadPoolExecutor() as exec:
                hashes = exec.map(chash, mods)
        else:
            hashes = map(chash, mods)
        return [hash for hash in hashes if hash is not None]

    def resolve(self, mlist: IModList, organizer: IOrganizer, verbose: bool = True) -> None:
        t0 = time()
        vers = sha256(organizer.managedGame().gameVersion().encode('ascii')).digest()
        gm: Mod = self.db.mod.U.get(vers, Mod(vers))
        self.db.mod.addU(gm)
        gm.name = f'{organizer.managedGame().gameName()} : {organizer.managedGame().gameVersion()}'
        mods = self._resolve(mlist, organizer, verbose)
        for mod in mods:
            m = self.db.mod.U.get(mod[0], Mod(mod[0]))
            self.db.mod.addU(m)
            m.name = mod[1].name()
        t1 = time()
        self._log.info(f'Resolved mods in {t1 - t0}s')
    
    def permutation(self, mlist: IModList, organizer: IOrganizer) -> list[bytes]:
        mods = self._resolve(mlist, organizer)
        active = list(filter(lambda mod: isActive(mod[1], mlist) or isEssential(mod[1], mlist), mods))
        active.sort(key=lambda mod: mlist.priority(mod[1].name()))
        vers = sha256(organizer.managedGame().gameVersion().encode('ascii')).digest()
        return [vers] + [mod[0] for mod in active]
    
    def observe(self, result: bool, mlist: IModList, organizer: IOrganizer) -> None:
        t0 = time()
        loadorder = self.permutation(mlist, organizer)
        self.db.mod.permutation(loadorder, result)
        t1 = time()
        self._log.info(f'Recorded run in {t1 - t0}s')

    def sample(self, mlist: IModList, plist: IPluginList, organizer: IOrganizer) -> None:
        t0 = time()
        ld = self.db.mod.rtoposort(True)
        if ld is None:
            self._log.warning('Failed to find a topological sort!')
            return
        order: list[str] = []
        for h in ld:
            order.append(self.db.mod.U[h].name)
        order = order[1:]
        for i in range(len(order)):
            _ = mlist.setPriority(order[i], i)
        pluginsync(organizer, mlist, plist)
        t1 = time()
        self._log.info(f'Derived and applied new order in {t1 - t0}s')

    def samplerandom(self, mlist: IModList, plist: IPluginList, organizer: IOrganizer) -> None:
        t0 = time()
        ld = self.permutation(mlist, organizer)[1:]
        order: list[str] = []
        for h in ld:
            m: Mod = self.db.mod.U.get(h, Mod(h))
            self.db.mod.addU(m)
            order.append(m.name)
        shuffle(order)
        for i in range(len(order)):
            _ = mlist.setPriority(order[i], i)
        pluginsync(organizer, mlist, plist)
        t1 = time()
        self._log.info(f'Derived and applied new order in {t1 - t0}s')

    def predict(self, mlist: IModList, organizer: IOrganizer) -> str:
        loadorder = self.permutation(mlist, organizer)
        report: list[tuple[str, str]] = []
        for i, hash in enumerate(loadorder):
            _, fset, _ = self.db.mod[hash]
            for j in range(i + 1, len(loadorder)):
                if fset is None or loadorder[j] not in fset:
                    m0: Mod = self.db.mod.U.get(hash, Mod(hash))
                    m1: Mod = self.db.mod.U.get(loadorder[j], Mod(loadorder[j]))
                    self.db.mod.addU(m0)
                    self.db.mod.addU(m1)
                    report.append((m0.name, m1.name))
        sreport = ''
        for pair in report:
            sreport += f'{pair[0]} -> {pair[1]}\n'
        if len(report):
            return f'Invalid orders:\n{sreport}'
        return 'No invalid orders detected.'

    

