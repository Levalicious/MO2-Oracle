from mobase import GamePlugins, IOrganizer, IModList, IPluginList, IModInterface, ModState, PluginState
import re

class Plugin:
    def __init__(self, priority, name) -> None:
        self.priority = priority
        self.name = name

        # add exceptions here:
        self.dict: dict[str, list[str]] = {
            # 'mod1 regex': ['1st plugin substr', 'substr in 2nd', 'etc.'] ,
            # 'mod2 regex': ['substr in 1st', 'substr in 2nd', 'etc.']
        }

    def __lt__(self, other) -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority

        lc_a = self.name.lower()
        lc_b = other.name.lower()
        for (k, arr) in self.dict.items():
            if re.search(k, lc_a):
                for n in arr:
                    if n in lc_a:
                        return True
                    if n in lc_b:
                        return False

        # within a plugin there can be several esps. something that fixes stuff
        # should come last. if not enough use self.dict for the exceptions

        patts = \
            ['(:?hot|bug)[ ._-]?fix',
                r'\bfix\b',
                'patch',
                'add[ ._-]?on',
                'expansion',
                'expanded',
                'extension',
                'ext',
                'ng',
                'conversion'
                'fix'
                'remastered']
        for pattern in patts:
            if re.search(pattern, lc_a) != re.search(pattern, lc_b):
                return re.search(pattern, lc_a) is None

        # generally shorter should come first
        return len(lc_a) < len(lc_b) or self.name < other.name
    
def pluginsync(organizer: IOrganizer, mlist: IModList, plist: IPluginList) -> None:
    all_plugins: list[str] = list(plist.pluginNames())
    all_plugins = sorted(
        all_plugins,
        key=lambda x: Plugin(mlist.priority(plist.origin(x)), x)
    )

    masters: list[str] = []
    plugins: list[str] = []
    
    for plugin in all_plugins:
        if plist.isMasterFlagged(plugin):
            masters.append(plugin)
        else:
            plugins.append(plugin)
    
    all_plugins = masters + plugins
    all_lowered = [x.lower() for x in all_plugins]

    plist.setLoadOrder(all_plugins)
    for plugin in all_plugins:
        plugin_masters = plist.masters(plugin)
        canEnable = True
        for master in plugin_masters:
            if master.lower() not in all_lowered:
                canEnable = False
                break
        if canEnable:
            plist.setState(plugin, PluginState.ACTIVE)
        else:
            plist.setState(plugin, PluginState.INACTIVE)
    organizer.gameFeatures().gameFeature(GamePlugins).writePluginLists(plist) # type: ignore
    organizer.refresh()


