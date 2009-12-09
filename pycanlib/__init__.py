"""
Module: pycanlib

An interface to Kvaser's CANLIB SDK, written in Python.
"""

import logging


class NullHandler(logging.Handler):
    """
    Class: NullHandler
    
    An instance of this class is added as the pycanlib logger's default
    handler, to prevent error messages about a missing handler from
    appearing in the output of any programs that use pycanlib but choose
    not to use its logging capabilities. This logger produces no output
    itself (see the `emit` function below), so has no effect on the rest
    of a program's output (either to the command line or to a file).
    
    Parent class: logging.Handler
    """

    def emit(self, record):
        """
        Function: emit
        
        Function called by the logging library when a logger that this handler
        is associated with receives a message to be logged.
        """
        pass


logging.getLogger("pycanlib").addHandler(NullHandler())
