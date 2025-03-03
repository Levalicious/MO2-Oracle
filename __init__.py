from mobase import IPlugin
from .base.oracle.oracle import Oracle
from .plugin.oracle import OraclePlugin
from .plugin.save import SavePlugin
from .plugin.load import LoadPlugin
from .plugin.predict import PredictPlugin
from .plugin.sample.best import OptimalSamplePlugin
from .plugin.sample.maxent import InfoGainSamplePlugin

def createPlugins() -> list[IPlugin]:
    oracle = Oracle()
    master = OraclePlugin(oracle)
    children: list[IPlugin] = [SavePlugin(oracle, master), 
                               LoadPlugin(oracle, master),
                               PredictPlugin(oracle, master),
                               OptimalSamplePlugin(oracle, master),
                               InfoGainSamplePlugin(oracle, master)]
    return [master] + children
