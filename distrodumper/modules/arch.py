""" Arch Linux module for Distro Dumper. """

# System imports.
import os
import re

from dataclasses import dataclass
from logging import LoggerAdapter
from typing import Callable

# 3rd-party imports.
import requests
from bs4 import BeautifulSoup

# Custom imports.
from distrodumper import BaseWorker
from distrodumper import BaseModuleConfiguration
from distrodumper import ModuleExternalError
from distrodumper.logging import get_logger


####################################################################################################
###                                                                                              ###
###                                 Constants & Global Variables                                 ###
###                                                                                              ###
####################################################################################################


# Environment-variable to validator mapping. (Optional variables)
__OPTIONAL_VALIDATORS: dict[str, Callable] = {
    "ARCH_GET_ALL": lambda val: isinstance(val, str) and val in {"true", "false"},
    "ARCH_GET_AVAILABLE": lambda val: isinstance(val, str) and val in {"true", "false"},
}

# Release page url.
_PAGE_URL = "https://archlinux.org/releng/releases/"

# Formatting strings.
_TORRENT_FORMAT = "https://archlinux.org/releng/releases/{year}.{major}.{minor}/torrent/"
_FILENAME_FORMAT = "archlinux-{year}-{major}-{minor}-x86_64.torrent"

# Logger to handle console out.
_LOGGER: LoggerAdapter = get_logger("ARCH_MODULE")


####################################################################################################
###                                                                                              ###
###                                        Module Classes                                        ###
###                                                                                              ###
####################################################################################################

@dataclass
class ArchConfiguration(BaseModuleConfiguration):
    """
    Module specific configuration object for the Arch Linux module.
    """
    get_all: bool = False
    get_available: bool = False



class ArchWorker(BaseWorker):
    """
    Arch specific implementation of the Base Worker.
    """

    config: ArchConfiguration

    def __init__(self, config: ArchConfiguration):
        self.config = config


    def dump(self) -> dict[str,str]:
        """
        Arch Linux dump worker.

        ### Raises:
        ModuleExternalError - If an error occured when fetching the release page.

        ### Returns:
        - dict[str,str]: A dictionary with keyed by filenames, and valued with URLs for the
                         torrent-files.
        """

        # Get the Arch Linux release page.
        _LOGGER.debug(f"Requesting release page: {_PAGE_URL}")
        resp = requests.get(_PAGE_URL)
        if resp.status_code != 200:
            _LOGGER.error("Recieved a non 200 status code from archlinux.org")
            raise ModuleExternalError("Unable to get the release-page from Archlinux.org")
        _LOGGER.debug(f"Recieved release page with length: {len(resp.text)}")


        # Parse the HTML.
        _LOGGER.debug("Parsing HTML from release page.")
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract all the links from the HTML.
        links = []
        for link in soup.find_all('a'):
            links.append(link.get('href'))
        _LOGGER.debug(f"Extracted {len(links)} links from the release page.")

        # Filter so we only kep release links.
        candidates = self._get_download_links(links)
        _LOGGER.debug(f"Filtered to {len(candidates)} candidates from the release page.")

        # If the "all" setting is not set, remove all but the newest link.
        if not self.config.get_all:
            _LOGGER.debug("\"ARCH_GET_ALL\" not set - Filtering candidates to find newest.")
            # We can exploit the versioning including leading zeroes to just sort lexicographically.
            # Sort the filenames in reverse and just take the first one.
            keys = [key for key in candidates.keys()]
            keys.sort(reverse=True)
            highest_version = keys[0]

            # Return super smol dict.
            candidates = {highest_version: candidates[highest_version]}

        _LOGGER.debug(f"Returning {len(candidates)} candidates.")
        return candidates


    def _get_download_links(self, links: list[str]) -> dict[str, str]:
        """
        Filters a list of links from the release page and returns only the torrent links and
        suitable filenames.

        ### Arguments
        - links : list[str]
          The list of links found on the release page.

        ### Returns:
        - dict[str, str]: Keys are filanames, values are absolute URLs to the torrents.
        """
        # Compile regex that matches the ISO name from the magnet link, it's reasier to match
        # precisely than the download link.
        regex = re.compile(r"archlinux-(\d{4})\.(\d{2})\.(\d{2})-x86_64\.iso")
        result = dict()
        for link in links:

            # Search each link for our target regex.
            match = regex.search(link)
            if not match:
                continue

            # Extract version information from the capture groups.
            year, major, minor = match.groups()

            # Add the resulting URL and filename to the results.
            url = _TORRENT_FORMAT.format(year=year, major=major, minor=minor)
            filename = _FILENAME_FORMAT.format(year=year, major=major, minor=minor)
            result[filename] = url

        return result

####################################################################################################
###                                                                                              ###
###                                        Public Methods                                        ###
###                                                                                              ###
####################################################################################################


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
    
    # Initialize to true, we assume the best of everyone. <3
    valid = True
    env = os.environ

    # Check optional configuration values only if they are present.
    for var_name, validator in __OPTIONAL_VALIDATORS.items():
        if var_name in env and not validator(env[var_name]):
            _LOGGER.error(
                f"Optional environment variable {var_name} had an invalid value: {env[var_name]}"
            )
            valid = False

    # Return validity
    return valid


def generate_from_environment() -> ArchConfiguration:
    """
    Generate a module configuration from the environment variables.

    ### Returns:
    - ArchConfiguration: The generated configuration.
    """

    module_config = ArchConfiguration()

    # Get everything?
    if "ARCH_GET_ALL" in os.environ:
        raw_val = os.environ["ARCH_GET_ALL"]
        module_config.get_all = raw_val == "true"
        _LOGGER.debug(f"Setting \"get_all\" = {module_config.get_all}")

    # Get just those with webseeds?
    if "ARCH_GET_AVAILABLE" in os.environ:
        raw_val = os.environ["ARCH_GET_AVAILABLE"]
        module_config.get_available = raw_val == "true"
        _LOGGER.debug(f"Setting \"get_available\" = {module_config.get_all}")
        _LOGGER.warning("ARCH_GET_AVAILABLE is not implemented.")

    return module_config


def create_worker(config: ArchConfiguration) -> ArchWorker:
    """
    Creates an Arch Linux worker from a suitable configuration dataclass.

    ### Arguments
    - config : ArchConfiguration
      Configuration to give the worker.

    ### Returns:
    - ArchWorker: A fully configured, and thus, functional worker.
    """
    return ArchWorker(config)
