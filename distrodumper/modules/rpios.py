""" Raspberry Pi OS module for Distro Dumper. """

# System imports.
import os
import re

from dataclasses import dataclass
from dataclasses import field
from logging import LoggerAdapter
from urllib.parse import urlparse
from typing import Any
from typing import Callable

# 3rd-party imports.
import cloudscraper
from bs4 import BeautifulSoup

# Custom imports.
from distrodumper import BaseHelper, BaseWorker
from distrodumper import BaseModuleConfiguration
from distrodumper import ModuleExternalError
from distrodumper.logging import get_logger
from distrodumper.validation import is_atomic_csv


####################################################################################################
###                                                                                              ###
###                                 Constants & Global Variables                                 ###
###                                                                                              ###
####################################################################################################

# Known flavors.
_AVAILABLE_IMAGES = {
    "raspios_armhf",
    "raspios_full_armhf",
    "raspios_lite_armhf",
    "raspios_arm64",
    "raspios_lite_arm64",
    "rpd_x86"
}


# Environment-variable to validator mapping. (Required variables)
_REQUIRED_VALIDATORS: dict[str, Callable] = {
    "RPIOS_IMAGES": lambda val: is_atomic_csv(val, _AVAILABLE_IMAGES),
}

# Environment-variable to validator mapping. (Optional variables)
_OPTIONAL_VALIDATORS: dict[str, Callable] = {
}

# Logger to handle console out.
_LOGGER: LoggerAdapter = get_logger("RPI_OS_MODULE")


####################################################################################################
###                                                                                              ###
###                                        Module Classes                                        ###
###                                                                                              ###
####################################################################################################

@dataclass
class RPiOsConfiguration(BaseModuleConfiguration):
    """
    Module specific configuration object for the Raspberri Pi OS module.
    """
    requested_images: list[str]


class RPiOsWorker(BaseWorker):
    """
    Raspberry Pi OS implementation of the Base Worker.
    """

    config: RPiOsConfiguration

    def __init__(self, config: RPiOsConfiguration):
        self.config = config


    def dump(self) -> dict[str,str]:
        """
        Raspberry Pi OS dump worker.

        ### Returns:
        - dict[str,str]: A dictionary with keyed by filenames, and valued with URLs for the
                         torrent-files.
        """

        candidates = dict()
        scraper = cloudscraper.create_scraper()

        # Construct the index url based on arch and media.
        index_url = f"https://www.raspberrypi.com/software/operating-systems/"
        _LOGGER.debug(f"Fetching index: {index_url}")

        try:
            # Attempt to get the index, if we can't log and propegate.
            resp = scraper.get(index_url, allow_redirects=True)
            resp.raise_for_status()
        except Exception as exc:
            error_message = f"Unable to get index from \"{index_url}\": {repr(exc)}"
            _LOGGER.error(error_message, exc_info=exc)
            raise ModuleExternalError(
                f"Raspberry Pi OS module couldn't fetch the index."
            )

        # Parse the index page to find our torrent links.
        _LOGGER.debug("Parsing HTML from index page.")
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract all the links from the HTML.
        links = []
        for link in soup.find_all("a"):
            links.append(link.get("href", ""))
        _LOGGER.debug(f"Extracted {len(links)} links from the Raspberry Pi OS index.")

        # Filter so we only keep release links.
        candidates = self._get_download_links(links)
        _LOGGER.debug(f"Returning {len(candidates)} candidates.")
        return candidates


    def _get_download_links(self, links: list[str]) -> dict[str, str]:
        """
        Filters a list of links from an index page and returns only the torrent links and
        suitable filenames.

        ### Arguments
        - links : list[str]
          The list of links found on the index page.

        ### Returns:
        - dict[str, str]: Keys are filanames, values are absolute URLs to the torrents.
        """

        result = dict()
        for link in [link for link in links if link.endswith(".torrent")]:
            for image in self.config.requested_images:
                if image in link:
                    # Extract filename and add to result.
                    parsed_url = urlparse(link)
                    filename = os.path.basename(parsed_url.path)
                    result[filename] = link

        return result


class RPiOsHelper(BaseHelper):
    """ Raspberry Pi OS module helper class. """

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

        # Initialize to true, we assume the best of everyone. <3
        valid = True
        env = os.environ

        # Check required configuration values first.
        for var_name, validator in _REQUIRED_VALIDATORS.items():
            if var_name not in env:
                _LOGGER.error(f"Required environment variable {var_name} was not configured.")
                valid = False
            elif not validator(env[var_name]):
                _LOGGER.error(
                    f"Required environment variable {var_name} had an invalid value: {env[var_name]}"
                )
                valid = False

        # Check optional configuration values only if they are present.
        for var_name, validator in _OPTIONAL_VALIDATORS.items():
            if var_name in env and not validator(env[var_name]):
                _LOGGER.error(
                    f"Optional environment variable {var_name} had an invalid value: {env[var_name]}"
                )
                valid = False

        # Return validity
        return valid


    @staticmethod
    def generate_from_environment() -> RPiOsConfiguration:
        """
        Generate a module configuration from the environment variables.

        ### Returns:
        - RPiOsConfiguration: The generated configuration.
        """
        requested_images = [image.strip() for image in os.environ["RPIOS_IMAGES"].split(",")]

        # Assemple the configuration object.
        conf = RPiOsConfiguration(
            requested_images=requested_images
        )

        return conf


    @staticmethod
    def create_worker(config: RPiOsConfiguration) -> RPiOsWorker:
        """
        Creates an Raspberry Pi OS worker from a suitable configuration dataclass.

        ### Arguments
        - config : RPiOsConfiguration
        Configuration to give the worker.

        ### Returns:
        - RPiOsWorker: A fully configured, and thus, functional worker.
        """
        return RPiOsWorker(config)
