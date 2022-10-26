""" Example module for Distro Dumper. """

# System imports.
from dataclasses import dataclass
from logging import LoggerAdapter

# 3rd-party imports.

# Custom imports.
from distrodumper import BaseHelper
from distrodumper import BaseModuleConfiguration
from distrodumper import BaseWorker
from distrodumper.logging import get_logger


####################################################################################################
###                                                                                              ###
###                                 Constants & Global Variables                                 ###
###                                                                                              ###
####################################################################################################


# Logger to handle console out.
_LOGGER: LoggerAdapter = get_logger("EXAMPLE_MODULE")


####################################################################################################
###                                                                                              ###
###                                        Module Classes                                        ###
###                                                                                              ###
####################################################################################################





@dataclass
class ExampleConfiguration(BaseModuleConfiguration):
    """
    Module specific configuration object for the Example module.
    """


class ExampleWorker(BaseWorker):
    """
    Example implementation of the Base Worker.
    """

    config: ExampleConfiguration

    def __init__(self, config: ExampleConfiguration):
        self.config = config


    def dump(self) -> dict[str,str]:
        """
        Example dump worker.

        ### Returns:
        - dict[str,str]: A dictionary with keyed by filenames, and valued with URLs for the
                         torrent-files.
        """

        _LOGGER.debug("Example worker always returns 0 candidates.")
        return dict()


class ExampleHelper(BaseHelper):
    """ Example module helper class. """
    

    @staticmethod
    def verify_config() -> bool:
        """
        Verifies that the environment has been configured correctly.
        A correct configuration requires:
        - All required environment variables are present.
        - All required environment variables hold sensible values. 
        - Optional environment variables that have been provided contain sensible values.

        ### Returns:
        - bool: True of the environment holds a valid configuration, False otherwise.
        """
        
        return True


    @staticmethod
    def generate_from_environment() -> ExampleConfiguration:
        """
        Generate a module configuration from the environment variables.

        ### Returns:
        - ExampleConfiguration: The generated configuration.
        """
        return ExampleConfiguration()


    @staticmethod
    def create_worker(config: ExampleConfiguration) -> ExampleWorker:
        """
        Creates an Example worker from a suitable configuration dataclass.

        ### Arguments
        - config : ExampleConfiguration
        Configuration to give the worker.

        ### Returns:
        - ExampleWorker: A fully configured, and thus, functional worker.
        """
        return ExampleWorker(config)
