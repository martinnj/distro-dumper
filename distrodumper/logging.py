""" Logging library for general output """

# System imports.
import logging
import os
import re

from typing import Optional


####################################################################################################
###                                                                                              ###
###                                    Constants & Variables                                     ###
###                                                                                              ###
####################################################################################################


# Detect if debug mode is active.
DEBUG = os.environ.get("DUMPER_DEBUG", "") == "true"

# Terminal printing control character stuff
TERM_OK_BLUE = '\033[94m'
TERM_OK_GREEN = '\033[92m'
TERM_WARNING = '\033[93m'
TERM_FAIL = '\033[91m'
TERM_ENDC = '\033[0m'
TERM_BOLD = '\033[1m'
TERM_UNDERLINE = '\033[4m'
TERM_INVERT = '\033[7m'

# Lookup log levels to terminal color codes.
LOGGING_COLOR_LOOKUP = {
    logging.DEBUG: TERM_OK_BLUE,
    logging.INFO: TERM_OK_GREEN,
    logging.WARNING: TERM_WARNING,
    logging.ERROR: TERM_FAIL,
    logging.CRITICAL: TERM_INVERT + TERM_BOLD + TERM_FAIL
}


####################################################################################################
###                                                                                              ###
###                                Custom Logger-Related Classes                                 ###
###                                                                                              ###
####################################################################################################


class ConsoleFormatter(logging.Formatter):
    """ Make console logging nice and colored. """

    def format(self, record):
        # Call the base formatter to get the default format in place.
        log_line = super().format(record)

        # Look up the color code for the log-level.
        color_code = LOGGING_COLOR_LOOKUP[record.levelno]

        # Find the log level and color it.
        # This is a hack and needs to be adjust if the formatter does not have the level as the
        # third element.
        reg_result = re.findall(r"\[(.+?)\]", log_line)
        log_line = log_line.replace(reg_result[2], color_code + reg_result[2] + TERM_ENDC)
        return log_line


class ProgressAdapter(logging.LoggerAdapter):
    """ Support progress tuples in the logger. """

    def __format_progress(self, progress: Optional[tuple[int,int]]) -> str:
        """
        Formats a progress tuple into some nice square brackets.
        Examples:
        - [7/7]
        - [001/100]

        Returns an empty string if no Tuple is given or the tuple isn't formed correctly.

        ### Arguments
        - progress : Optional[tuple[int,int]]
        A tuple with two integers. Second element should be >= first element for formatting to look
        as intended.

        ### Returns:
        - str: A string with the formatted progress indicator, or an empty string if the progress
               tuple was missing or malformed.
        """

        if isinstance(progress, tuple) and len(progress) == 2:
            current = progress[0]
            total = progress[1]
            if isinstance(current, int) and isinstance(total, int):
                current_padded = ("%0" + str(len(str(total))) + "i") % current
                return f"[{current_padded}/{total}] "

        # Return nothing otherwise.
        return ""

    def process(self, msg, kwargs):
        progress_t = kwargs.pop("progress", self.extra.get("progress"))
        progress_str = self.__format_progress(progress_t) if isinstance(progress_t, tuple) else ""
        return f"{progress_str}{msg}", kwargs


####################################################################################################
###                                                                                              ###
###                                     Logger Factory Method                                    ###
###                                                                                              ###
####################################################################################################


def get_logger(name: str) -> logging.LoggerAdapter:
    """
    Creates a named logger with our wanted output formatting.

    ### Arguments
    - name : str
      Name of the logger, should usually correspond to the library or section of code that calls it.

    ### Returns:
    - logging.LoggerAdapter: The configured logger.
    """

    # Create a new stream handler for the logger, and set the appropriate level.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    # Create a formatter so we can print the way we want to.
    console_formatter = ConsoleFormatter("[%(asctime)-15s] [%(name)s] [%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)

    # Create a logger with the requested name and add the handler so the logs go there.
    logger = logging.Logger(name)
    logger.addHandler(console_handler)

    logger = ProgressAdapter(logger, {"progress": None})
    return logger
