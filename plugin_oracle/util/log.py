from logging import getLogger, LoggerAdapter

class PluginLogger(LoggerAdapter):
    def process(self, msg, kwargs):
        return f'[{self.extra["name"]}] {msg}', kwargs