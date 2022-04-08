#!/usr/bin/env python3
 
""" Simple worker script to routinely check and dump torrent files from Distrowatch.com """


# System imports.
import datetime
import os
import shutil
import sys

from time import sleep
from typing import Generator, Tuple

# 3rd party imports.
import cloudscraper
import feedparser

# Constants.
__VERSION__ = "###VERSION###"

# Globals.
__CACHE_DIR = ""
__DISTRO_PREFIXES = set()
__DUMP_DIR = ""
__DUMP_INTERVAL = 0
__FEED_URL = ""

# Terminal printing control stuff
__term_ok_blue = '\033[94m'
__term_ok_green = '\033[92m'
__term_warning = '\033[93m'
__term_fail = '\033[91m'
__term_endc = '\033[0m'
__term_bold = '\033[1m'
__term_underline = '\033[4m'

def pprint(message: str, text_class: str="info") -> None:
    """
    Prints a message to console, all prettylike.
    Class can be info, ok, warning or error, defaults to info.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d T %H:%M:%S")
    tag = "?"
    if text_class == "info":
        tag = __term_ok_blue + "INFO" + __term_endc
    elif text_class == "ok":
        tag = __term_ok_green + "SUCCESS" + __term_endc
    elif text_class == "warning":
        tag = __term_warning + "WARNING" + __term_endc
    elif text_class == "error":
        tag = __term_fail + "ERROR" + __term_endc

    print("[%s] [%s] %s" % (timestamp, tag, message.strip()), flush=True)


def __verify_environ() -> None:
    """ Verifies all the necesarry environment variables are set. """
    keys = [
        "CACHE_DIRECTORY",
        "DISTRO_PREFIXES",
        "DUMP_DIRECTORY",
        "DUMP_INTERVAL",
        "FEED_URL",
    ]
    for key in keys:
        assert key in os.environ, "The \"%s\" environment variable must be set." % key
        assert os.environ[key], "The \"%s\" environment variable must have a value." % key


def __set_globals() -> None:
    """
    Sets the globals from environment variables.
    I know globals are bad, but this is a dirty script. ;)
    """

    # The cache dir is where we download files.
    global __CACHE_DIR
    __CACHE_DIR = os.environ["CACHE_DIRECTORY"]

    # The distro prefixes are used to decide what to download from the feed.
    global __DISTRO_PREFIXES
    __DISTRO_PREFIXES = set(os.environ["DISTRO_PREFIXES"].lower().split(","))

    # The dump dir is where we copy files when downloaded.
    global __DUMP_DIR
    __DUMP_DIR = os.environ["DUMP_DIRECTORY"]

    # The dump dir is where we copy files when downloaded.
    global __DUMP_INTERVAL
    __DUMP_INTERVAL = int(os.environ["DUMP_INTERVAL"])

    # The URL of the RSS feed.
    global __FEED_URL
    __FEED_URL = os.environ["FEED_URL"]


def __get_feed_items() -> Generator[Tuple[str, str], None, None]:
    """
    Yields tuples with (filename, url) from the feed.
    """
    
    feed = feedparser.parse(__FEED_URL)
    for item in feed["entries"]:
        yield (item["title"], item["link"])


def __feed_item_filter(feed_tuple: Tuple[str, str]) -> bool:
    """ Takes a feed item and determines if it matches any of the prefixes. """
    # TODO: Would be a lot cooler to have regexes.
    #       That way we can filter disros by arch and version.
    lower_title = feed_tuple[0].lower()
    for prefix in __DISTRO_PREFIXES:
        if lower_title.startswith(prefix):
            return True

    return False


def __dump() -> None:
    """ Performs the actual work. """

    # Get all items from the feed and filter them for the relevant ones.
    feed_items = __get_feed_items()
    feed_items = [item for item in feed_items if __feed_item_filter(item)]

    # Get any files in cache.
    cached_items = {
        path_entry
        for path_entry
        in os.listdir(__CACHE_DIR)
        if os.path.isfile(os.path.join(__CACHE_DIR, path_entry))
    }

    # Create a scraper to download with.
    scraper = cloudscraper.create_scraper()

    # Start going through filtered items and work them over.
    for item in feed_items:

        # Only download items not already in cache.
        filename, url = item
        if filename not in cached_items:
        
            pprint("Downloading: %s" % filename)

            # Do the download!
            cache_path = os.path.join(__CACHE_DIR, filename)
            target_path = os.path.join(__DUMP_DIR, filename)
            response = scraper.get(url, allow_redirects=True, cookies={})
            response.raise_for_status()

            # Save the file to cache.
            with open(cache_path, 'wb') as f_obj:
                f_obj.write(response.content)

            # Copy cache to destination.
            shutil.copyfile(
                cache_path,
                target_path
            )


def run() -> None:
    """ Main runnable function. """
    try:
        pprint("DistroWatch Dumper %s" % __VERSION__)
        pprint("Verifying configuration.")
        __verify_environ()
    except AssertionError as exc:
        pprint("Configuration could not be verfied: %s" % str(exc), text_class="error")
        sys.exit(1)

    pprint("Setting globals from environemtn.")
    __set_globals()

    pprint("Entering main program loop.")

    while True:
        try:
            __dump()
        except KeyboardInterrupt:
            pprint("Keyboard interrupt recieved, shutting down.")
            sys.exit(0)
        except Exception as exc:
            pprint("An error occured during dump: %s" % str(exc), text_class="warning")
            pprint("Retrying after next sleep.", text_class="warning")
        finally:
            pprint("Sleeping for %i seconds." % __DUMP_INTERVAL)
            sleep(__DUMP_INTERVAL)

if __name__ == "__main__":
    run()
