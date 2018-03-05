#!/usr/bin/env python
# coding: utf-8

"""
This Listener simply prints to stdout / the terminal or a file.
"""

from __future__ import print_function

import logging

from can.listener import Listener

log = logging.getLogger('can.io.stdout')


class Printer(Listener):
    """
    The Printer class is a subclass of :class:`~can.Listener` which simply prints
    any messages it receives to the terminal (stdout).

    :param output_file: An optional file to "print" to.
    """

    def __init__(self, output_file=None):
        if output_file is not None:
            log.info('Creating log file "{}"'.format(output_file))
            output_file = open(output_file, 'wt')
        self.output_file = output_file

    def on_message_received(self, msg):
        if self.output_file is not None:
            self.output_file.write(str(msg) + '\n')
        else:
            print(msg)

    def stop(self):
        if self.output_file:
            self.output_file.write('\n')
            self.output_file.close()
