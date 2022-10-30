""" Manjaro module for Distro Dumper. """

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
import requests
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

# Known flavors (desktop environments) from Manjaro/Community.
_AVAILABLE_FLAVORS = {
    "kde",
    "xfce",
    "gnome",
    "budgie",
    "cinnamon",
    "i3",
    "mate",
}

# TODO: Arm images are a bit wild looks like. Since they come in a DE+ARM-flavor combo.


# Environment-variable to validator mapping. (Required variables)
_REQUIRED_VALIDATORS: dict[str, Callable] = {
    "MANJARO_FLAVORS": lambda val: is_atomic_csv(val, _AVAILABLE_FLAVORS),
}

# Environment-variable to validator mapping. (Optional variables)
_OPTIONAL_VALIDATORS: dict[str, Callable] = {
}

# Logger to handle console out.
_LOGGER: LoggerAdapter = get_logger("MANJARO_MODULE")


####################################################################################################
###                                                                                              ###
###                                        Module Classes                                        ###
###                                                                                              ###
####################################################################################################

@dataclass
class ManjaroConfiguration(BaseModuleConfiguration):
    """
    Module specific configuration object for the Manjaro module.
    """
    requested_flavors: list[str]


class ManjaroWorker(BaseWorker):
    """
    Manjaro implementation of the Base Worker.
    """

    config: ManjaroConfiguration

    def __init__(self, config: ManjaroConfiguration):
        self.config = config


    def dump(self) -> dict[str,str]:
        """
        Manjaro dump worker.

        ### Returns:
        - dict[str,str]: A dictionary with keyed by filenames, and valued with URLs for the
                         torrent-files.
        """

        candidates = dict()

        # Construct the index url based on arch and media.
        index_url = f"https://manjaro.org/download/"
        _LOGGER.debug(f"Fetching index: {index_url}")

        try:
            # Attempt to get the index, if we can't log and propegate.
            resp = requests.get(index_url, allow_redirects=True)
            resp.raise_for_status()
        except Exception as exc:
            error_message = f"Unable to get index from \"{index_url}\": {repr(exc)}"
            _LOGGER.error(error_message, exc_info=exc)
            raise ModuleExternalError(
                f"Manjaro module couldn't fetch the Manjaro index."
            )

        # Parse the index page to find our torrent links.
        _LOGGER.debug("Parsing HTML from index page.")
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract all the links from the HTML.
        links = []
        for link in soup.find_all("a"):
            links.append(link.get("href", ""))
        _LOGGER.debug(f"Extracted {len(links)} links from the Manjaro index.")

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
        # Compile a regex that can match the torrent filenames and get any relevant information
        # from them.
        regex = re.compile(r"^https:\/\/download\.manjaro\.org\/([\w\d]+)\/(\d+)\.(\d+)\.(\d+)\/manjaro-([\w\d]+)-(\d+)\.(\d+)\.(\d+)-(\d+)-([\w\d]+).iso.torrent$")
        result = dict()
        for link in links:

            # Search each link using the regex.
            match = regex.search(link)
            if not match:
                continue

            # Extract match groups, we don't use them all, but sscchhh.
            flavor, major, minor, patch, flavor_2, major_2, minor_2, patch_2, date, linux = match.groups()

            if flavor != flavor_2 \
                or major != major_2 \
                or minor != minor_2 \
                or patch != patch_2:
                _LOGGER.warning(f"Got a match with mismatched flavor/versions: {link}")
                continue

            # If we haven't requested this particular flavor, skip.
            if isinstance(flavor, str) \
               and len(flavor) > 0 \
               and flavor not in self.config.requested_flavors:
                continue

            # Extract filename and add to result.
            parsed_url = urlparse(link)
            filename = os.path.basename(parsed_url.path)
            result[filename] = link

        return result


class ManjaroHelper(BaseHelper):
    """ Manjaro module helper class. """

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
    def generate_from_environment() -> ManjaroConfiguration:
        """
        Generate a module configuration from the environment variables.

        ### Returns:
        - ManjaroConfiguration: The generated configuration.
        """
        requested_flavors = [flavor.strip() for flavor in os.environ["MANJARO_FLAVORS"].split(",")]

        # Assemple the configuration object.
        conf = ManjaroConfiguration(
            requested_flavors=requested_flavors
        )

        return conf


    @staticmethod
    def create_worker(config: ManjaroConfiguration) -> ManjaroWorker:
        """
        Creates an Manjaro worker from a suitable configuration dataclass.

        ### Arguments
        - config : ManjaroConfiguration
        Configuration to give the worker.

        ### Returns:
        - ManjaroWorker: A fully configured, and thus, functional worker.
        """
        return ManjaroWorker(config)
