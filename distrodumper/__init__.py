""" Main Package for distrodumper. """


# System imports.
from dataclasses import dataclass
from dataclasses import field
from types import ModuleType
from typing import Tuple


####################################################################################################
###                                                                                              ###
###                                         Data Classes                                         ###
###                                                                                              ###
####################################################################################################


@dataclass
class BaseModuleConfiguration:
    """
    Dummy dataclass that module configurations should inherit from.

    Really just here to make type checking easier. ;)
    """


@dataclass
class Configuration:
    """
    Dataclass holding a basic program configuration.
    """

    # Module related.
    requested_modules: list[str]
    modules: dict[str, Tuple[BaseModuleConfiguration, ModuleType]] = field(default_factory=lambda: dict())

    # Basic configuration.
    cache_dir: str = "/cache"
    debug: bool = False
    dump_dir: str = "/dump"
    interval: int = 3600


####################################################################################################
###                                                                                              ###
###                                      Exception Classes                                       ###
###                                                                                              ###
####################################################################################################


class ModuleExternalError(Exception):
    """
    Exception class indicating that a module ran into trouble with an external source.
    Might and might not warrant investigation.
    """


####################################################################################################
###                                                                                              ###
###                                      Module Base Class                                       ###
###                                                                                              ###
####################################################################################################

class BaseWorker:
    """
    Base worker class, specifying the interface expected.
    """

    config: BaseModuleConfiguration

    def __init__(self, config: BaseModuleConfiguration):
        self.config = config

    def dump(self) -> dict[str,str]:
        """
        Stub workers must implement to work correctly.

        ### Raises:
        - NotImplementedError: If the Worker hasn't implemented the method.

        ### Returns:
        - dict[str,str]: A dictionary with keyed by filenames, and valued with URLs for the
                         torrent-files.
        """
        raise NotImplementedError(f"`dump()` not implemented in {self.__class__.__name__}")


