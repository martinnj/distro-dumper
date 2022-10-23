""" Debian module for Distro Dumper. """

# System imports.
import os
import re

from dataclasses import dataclass
from dataclasses import field
from logging import LoggerAdapter
from typing import Any
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

# Known architechtures from Debian.
__AVAILABLE_ARCHS = {
    "amd64",
    "arm64",
    "armel",
    "armhf",
    "i386",
    "mips64el",
    "mipsel",
    "ppc64el",
    "s390x",
}

# Environment-variable to validator mapping. (Required variables)
__REQUIRED_VALIDATORS: dict[str, Callable] = {
    "DEBIAN_ARCHS": lambda val: __is_arch_csv(val),
    "DEBIAN_MEDIA": lambda val: __is_media_csv(val),
}

# Environment-variable to validator mapping. (Optional variables)
__OPTIONAL_VALIDATORS: dict[str, Callable] = {
    "DEBIAN_EXTRA_FLAVORS": lambda val: isinstance(val, str) and val in {"edu", "mac"},
}

# Format string for generating download URLs.
_TORRENT_URL_FORMAT = "https://cdimage.debian.org/debian-cd/current/{arch}/bt-{media}/{filename}"

# Logger to handle console out.
_LOGGER: LoggerAdapter = get_logger("DEBIAN_MODULE")


####################################################################################################
###                                                                                              ###
###                                        Helper Methods                                        ###
###                                                                                              ###
####################################################################################################


def __is_arch_csv(val: Any) -> bool:
    """
    Checks if a value is a string containing a comma separated list fo valid Debian architechture
    names.
    Must contain at least one element.

    ### Arguments
    - val : Any
      Any object to check.

    ### Returns:
    - bool: True if the value is a string containing a comma separated list of valid Debian
            architechture names, with at least one element.
    """
    if not isinstance(val, str):
        return False

    formats = [format.strip() for format in val.split(",")]
    return len(formats) > 0 and all([_format in __AVAILABLE_ARCHS for _format in formats])


def __is_media_csv(val: Any) -> bool:
    """
    Checks if a value is a string containing a comma separated list fo valid Debian media types.
    Must contain at least one element.

    ### Arguments
    - val : Any
      Any object to check.

    ### Returns:
    - bool: True if the value is a string containing a comma separated list of valid Debian
            media types, with at least one element.
    """
    if not isinstance(val, str):
        return False

    formats = [format.strip() for format in val.split(",")]
    return len(formats) > 0 and all([_format in {"cd", "dvd"} for _format in formats])

####################################################################################################
###                                                                                              ###
###                                        Module Classes                                        ###
###                                                                                              ###
####################################################################################################

@dataclass
class DebianConfiguration(BaseModuleConfiguration):
    """
    Module specific configuration object for the Debian module.
    """
    requested_archs: list[str]
    requested_media: list[str]
    extra_flavors: list[str] = field(default_factory=lambda: list())


class DebianWorker(BaseWorker):
    """
    Debian implementation of the Base Worker.
    """

    config: DebianConfiguration

    def __init__(self, config: DebianConfiguration):
        self.config = config


    def dump(self) -> dict[str,str]:
        """
        Debian dump worker.

        ### Returns:
        - dict[str,str]: A dictionary with keyed by filenames, and valued with URLs for the
                         torrent-files.
        """

        candidates = dict()
        for arch in self.config.requested_archs:
            for media in self.config.requested_media:

                # Construct the index url based on arch and media.
                index_url = f"https://cdimage.debian.org/debian-cd/current/{arch}/bt-{media}/"
                _LOGGER.debug(f"Fetching index: {index_url}")
                try:
                    # Attempt to get the index, if we can't log and propegate.
                    resp = requests.get(index_url, allow_redirects=True)
                    resp.raise_for_status()
                except Exception as exc:
                    error_message = f"Unable to get index from \"{index_url}\": {repr(exc)}"
                    _LOGGER.error(error_message, exc_info=exc)
                    raise ModuleExternalError(
                        f"Debian module couldn't fetch the {arch}-{media} index"
                    )
                
                # Parse the index page to find our torrent links.
                _LOGGER.debug("Parsing HTML from index page.")
                soup = BeautifulSoup(resp.text, "html.parser")

                # Extract all the links from the HTML.
                links = []
                for link in soup.find_all('a'):
                    links.append(link.get('href'))
                _LOGGER.debug(f"Extracted {len(links)} links from the {arch}-{media} index.")
        
                # Filter so we only kep release links.
                _candidates = self._get_download_links(arch, media, links)
                _LOGGER.debug(f"Filtered to {len(_candidates)} candidates from the release page.")

                # Add to the distro wide results.
                candidates.update(_candidates)

        _LOGGER.debug(f"Returning {len(candidates)} candidates.")
        return candidates


    def _get_download_links(self, arch: str, media: str, links: list[str]) -> dict[str, str]:
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
        regex = re.compile(r"^debian-([a-zA-Z]*)-*(\d+)\.(\d+)\.(\d+)-(\w*)-.*\.torrent?")
        result = dict()
        for link in links:

            # Search each link using the regex.
            match = regex.search(link)
            if not match:
                continue

            # Extract match groups, we don't use them all, but sscchhh.
            flavor, major, minor, patch, arch = match.groups()

            # If we haven't requested this particular flavor, skip.
            if isinstance(flavor, str) \
               and len(flavor) > 0 \
               and flavor not in self.config.extra_flavors:
                continue

            # Assemble a URL for the file.
            url = _TORRENT_URL_FORMAT.format(arch=arch, media=media, filename=link)
            result[link] = url

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

    # Check required configuration values first.
    for var_name, validator in __REQUIRED_VALIDATORS.items():
        if var_name not in env:
            _LOGGER.error(f"Required environment variable {var_name} was not configured.")
            valid = False
        elif not validator(env[var_name]):
            _LOGGER.error(
                f"Required environment variable {var_name} had an invalid value: {env[var_name]}"
            )
            valid = False

    # Check optional configuration values only if they are present.
    for var_name, validator in __OPTIONAL_VALIDATORS.items():
        if var_name in env and not validator(env[var_name]):
            _LOGGER.error(
                f"Optional environment variable {var_name} had an invalid value: {env[var_name]}"
            )
            valid = False

    # Return validity
    return valid


def generate_from_environment() -> DebianConfiguration:
    """
    Generate a module configuration from the environment variables.

    ### Returns:
    - DebianConfiguration: The generated configuration.
    """
    requested_archs = [arch.strip() for arch in os.environ["DEBIAN_ARCHS"].split(",")]
    requested_media = [media.strip() for media in os.environ["DEBIAN_MEDIA"].split(",")]

    # Assemple the configuration object.
    conf = DebianConfiguration(
        requested_archs=requested_archs,
        requested_media=requested_media
    )

    # Add any optional configuration keys that are present.
    if "DEBIAN_EXTRA_FLAVORS" in os.environ:
        raw_val = os.environ["DEBIAN_EXTRA_FLAVORS"]
        conf.extra_flavors = [flavor.strip() for flavor in raw_val.split(",")]
        _LOGGER.debug(f"Setting \"extra_flavors\" = {conf.extra_flavors}")

    return conf


def create_worker(config: DebianConfiguration) -> DebianWorker:
    """
    Creates an Debian worker from a suitable configuration dataclass.

    ### Arguments
    - config : DebianConfiguration
      Configuration to give the worker.

    ### Returns:
    - DebianWorker: A fully configured, and thus, functional worker.
    """
    return DebianWorker(config)
