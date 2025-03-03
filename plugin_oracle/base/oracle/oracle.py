from mobase import IModList, IModInterface, ModState
from ...util.mod.minfo import OMod
from ...util.ml.mgraph import MGraph
from ...util.log import PluginLogger, getLogger
import pickle
import os
from logging import getLogger
from concurrent.futures import ThreadPoolExecutor
import random


class Oracle:
    def __init__(self) -> None:
        self._log = PluginLogger(getLogger(__name__), {'name': 'Oracle'})
        self.path = ''
        self._lgraph = MGraph()
        self._hgraph = MGraph(True)
        self._mmap: dict[bytes, OMod] = {}
        self._ecnt: int = 0
    
    def add_mod(self, mod: IModInterface, mlist: IModList) -> None:
        omod = OMod(mod, mlist)
        if omod.hash in self._mmap:
            return
        self._lgraph.add_mod(omod)
        self._hgraph.add_mod(omod)
        self._mmap[omod.hash] = omod

    def add_omod(self, omod: OMod) -> None:
        if omod.hash in self._mmap:
            return
        self._lgraph.add_mod(omod)
        self._hgraph.add_mod(omod)
        self._mmap[omod.hash] = omod

    def save(self) -> None:
        if self.path == '':
            return
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)
        lgraph_path = self.path + '/lgraph.pkl'
        hgraph_path = self.path + '/hgraph.pkl'

        with open(lgraph_path, 'wb') as f:
            pickle.dump(self._lgraph, f)
        with open(hgraph_path, 'wb') as f:
            pickle.dump(self._hgraph, f)
        self._log.info(f'Save complete')

    def load(self) -> None:
        lgraph_path = self.path + '/lgraph.pkl'
        hgraph_path = self.path + '/hgraph.pkl'
        if not os.path.exists(lgraph_path) or not os.path.exists(hgraph_path):
            return

        with open(lgraph_path, 'rb') as f:
            self._lgraph = pickle.load(f)
        with open(hgraph_path, 'rb') as f:
            self._hgraph = pickle.load(f)
        self._log.info(f'Load complete')
    
    def refresh(self, mlist: IModList) -> None:
        mnames = [mname for mname in mlist.allModsByProfilePriority()]
        for omod in self._mmap.values():
            if omod.name in mnames:
                omod.mod = mlist.getMod(omod.name)
                omod.mlist = mlist
    
    def resolve(self, mlist: IModList) -> None:
        self.refresh(mlist)
        mnames = [mname for mname in mlist.allModsByProfilePriority()]
        for omod in self._mmap.values():
            if omod.name in mnames:
                mnames.remove(omod.name)
        tlist: list[str] = []
        self._ecnt = 0
        for mname in mnames:
            if (mlist.state(mname) & (ModState.ACTIVE)) != 0:
                tlist.append(mname)
            if (mlist.state(mname) & (ModState.ESSENTIAL)) != 0:
                self._ecnt += 1
        mnames = tlist

        if len(mnames) == 0:
            return
        self._log.info(f'Resolving {len(mnames)} mods')
        self._log.info(f'{mnames}')
        
        mods = [mlist.getMod(mname) for mname in mnames]
        if len(mods) > 32:
            with ThreadPoolExecutor() as executor:
                def process(mod) -> OMod | str:
                    om = OMod(mod, mlist)
                    if not om.state:
                        return om.name
                    om.dhash()
                    return om
                omods = executor.map(process, mods)
        else:
            omods = map(lambda om: (om) if om.state else om.name, map(lambda mod: OMod(mod, mlist), mods))
        for om in omods:
            if isinstance(om, OMod):
                self.add_omod(om)
                if om.name in mnames:
                    mnames.remove(om.name)
            elif isinstance(om, str):
                mnames.remove(om)
        self._log.info('Mods resolved')
        if mnames:
            self._log.warning('Failed to find/process the following mods:')
            for mname in mnames:
                self._log.warning(f'{mname}')
    
    def observe(self, mlist: IModList, result: bool) -> None:
        self.refresh(mlist)
        omodhashes: list[bytes] = list(self._mmap.keys())
        omodhashes = list(filter(lambda h: self._mmap[h].state, omodhashes))
        omodhashes.sort(key=lambda h: self._mmap[h].index)
        self._log.info('Active mods:')
        for h in omodhashes:
            omod = self._mmap[h]
            self._log.info(f'{omod.name} : {omod.hash.hex()}')
        for ind, h in enumerate(omodhashes):
            self._lgraph._nodes[h].dist.observe(result) # type: ignore
            for ind2, h2 in enumerate(omodhashes):
                if ind == ind2:
                    continue
                if h == h2:
                    continue
                if ind < ind2:
                    self._hgraph._edges[h + h2].dist.observe(result)
                else:
                    self._hgraph._edges[h2 + h].dist.observe(result)
        for i in range(len(omodhashes) - 1):
            self._lgraph._edges[omodhashes[i] + omodhashes[i + 1]].dist.observe(result)
        self._log.info('Run recorded')

    def sample(self, hi: bool = True, iters: int = 10, infogain: bool = False) -> None:
        hegraph = self._hgraph.enabled(self._mmap)
        legraph = self._lgraph.enabled(self._mmap)
        order = self.btderive(hegraph if hi else legraph, iters, infogain)
        for i in range(len(order)):
            self._mmap[order[i]].index = i + self._ecnt
        
    def btderive(self, graph: MGraph, iters: int = 10, infogain: bool = False) -> list[bytes]:
        def btiter(scores: dict[bytes, float], weights: dict[bytes, list[float]]) -> dict[bytes, float]:
            for node in graph._nodes.values():
                num = 0.0
                den = 0.0
                for node2 in graph._nodes.values():
                    if node.hash != node2.hash:
                        num += (scores[node2.hash] / (scores[node.hash] + scores[node2.hash]))
                        den += (scores[node.hash] + scores[node2.hash])
                num *= weights[node.hash][0]
                den = weights[node.hash][1] / den
                scores[node.hash] = num / den
            gmean = 1.0
            for node in graph._nodes.values():
                gmean *= scores[node.hash]
            gmean **= (1 / len(graph._nodes))
            gmean = 1 / gmean
            for node in graph._nodes.values():
                scores[node.hash] *= gmean
            return scores
        scores: dict[bytes, float] = {}
        weights: dict[bytes, list[float]] = {}
        for node in graph._nodes.values():
            scores[node.hash] = random.random()
            weights[node.hash] = [0.0] * 2
            for node2 in graph._nodes.values():
                if node.hash != node2.hash:
                    if not infogain:
                        weights[node.hash][0] += graph._edges[node.hash + node2.hash].dist.P[0]
                        weights[node.hash][1] += graph._edges[node2.hash + node.hash].dist.P[0]
                    else:
                        weights[node.hash][0] += graph._edges[node.hash + node2.hash].dist.H
                        weights[node.hash][1] += graph._edges[node2.hash + node.hash].dist.H
        for i in range(iters):
            scores = btiter(scores, weights)
        scored = [(scores[h], h) for h in scores.keys()]
        scored.sort(key=lambda x: x[0])
        order = [h for s, h in scored]
        return order

    def predict(self, mlist: IModList) -> tuple[float, float, float, float]:
        self.resolve(mlist)
        activemods = list(filter(lambda h: self._mmap[h].state, self._mmap.keys()))
        activemods.sort(key=lambda h: self._mmap[h].index)

        est_lo = 1.0
        ent_lo = 0.0
        for i in range(len(activemods) - 1):
            print(self._mmap[activemods[i]].name + ' ' + self._mmap[activemods[i + 1]].name)
            print(self._lgraph._edges[activemods[i] + activemods[i + 1]].dist.P[0])
            est_lo *= self._lgraph._edges[activemods[i] + activemods[i + 1]].dist.P[0]
            ent_lo += self._lgraph._edges[activemods[i] + activemods[i + 1]].dist.H
        est_lo = 1 - est_lo
        ent_lo = -ent_lo / (len(activemods) - 1)

        est_hi = 1.0
        ent_hi = 0.0
        for ind, h in enumerate(activemods):
            for ind2, h2 in enumerate(activemods):
                if ind == ind2:
                    continue
                if h == h2:
                    continue
                if ind < ind2:
                    est_hi *= self._hgraph._edges[h + h2].dist.P[0]
                    ent_hi += self._hgraph._edges[h + h2].dist.H
                else:
                    est_hi *= self._hgraph._edges[h2 + h].dist.P[0]
                    ent_hi += self._hgraph._edges[h2 + h].dist.H
        est_hi = 1 - est_hi
        ent_hi = -ent_hi / (len(activemods) * (len(activemods) - 1))

        if est_lo < est_hi:
            return (est_lo, ent_lo, est_hi, ent_hi)
        else:
            return (est_hi, ent_hi, est_lo, ent_lo)