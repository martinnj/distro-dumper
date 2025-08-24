""" CachyOS module for Distro Dumper. """

# System imports.
import os
import re

from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse

# 3rd-party imports.
import requests
from bs4 import BeautifulSoup

# Custom imports.
from distrodumper import BaseHelper, BaseWorker
from distrodumper import BaseModuleConfiguration
from distrodumper.logging import get_logger
from distrodumper.validation import is_atomic_csv


####################################################################################################
###                                                                                              ###
###                                 Constants & Global Variables                                 ###
###                                                                                              ###
####################################################################################################


# Known editions from CachyOS. Keep small and conservative until more are verified.
_AVAILABLE_EDITIONS = {
    "desktop",
    "handheld",
}


# Environment-variable to validator mapping. (Required variables)
_REQUIRED_VALIDATORS: dict[str, Callable] = {
    "CACHYOS_EDITIONS": lambda val: is_atomic_csv(val, _AVAILABLE_EDITIONS),
}

# Environment-variable to validator mapping. (Optional variables)
_OPTIONAL_VALIDATORS: dict[str, Callable] = {
}

# Logger to handle console out.
_LOGGER = get_logger("CACHYOS_MODULE")


####################################################################################################
###                                                                                              ###
###                                        Module Classes                                        ###
###                                                                                              ###
####################################################################################################


@dataclass
class CachyOsConfiguration(BaseModuleConfiguration):
    """
    Module specific configuration object for the CachyOS module.
    """
    requested_editions: list[str]


class CachyOsWorker(BaseWorker):
    """
    CachyOS implementation of the Base Worker.
    """

    def __init__(self, config: CachyOsConfiguration):
        self.config = config


    def dump(self) -> dict[str,str]:
        """
        CachyOS dump worker.

        The CachyOS website provides links on the downloads page and blog posts. We will
        parse the main downloads page and collect direct .torrent links from official
        domains only.

        ### Returns:
        - dict[str,str]: A dictionary with keys as filenames, values as absolute URLs.
        """

        # Simpler approach: parse only the downloads page and extract absolute .torrent links.
        index_url = "https://cachyos.org/download/"
        _LOGGER.debug(f"Fetching downloads page: {index_url}")
        try:
            resp = requests.get(index_url, allow_redirects=True, timeout=(15, 15))
            resp.raise_for_status()
        except Exception as exc:
            _LOGGER.error(f"Unable to fetch CachyOS downloads page: {repr(exc)}", exc_info=exc)
            return {}

        # Quick probe for torrent/magnet presence in raw HTML
        lower_html = resp.text.lower()
        dot_torrent_hits = lower_html.count('.torrent')
        magnet_hits = lower_html.count('magnet:?xt=urn:btih:')
        _LOGGER.debug(f"Raw HTML contains '.torrent' {dot_torrent_hits} time(s), magnet links {magnet_hits} time(s).")

        soup = BeautifulSoup(resp.text, "html.parser")
        results: dict[str, str] = {}

        anchors = soup.find_all("a", href=True)
        _LOGGER.debug(f"Downloads page anchor count: {len(anchors)}")
        sample_hrefs = [a.get("href", "") for a in anchors[:20]]
        if sample_hrefs:
            _LOGGER.debug("Sample hrefs:" + "\n" + "\n".join([f"- {h}" for h in sample_hrefs]))

        requested = {e.lower() for e in self.config.requested_editions}

        # Collect torrents from anchors
        found_urls: set[str] = set()
        for a_tag in anchors:
            href = a_tag.get("href", "")
            if not isinstance(href, str) or len(href) == 0:
                continue

            absolute_url = urljoin(index_url, href)
            # If the anchor accidentally contains extra JSON/HTML after the torrent URL,
            # trim it hard at the first occurrence of ".torrent".
            lower_abs = absolute_url.lower()
            if ".torrent" in lower_abs:
                cut = lower_abs.find(".torrent") + len(".torrent")
                absolute_url = absolute_url[:cut]
            parsed = urlparse(absolute_url)
            # Only http(s) .torrent links
            if parsed.scheme not in {"http", "https"}:
                continue
            if not parsed.path.lower().endswith(".torrent"):
                continue
            # Skip if the URL still appears polluted with JSON meta
            if any(ch in absolute_url for ch in ['"', "'", '[', ']', '{', '}', ' '] ):
                _LOGGER.debug(f"Skipping polluted anchor URL: {absolute_url}")
                continue
            found_urls.add(absolute_url)

        # Also scan raw HTML for http(s) .torrent links that might be in inline JSON
        html_text = resp.text
        for match in re.findall(r"https?://[^\s\"'>]+?\.torrent", html_text, flags=re.IGNORECASE):
            # Defensive trim
            lower_m = match.lower()
            cut = lower_m.find(".torrent") + len(".torrent")
            cleaned = match[:cut]
            if any(ch in cleaned for ch in ['"', "'", '[', ']', '{', '}', ' '] ):
                _LOGGER.debug(f"Skipping polluted inline URL: {cleaned}")
                continue
            found_urls.add(cleaned)

        # Build results filtered by requested editions using filename/URL label
        all_candidates_count = len(found_urls)
        for link in sorted(found_urls):
            parsed = urlparse(link)
            filename = os.path.basename(parsed.path)
            if not filename.lower().endswith('.torrent'):
                _LOGGER.debug(f"Discarding non-torrent after collection: {link}")
                continue
            label = f"{link} {filename}".lower()
            if requested and not any(edition in label for edition in requested):
                continue
            results[filename] = link

        _LOGGER.debug(f"Found {all_candidates_count} .torrent link(s) total, returning {len(results)} filtered candidate(s).")

        # Log a small sample to aid debugging
        sample = list(results.items())[:5]
        if len(sample) > 0:
            _LOGGER.debug("Sample torrent candidates:" + "\n" + "\n".join([f"- {k} -> {v}" for k, v in sample]))

        _LOGGER.debug(f"Returning {len(results)} candidates.")
        return results


class CachyOsHelper(BaseHelper):
    """ CachyOS module helper class. """

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
    def generate_from_environment() -> CachyOsConfiguration:
        """
        Generate a module configuration from the environment variables.

        ### Returns:
        - CachyOsConfiguration: The generated configuration.
        """
        requested_editions = [value.strip() for value in os.environ["CACHYOS_EDITIONS"].split(",")]

        conf = CachyOsConfiguration(
            requested_editions=requested_editions,
        )

        return conf


    @staticmethod
    def create_worker(config: BaseModuleConfiguration) -> CachyOsWorker:
        """
        Creates a CachyOS worker from a suitable configuration dataclass.

        ### Arguments
        - config : CachyOsConfiguration
        Configuration to give the worker.

        ### Returns:
        - CachyOsWorker: A fully configured, and thus, functional worker.
        """
        return CachyOsWorker(config)  # type: ignore[arg-type]


