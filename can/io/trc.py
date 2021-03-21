# coding: utf-8

"""
Reader and writer for can logging files in peak trc format
"""

from __future__ import absolute_import

import logging

from ..listener import Listener
from .generic import BaseIOHandler


logger = logging.getLogger('can.io.trc')


class TRCReader(BaseIOHandler):
    """
    Iterator of CAN messages from a TRC logging file.
    """

    def __init__(self, file):
        """
        :param file: a path-like object or as file-like object to read from
                     If this is a file-like object, is has to opened in text
                     read mode, not binary read mode.
        """
        super(TRCReader, self).__init__(file, mode='r')

    def __iter__(self):
        pass


class TRCWriter(BaseIOHandler, Listener):
    """Logs CAN data to text file (.trc).

    The measurement starts with the timestamp of the first registered message.
    If a message has a timestamp smaller than the previous one or None,
    it gets assigned the timestamp that was written for the last message.
    It the first message does not have a timestamp, it is set to zero.
    """

    def __init__(self, file, channel=1):
        """
        :param file: a path-like object or as file-like object to write to
                     If this is a file-like object, is has to opened in text
                     write mode, not binary write mode.
        :param channel: a default channel to use when the message does not
                        have a channel set
        """
        super(TRCWriter, self).__init__(file, mode='w')
        self.channel = channel

    def on_message_received(self, msg):
        pass
