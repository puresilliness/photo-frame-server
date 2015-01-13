"""A utility module.  Classes and functions in this module should be items
which are general solutions that have little direct relevence the the current
project."""

import logging


class ErrorFilter(logging.Filter):
    """ErrorFilter will filter out all logging messages of level ERROR or
    higher. The main intent of the class is to make it easy to have a handler
    for logging messages of low priority that doesn't repeat the high priority
    messages being logged elseware."""

    def filter(self, record):
        return int(record.levelno) < logging.ERROR
