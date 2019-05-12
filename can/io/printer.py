# coding: utf-8

"""
This Listener simply prints to stdout / the terminal or a file.
"""

from __future__ import print_function, absolute_import

import logging

from can.listener import Listener
from .generic import BaseIOHandler

log = logging.getLogger('can.io.printer')


class Printer(BaseIOHandler, Listener):
    """
    The Printer class is a subclass of :class:`~can.Listener` which simply prints
    any messages it receives to the terminal (stdout). A message is turned into a
    string using :meth:`~can.Message.__str__`.

    :attr bool write_to_file: `True` iff this instance prints to a file instead of
                              standard out
    """

    def __init__(self, file=None):
        """
        :param file: an optional path-like object or as file-like object to "print"
                     to instead of writing to standard out (stdout)
                     If this is a file-like object, is has to opened in text
                     write mode, not binary write mode.
        """
        self.write_to_file = file is not None
        super(Printer, self).__init__(file, mode='w')

    def on_message_received(self, msg):
        if self.write_to_file:
            self.file.write(str(msg) + '\n')
        else:
            print(msg)
