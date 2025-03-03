from logging import LoggerAdapter, getLogger
from mobase import IPluginTool, IOrganizer, IModList, IPluginList, VersionInfo, PluginSetting
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox
from ..util.mod.minfo import OMod
from ..base.oracle.oracle import Oracle
from .oracle import OraclePlugin
from ..util.log import PluginLogger, getLogger

class LoadPlugin(IPluginTool):
    _organizer: IOrganizer
    _modlist: IModList
    _pluginlist: IPluginList
    _version: VersionInfo = VersionInfo(0, 0, 0)

    def __init__(self, oracle: Oracle, master: OraclePlugin) -> None:
        self._master = master
        self._oracle = oracle
        self._log = PluginLogger(getLogger(__name__), {'name': self.name()})
        super().__init__()

    def checkversion(self, silent: bool = False) -> bool:
        minversion: VersionInfo = VersionInfo(2, 5, 2)
        maxversion: VersionInfo = VersionInfo(2, 5, 2)
        exceptions: list[VersionInfo] = []
        appVersion = self._organizer.appVersion()

        if appVersion < minversion:
            if not silent:
                self._log.error(f'This plugin requires MO2 version {minversion} or newer.')
            return False
        if appVersion in exceptions:
            if not silent:
                self._log.error(f'This plugin is not compatible with MO2 version {appVersion}.')
            return False
        if appVersion > maxversion:
            if not silent:
                self._log.warning(f'This plugin was not tested with MO2 version {appVersion}. You may experience issues.')
        else:
            if not silent:
                self._log.info(f'This plugin is compatible with MO2 version {appVersion}.')
        return True
    
    def init(self, organizer: IOrganizer) -> bool:
        self._organizer = organizer
        self._modlist = organizer.modList()
        self._pluginlist = organizer.pluginList()
        return self.checkversion(True)
    
    def name(self) -> str:
        return self._master.name() + ' Load Plugin'
    
    def master(self) -> str:
        return self._master.name()

    def displayName(self) -> str:
        return self._master.displayName() + '/Load'
    
    def author(self) -> str:
        return 'Levalicious'
    
    def description(self) -> str:
        return 'A crash lies in your future'
    
    def version(self) -> VersionInfo:
        return self._version
    
    def settings(self) -> list[PluginSetting]:
        return [
            PluginSetting('enabled', 'enable this plugin', True)
        ]
    
    def isActive(self) -> bool:
        return self._master.isActive() and bool(self._organizer.pluginSetting(self.name(), 'enabled'))
    
    def tooltip(self) -> str:
        return 'Consumes crash reports for greater evil'
    
    def icon(self) -> QIcon:
        return self._master.icon()
    
    def display(self) -> None:
        self._oracle.load()