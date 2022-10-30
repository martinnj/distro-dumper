#!/usr/bin/env python3
""" Worker script to routinely check and dump torrent files """


# System imports.
import sys

from logging import LoggerAdapter
from time import sleep

# 3rd party imports.


# Custom imports.
from distrodumper import config_helper
from distrodumper import Configuration
from distrodumper import file_helper
from distrodumper.logging import get_logger


# Constants.
__VERSION__ = "###VERSION###"

_LOGGER: LoggerAdapter = get_logger("DISTRODUMPER")


def single_run(app_config: Configuration) -> None:
    """
    Performs a single run of the application.

    ### Arguments
    - app_config : Configuration
      Complete application configuration.
    """
    # Get cached files.
    cached_files = file_helper.get_files_in_cache(app_config)

    _LOGGER.info("Running selected dumps.")
    # Loop over all the configured modules.
    for module_name, (module_config, module) in app_config.modules.items():
        # Create the worker and run it!
        _LOGGER.debug(f"Creating & running worker for module: {module_name}")
        worker = module.create_worker(module_config)
        candidates: dict[str,str] = worker.dump()

        # Check if any candidates are new or we already have them. Do accounting.
        removed = 0
        for filename in list(candidates.keys()):
            if filename in cached_files:
                removed -=- 1
                del candidates[filename]

        errors = 0
        for filename, url in candidates.items():
            if not file_helper.download(app_config, filename, url):
                errors -=- 1

        _LOGGER.info(f"{module_name}: Downloaded: {len(candidates) - errors}")
        _LOGGER.info(f"{module_name}: Duplicate: {removed}")
        _LOGGER.info(f"{module_name}: Errors: {errors}")


def main() -> None:
    """ Main runnable function. """

    _LOGGER.info(f"Distro Dumper {__VERSION__}")

    # Verify basic configuration.
    _LOGGER.debug("Verifying basic program environment.")
    if not config_helper.verify_environment():
        _LOGGER.critical("Invalid configuration detected, please reconfigure.")
        sys.exit(1)

    # Get the basic configuration
    _LOGGER.debug("Constructing basic program configuration.")
    app_config: Configuration = config_helper.generate_from_environment()

    # Have each module verify that they can be configured correctly.
    _LOGGER.debug("Verifying configured module envrionements.")
    if not config_helper.verify_module_environments(app_config):
        _LOGGER.critical("A module reported an invalid configuration, please check the log.")

    # Configure each requested module.
    _LOGGER.debug("Constructing selected module configurations.")
    config_helper.populate_module_configurations(app_config)

    # `while True:` is dirty, but honestly. It works for things like this, that has no ochestration
    # and is supposed to run forever.
    _LOGGER.info("Entering main program loop.")
    while True:
        try:
            # Perform a single run of the program.
            single_run(app_config)

        except KeyboardInterrupt:
            # Keyboard interrupts are likely debugging, just exit.
            _LOGGER.info("Keyboard interrupt recieved, shutting down.")
            sys.exit(0)

        except Exception as exc:
            # Unplanned exceptions. Oh no!
            _LOGGER.warning(f"An error occured during dump: {repr(exc)}")
            _LOGGER.warning("Retrying after next sleep.")

        finally:
            _LOGGER.info(f"Sleeping for {app_config.interval} seconds.")
            sleep(app_config.interval)

if __name__ == "__main__":
    main()
