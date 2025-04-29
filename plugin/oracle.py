from mobase import IPluginTool, IOrganizer, IModList, IPluginList, VersionInfo, PluginSetting, IModInterface # pyright: ignore [reportMissingModuleSource]
from PyQt6.QtCore import QDir
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox, QMainWindow

import os

from plugin_oracle.base.window import OracleWidget
from plugin_oracle.util.log import PluginLogger, getLogger
from plugin_oracle.base.oracle.oracle import Oracle

class OraclePlugin(IPluginTool):
    _organizer: IOrganizer
    _modlist: IModList
    _pluginlist: IPluginList
    _version: VersionInfo = VersionInfo(0, 0, 0)

    def __init__(self) -> None:
        self._log: PluginLogger = PluginLogger(getLogger(__name__), {'name': self.name()})
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
        self.oracle: Oracle = Oracle(organizer.getPluginDataPath() + '/' + self.name())        
        self._wdgt: OracleWidget | None = None
        res = self._organizer.onUserInterfaceInitialized(self.onInit)
        res |= self._organizer.onAboutToRun(self.onRun)
        res |= self._organizer.onFinishedRun(self.onExit)
        res |= self._modlist.onModInstalled(self.onInstall)
        if not res:
            self._log.error('Failed to register plugin handlers!')
            return False
        
        return self.checkversion()
    
    def name(self) -> str:
        return 'Oracle'
    
    def displayName(self) -> str:
        return self.name()
    
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
        return bool(self._organizer.pluginSetting(self.name(), 'enabled'))
    
    def tooltip(self) -> str:
        return 'Consumes crash reports for greater evil'
    
    def icon(self) -> QIcon:
        return QIcon()
    
    def display(self) -> None:
        self.oracle.resolve(self._modlist, self._organizer, False)
        if self._wdgt is not None:
            _ = self._wdgt.close()
            del self._wdgt
        self._wdgt = OracleWidget(self.oracle, [self.sample], self.predict, self.permutation)
        self._wdgt.show()

    def onInit(self, _: QMainWindow) -> None:
        self.oracle.load()
        self.oracle.resolve(self._modlist, self._organizer)

    def onRun(self, _: str, _1: QDir, _2: str) -> bool:
        self.oracle.resolve(self._modlist, self._organizer, False)
        return True

    def onExit(self, game: str, code: int) -> None:
        game = os.path.basename(game)
        if game.endswith('.exe'):
            game = game[:-4]
        whitelist: list[str] = ['skse64_loader']
        self._log.info(f'{game} : {code}')
        if game in whitelist:
            res = code == 0
            if res:
                reply = QMessageBox.question(None,'CrashStatus',
                    'Please confirm that this load order works:',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes)

                if reply == QMessageBox.StandardButton.No:
                    res = False
            self.oracle.observe(res, self._modlist, self._organizer)
            self.oracle.save()
        
    def onInstall(self, mod: IModInterface) -> None:
        _ = self.oracle.addMod(mod, self._organizer)
    
    def sample(self, random: bool = False) -> None:
        if random:
            self.oracle.samplerandom(self._modlist, self._pluginlist, self._organizer)
        else:
            self.oracle.sample(self._modlist, self._pluginlist, self._organizer)
    
    def predict(self) -> str:
        return self.oracle.predict(self._modlist, self._organizer)
    
    def permutation(self) -> list[bytes]:
        return self.oracle.permutation(self._modlist, self._organizer)