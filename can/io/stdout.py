#!/usr/bin/env python
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
    any messages it receives to the terminal (stdout). A message is tunred into a
    string using :meth:`~can.Message.__str__`.
    """

    def __init__(self, filename=None):
        """
        :param str output_file: An optional file to "print" to
        """
        self.write_to_file = filename is not None
        super(Printer, self).__init__(file=filename, mode='w')

    def on_message_received(self, msg):
        if self.write_to_file:
            self.file.write(str(msg) + '\n')
        else:
            print(msg)
