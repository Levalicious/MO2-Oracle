from mobase import IPlugin # pyright: ignore [reportMissingModuleSource]
from plugin_oracle.plugin.oracle import OraclePlugin

def createPlugins() -> list[IPlugin]:
    master = OraclePlugin()
    children: list[IPlugin] = []
    return [master] + children
