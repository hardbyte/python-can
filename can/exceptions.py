"""
There are several specific :class:`Exception` classes to allow user
code to react to specific scenarios related to CAN busses::

    Exception (Python standard library)
     +-- ...
     +-- CanError (python-can)
         +-- CanBackendError
         +-- CanInitializationError
         +-- CanOperationError
         +-- CanTimeoutError

"""


class CanError(Exception):
    """Base class for all can related exceptions."""


class CanBackEndError(CanError):
    """Indicates an error related to the backend (e.g. driver/OS/library)
    Examples:
    - A call to a library function results in an unexpected return value
    """


class CanInitializationError(CanError):
    """Indicates an error related to the initialization.
    Examples for situations when this exception may occur:
    - Try to open a non-existent device and/or channel
    - Try to use an invalid setting, which is ok by value, but not ok for the interface
    """


class CanOperationError(CanError):
    """Indicates an error while in operation."""


class CanTimeoutError(CanError):
    """Indicates a timeout of an operation."""
