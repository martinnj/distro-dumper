""" Main Package for distrodumper. """


# System imports.
from dataclasses import dataclass
from dataclasses import field
from typing import Type
from typing import Tuple


####################################################################################################
###                                                                                              ###
###                                     Module Data Classes                                      ###
###                                                                                              ###
####################################################################################################


@dataclass
class BaseModuleConfiguration:
    """
    Dummy dataclass that module configurations should inherit from.

    Really just here to make type checking easier. ;)
    """


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


class BaseHelper:
    """
    Base helper class modules should implemenent to enforce a specific interface.
    """


    @staticmethod
    def verify_config() -> bool:
        """
        Stub module helpers must implement to work correctly.

        Verifies that the environment has been configured correctly.
        A correct configuration requires:
        - All required environment variables are present.
        - All required environment variables hold sensible values.
        - Optional environment variables that have been provided contain sensible values.

        ### Returns:
        - bool: True of the environment holds a valid configuration, False otherwise.
        """
        raise NotImplementedError("`verify_config` was not implemented.")


    @staticmethod
    def generate_from_environment() -> BaseModuleConfiguration:
        """
        Stub module helpers must implement to work correctly.

        Generate a module configuration from the environment variables.

        ### Returns:
        - BaseModuleConfiguration: The generated configuration.
        """
        raise NotImplementedError("`generate_from_environment` was not implemented.")


    @staticmethod
    def create_worker(config: BaseModuleConfiguration) -> BaseWorker:
        """
        Stub module helpers must implement to work correctly.

        Creates an worker from a suitable configuration dataclass.

        ### Arguments
        - config : BaseModuleConfiguration
        Configuration to give the worker.

        ### Returns:
        - BaseWorker: A fully configured, and thus, functional worker.
        """
        raise NotImplementedError("`create_worker` was not implemented.")


####################################################################################################
###                                                                                              ###
###                                     Program Data Classes                                     ###
###                                                                                              ###
####################################################################################################


@dataclass
class Configuration:
    """
    Dataclass holding a basic program configuration.
    """

    # Module related.
    requested_modules: list[str]
    modules: dict[str, Tuple[BaseModuleConfiguration, Type[BaseHelper]]] \
        = field(default_factory=lambda: dict())

    # Basic configuration.
    cache_dir: str = "/cache"
    debug: bool = False
    dump_dir: str = "/dump"
    interval: int = 3600
