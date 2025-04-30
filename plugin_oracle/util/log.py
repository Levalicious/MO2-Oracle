import logging
from collections.abc import MutableMapping
from typing import Any

getLogger = logging.getLogger

class PluginLogger(logging.LoggerAdapter):                                                                  # pyright: ignore [reportMissingTypeArgument]
    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, MutableMapping[str, Any]]:  # pyright: ignore [reportExplicitAny]
        return f'[{self.extra["name"]}] {msg}', kwargs                                                      # pyright: ignore [reportOptionalSubscript]