from mobase import IPluginTool, IOrganizer, IModList, IPluginList, VersionInfo, PluginSetting, IModInterface
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox, QMainWindow, QInputDialog
from PyQt6.QtCore import QDir
from ..util.mod.minfo import OMod
from ..base.oracle.oracle import Oracle
from ..util.log import PluginLogger, getLogger
import os

class OraclePlugin(IPluginTool):
    _organizer: IOrganizer
    _modlist: IModList
    _pluginlist: IPluginList
    _version: VersionInfo = VersionInfo(0, 0, 0)

    def __init__(self, oracle: Oracle) -> None:
        self._log = PluginLogger(getLogger(__name__), {'name': self.name()})
        self._oracle = oracle
        super().__init__()

    def checkversion(self, silent: bool = False) -> bool:
        minversion: VersionInfo = VersionInfo(2, 5, 2)
        maxversion: VersionInfo = VersionInfo(2, 5, 2)
        exceptions: list[VersionInfo] = []
        self._log.info(self._organizer.getPluginDataPath() + '/' + self.name())

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
        self._oracle.path = organizer.getPluginDataPath() + '/' + self.name()
        
        self._organizer.onUserInterfaceInitialized(self.onInit)
        self._organizer.onAboutToRun(self.onRun)
        self._organizer.onFinishedRun(self.onExit)
        self._modlist.onModInstalled(self.onInstall)
        
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
        mods = self._modlist.allModsByProfilePriority()
        omods = self._oracle._mmap.values()
        prefix, ok = QInputDialog.getText(None, 'Prefix Prompt', 'Enter prefix:')
        if not ok or not prefix:
            QMessageBox.information(None, 'Oracle', 'Operation canceled or no prefix provided.', QMessageBox.StandardButton.Ok)
            return
        testmod = next((m for m in omods if m.name.lower().startswith(prefix.lower())), None)
        if not testmod:
            QMessageBox.information(
                None,
                'Oracle',
                'No mod found',
                QMessageBox.StandardButton.Ok
            )
            return
        QMessageBox.information(
            None,
            'Oracle',
            testmod.name + ':' + testmod.hash.hex(),
            QMessageBox.StandardButton.Ok
        )

    def onInit(self, window: QMainWindow) -> None:
        self._oracle.load()
        self._oracle.resolve(self._modlist)
    
    def onRun(self, path: str, dir: QDir, args: str) -> bool:
        self._oracle.resolve(self._modlist)
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
                reply = QMessageBox.question(
                    None,  # parent widget
                    'CrashStatus',  # dialog title
                    'Please confirm that this load order works:',  # dialog message
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,  # buttons to show
                    QMessageBox.StandardButton.Yes  # default button
                )

                if reply == QMessageBox.StandardButton.No:
                    res = False
            self._oracle.observe(self._modlist, res)

    def onInstall(self, mod: IModInterface) -> None:
        self._oracle.add_mod(mod, self._modlist)