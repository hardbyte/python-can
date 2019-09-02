# coding: utf-8

"""
Contains a generic class for file IO.
"""

from abc import ABCMeta
from typing import Optional, cast

import can
import can.typechecking


class BaseIOHandler(metaclass=ABCMeta):
    """A generic file handler that can be used for reading and writing.

    Can be used as a context manager.

    :attr Optional[FileLike] file:
        the file-like object that is kept internally, or None if none
        was opened
    """

    def __init__(self, file: can.typechecking.AcceptedIOType, mode: str = "rt") -> None:
        """
        :param file: a path-like object to open a file, a file-like object
                     to be used as a file or `None` to not use a file at all
        :param mode: the mode that should be used to open the file, see
                     :func:`open`, ignored if *file* is `None`
        """
        if file is None or (hasattr(file, "read") and hasattr(file, "write")):
            # file is None or some file-like object
            self.file = cast(Optional[can.typechecking.FileLike], file)
        else:
            # file is some path-like object
            self.file = open(cast(can.typechecking.StringPathLike, file), mode)

        # for multiple inheritance
        super().__init__()

    def __enter__(self) -> "BaseIOHandler":
        return self

    def __exit__(self, *args) -> None:
        self.stop()

    def stop(self) -> None:
        """Closes the undelying file-like object and flushes it, if it was opened in write mode."""
        if self.file is not None:
            # this also implies a flush()
            self.file.close()


# pylint: disable=abstract-method,too-few-public-methods
class MessageWriter(BaseIOHandler, can.Listener, metaclass=ABCMeta):
    """The base class for all writers."""


# pylint: disable=too-few-public-methods
class MessageReader(BaseIOHandler, metaclass=ABCMeta):
    """The base class for all readers."""
