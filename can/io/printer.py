"""
This Listener simply prints to stdout / the terminal or a file.
"""

import logging

from typing import Optional, cast, TextIO

from ..message import Message
from ..listener import Listener
from .generic import BaseIOHandler
from ..typechecking import AcceptedIOType

log = logging.getLogger("can.io.printer")


class Printer(BaseIOHandler, Listener):
    """
    The Printer class is a subclass of :class:`~can.Listener` which simply prints
    any messages it receives to the terminal (stdout). A message is turned into a
    string using :meth:`~can.Message.__str__`.

    :attr write_to_file: `True` if this instance prints to a file instead of
                         standard out
    """

    file: Optional[TextIO]

    def __init__(
        self, file: Optional[AcceptedIOType] = None, append: bool = False
    ) -> None:
        """
        :param file: An optional path-like object or a file-like object to "print"
                     to instead of writing to standard out (stdout).
                     If this is a file-like object, is has to be opened in text
                     write mode, not binary write mode.
        :param append: If set to `True` messages, are appended to the file,
                       else the file is truncated
        """
        mode = "a" if append else "w"
        super().__init__(file, mode=mode)

    def on_message_received(self, msg: Message) -> None:
        if self.file is not None:
            self.file.write(str(msg) + "\n")
        else:
            print(msg)
