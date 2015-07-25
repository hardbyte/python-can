"""
The core of python-can - contains implementations of all
the major classes in the library, which form abstractions of the
functionality provided by each CAN interface.

Copyright (C) 2010 Dynamic Controls
"""
from __future__ import print_function

import logging

try:
    import queue
except ImportError:
    import Queue as queue

log = logging.getLogger('can')
log.debug("Loading python-can")


def set_logging_level(level_name=None):
    """Set the logging level for python-can.
    Expects one of: 'critical', 'error', 'warning', 'info', 'debug', 'subdebug'
    """
    try:
        log.setLevel(getattr(logging, level_name.upper()))
    except AttributeError:
        log.setLevel(logging.DEBUG)
    log.debug("Logging set to {}".format(level_name))

    logging.basicConfig()


class Listener(object):
    def on_message_received(self, msg):
        raise NotImplementedError(
            "{} has not implemented on_message_received".format(
                self.__class__.__name__)
        )

    def __call__(self, msg):
        return self.on_message_received(msg)


class BufferedReader(Listener):
    """
    A BufferedReader is a subclass of :class:`~can.Listener` which implements a
    **message buffer**: that is, when the :class:`can.BufferedReader` instance is
    notified of a new message it pushes it into a queue of messages waiting to
    be serviced.
    """

    def __init__(self):
        self.buffer = queue.Queue(0)

    def on_message_received(self, msg):
        self.buffer.put(msg)

    def get_message(self, timeout=0.5):
        """
        Attempts to retrieve the latest message received by the instance. If no message is
        available it blocks for 0.5 seconds or until a message is received (whichever
        is shorter), and returns the message if there is one, or None if there is not.
        """
        try:
            return self.buffer.get(block=True, timeout=timeout)
        except queue.Empty:
            return None


class Printer(Listener):
    """
    The Printer class is a subclass of :class:`~can.Listener` which simply prints
    any messages it receives to the terminal.

    :param output_file: An optional file to "print" to.
    """

    def __init__(self, output_file=None):
        if output_file is not None:
            log.info("Creating log file '{}' ".format(output_file))
            output_file = open(output_file, 'wt')
        self.output_file = output_file

    def on_message_received(self, msg):
        if self.output_file is not None:
            self.output_file.write(str(msg) + "\n")
        else:
            print(msg)

    def __del__(self):
        self.output_file.write("\n")
        if self.output_file:
            self.output_file.close()


class CSVWriter(Listener):
    """Writes a comma separated text file of
    timestamp, arbitrationid, flags, dlc, data
    for each messages received.
    """

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

    def __del__(self):
        self.csv_file.close()
        super(CSVWriter, self).__del__()


class SqliteWriter(Listener):
    """TODO"""

    def __init__(self, filename):
        self.db_file = open(filename, 'wt')

        # create table structure
        raise NotImplementedError("TODO")

    def on_message_received(self, msg):
        # add row
        raise NotImplementedError("TODO")
