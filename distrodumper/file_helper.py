""" Module containing useful(?) file related things. """

# System imports.
import os
import shutil

from logging import LoggerAdapter

# 3rd-party imports.
import cloudscraper

# Custom imports.
from distrodumper import Configuration
from distrodumper.logging import get_logger


####################################################################################################
###                                                                                              ###
###                                 Constants & Global Variables                                 ###
###                                                                                              ###
####################################################################################################


# Logger to handle console out.
_LOGGER: LoggerAdapter = get_logger("FILE_HELPER")


####################################################################################################
###                                                                                              ###
###                                         Data Classes                                         ###
###                                                                                              ###
####################################################################################################


def get_files_in_cache(config: Configuration) -> set[str]:
    """
    Get all the files currently stored in the cache directory.

    ### Arguments
    - config : Configuration
      Basic program configuration to get the cache directory from.

    ### Returns:
    - set[str]: A set of filenames stores in the cache.
    """

    # Get the absolute cache path for good measure.
    cache_path = os.path.abspath(config.cache_dir)

    # set-comprehension that lists the cache-directory contents and checks if they're a file.
    return {
        filename
        for filename
        in os.listdir(cache_path)
        if os.path.isfile(os.path.join(cache_path, filename))
    }


def download(config: Configuration, filename: str, url: str) -> bool:
    """
    Download a file from a specified url to a specified filename.
    The directory the file will be placed in is pulled from the supplied Configuration object.

    ### Arguments
    - config : Configuration
      An initialized configuration object that can supply the cache- and dump-directories to use.
    - filename : str
      The name of the file to download the data into.
    - url : str
      The url to fetch the file data from.

    ### Returns:
    - bool: `True` if the download succedded, `False` otherwise.
    """

    # Calculate the target paths.
    cache_filepath = os.path.join(os.path.abspath(config.cache_dir), filename)
    dump_filepath = os.path.join(os.path.abspath(config.dump_dir), filename)
    _LOGGER.debug(f"Downloading \"{url}\" to:\n- {cache_filepath}\n- {dump_filepath}")

    try:
        # Open a file handle and download the file to cache.
        with open(cache_filepath, "wb") as f_obj:
            # Send the request for the file and raise an exception if we don't get HTTP 200.
            scraper = cloudscraper.create_scraper()
            resp = scraper.get(url, allow_redirects=True, timeout=(15,15))
            resp.raise_for_status()

            # Write the response contents to the file.
            _LOGGER.debug(f"File-length: {len(resp.content)}")
            f_obj.write(resp.content)

    # We actually want to catch everything so we can clean up neatly.
    # pylint: disable=broad-exception-caught
    except Exception as exc:
        _LOGGER.error(f"An error occured when downloading {url}: {repr(exc)}", exc_info=exc)
        # Remove the cache file so we can retry neatly later.
        if os.path.exists(cache_filepath):
            os.remove(cache_filepath)
        return False

    try:
        # Attempt to copy the cached file to dump.
        shutil.copy(cache_filepath, dump_filepath)

    # Same as above, we want to catch everything.
    # pylint: disable=broad-exception-caught
    except Exception as exc:
        _LOGGER.error(f"An error occured when copying {cache_filepath}: {repr(exc)}", exc_info=exc)
        # Remove the files so we can retry neatly later.
        if os.path.exists(cache_filepath):
            os.remove(cache_filepath)
        if os.path.exists(dump_filepath):
            os.remove(dump_filepath)
        return False

    # Wohooo, done.
    return True
