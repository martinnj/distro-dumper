""" Things that are helpful when checking and doing configuration. """

# System imports.
import os

from logging import LoggerAdapter
from types import ModuleType
from typing import Any
from typing import Callable

# Custom imports.
from distrodumper import Configuration
from distrodumper import BaseModuleConfiguration
from distrodumper.logging import get_logger

from distrodumper.modules import arch as arch_module
from distrodumper.modules import debian as debian_module
from distrodumper.modules import example as example_module

from distrodumper.validation import is_atomic_csv
from distrodumper.validation import is_bool_string


####################################################################################################
###                                                                                              ###
###                                 Constants & Global Variables                                 ###
###                                                                                              ###
####################################################################################################


# Logger to handle console out.
_LOGGER: LoggerAdapter = get_logger("CONFIG_HELPER")

# Formats available for download.
# TODO: Find a better way to type the value.
# TODO: Maybe this should just be dynamically loaded instead of mapped manually?
__AVAILABLE_MODULES: dict[str, ModuleType] = {
    "arch": arch_module,
    "example": example_module,
    "debian": debian_module
    # "manjaro": arch_module,
    # "raspberry_pi_os": arch_module,
}

# Environment-variable to validator mapping. (Required variables)
__REQUIRED_VALIDATORS: dict[str, Callable] = {
    "DUMPER_MODULES": lambda val: is_atomic_csv(val, {k for k in __AVAILABLE_MODULES.keys()}),
}

# Environment-variable to validator mapping. (Optional variables)
__OPTIONAL_VALIDATORS: dict[str, Callable] = {
    "DUMPER_CACHE": lambda val: __is_nonempty_string(val) and os.path.isdir(val),
    "DUMPER_DEBUG": is_bool_string,
    "DUMPER_DIRECTORY": lambda val: __is_nonempty_string(val) and os.path.isdir(val),
    "DUMPER_INTERVAL": lambda val: __is_non_zero_int(val),
}


####################################################################################################
###                                                                                              ###
###                                        Helper Methods                                        ###
###                                                                                              ###
####################################################################################################


def __is_nonempty_string(val: Any) -> bool:
    """
    Checks if a value is a non-empty string

    ### Arguments
    - val : Any
      Any object to check.

    ### Returns:
    - bool: True if `val` was a string with at least one character, False otherwise.
    """
    return isinstance(val, str) and len(val) > 0


def __is_module_csv(val: Any) -> bool:
    """
    Checks if a value is a string containing a comma separated list fo valid module names.
    Must contain at least one element.

    ### Arguments
    - val : Any
      Any object to check.

    ### Returns:
    - bool: True if the value is a string containing a comma separated list of valid formats, with
            at least one element.
    """
    if not isinstance(val, str):
        return False

    formats = [format.strip() for format in val.split(",")]
    return len(formats) > 0 and all([_format in __AVAILABLE_MODULES for _format in formats])


def __is_non_zero_int(val: Any) -> bool:
    """
    Checks if a value is an integer > 0 or a string containing an integer > 0.

    ### Arguments
    - val : Any
      Any object to check.

    ### Returns:
    - bool: True if `val` was an integer > 0 or a string containing an integer > 0, False otherwise.
    """
    return isinstance(val, int) or (isinstance(val, str) and val.isdigit() and int(val) > 0)


####################################################################################################
###                                                                                              ###
###                                        Public Methods                                        ###
###                                                                                              ###
####################################################################################################


def verify_environment() -> bool:
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


def generate_from_environment() -> Configuration:
    """
    Assembles the environment variables into a configuration-dataclass.

    ### Returns:
    - `distrodumper.configuration`: The finished configuration object.
    """

    requested_modules = [module.strip() for module in os.environ["DUMPER_MODULES"].split(",")]

    # Assemble required configuration.
    conf = Configuration(
        requested_modules=requested_modules,
    )

    # Add any optional configuration keys that are present.
    if "DUMPER_CACHE" in os.environ:
        raw_val = os.environ["DUMPER_CACHE"]
        conf.cache_dir = raw_val
        _LOGGER.debug(f"Setting \"cache_dir\" = {conf.cache_dir}")

    if "DUMPER_DEBUG" in os.environ:
        raw_val = os.environ["DUMPER_DEBUG"]
        conf.debug = raw_val == "true"
        _LOGGER.debug(f"Setting \"debug\" = {conf.debug}")

    if "DUMPER_DIRECTORY" in os.environ:
        raw_val = os.environ["DUMPER_DIRECTORY"]
        conf.dump_dir = raw_val
        _LOGGER.debug(f"Setting \"dump_dir\" = {conf.dump_dir}")

    if "DUMPER_INTERVAL" in os.environ:
        raw_val = os.environ["DUMPER_INTERVAL"]
        conf.interval = int(raw_val)
        _LOGGER.debug(f"Setting \"interval\" = {conf.interval}")

    return conf


def verify_module_environments(config: Configuration) -> bool:
    """
    Verify that the requested modules can be satisfied by the current environment variables.

    ### Arguments
    - config : Configuration
      The current program configuration.

    ### Returns:
    - bool: True if all requested modules was satisfied, False otherwise.
    """
    
    # Initialize to true, we assume the best of everyone. <3
    valid = True

    # Loop over each requested module.
    for module_name in config.requested_modules:
        # Load specific module and have it verify it's own environment.
        module = __AVAILABLE_MODULES[module_name]
        valid = valid and module.verify_config()

    return valid


def populate_module_configurations(config: Configuration) -> None:
    """
    Populates the module dictionary of the given program config.

    ### Arguments
    - config : Configuration
      The configuration instance to populate with module configurations.
    """

    # Loop over all the requested modules.
    for module_name in config.requested_modules:
        # Fetch the module and generate configuration.
        module = __AVAILABLE_MODULES[module_name]
        module_config = module.generate_from_environment()

        # Assign module & configuration into the program configuration.
        config.modules[module_name] = (module_config, module)
