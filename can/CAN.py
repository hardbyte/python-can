"""
The core of python-can - contains implementations of all
the major classes in the library, which form abstractions of the
functionality provided by each CAN interface.

Copyright (C) 2010 Dynamic Controls
"""

import logging
import os
import sys
import platform
import pickle
import ctypes
import Queue as queue
import threading
import time

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('CAN')

log.debug("Loading python-can")

from constants import *
from interfaces import *


# Sets the level of messages that are displayed. Default is 'Warning'
def set_logging_level(level_name=None):
    """
    Given 'critical', 'error', 'warning', 'info', 'debug', 'subdebug'
    Set the logging level for python-can
    """
    try:
        log.setLevel(getattr(logging, level_name.upper()))
    except:
        log.setLevel(logging.DEBUG)


class Listener(object):
    def on_message_received(self, msg):
        raise NotImplementedError(
            "{} has not implemented on_message_received".format(
                self.__class__.__name__)
            )

class BufferedReader(Listener):

    def __init__(self):
        self.__buffer = queue.Queue(0)

    def on_message_received(self, msg):
        self.__buffer.put_nowait(msg)

    def get_message(self):
        try:
            return self.__buffer.get(timeout=0.5)
        except queue.Empty:
            return None

class MessagePrinter(Listener):
    def on_message_received(self, msg):
        print(msg)


class MessageCSVWriter(Listener):
    def __init__(self, filename):
        self.csv_file = open(filename, 'wt')
        
        # Write a header row
        self.csv_file.write("timestamp, arbitrationid, flags, dlc, data")

    def on_message_received(self, msg):
        row = ','.join([msg.timestamp, 
                        msg.arbitration_id, 
                        msg.flags, 
                        msg.dlc, 
                        msg.data])
        self.csv_file.write(row + '\n')