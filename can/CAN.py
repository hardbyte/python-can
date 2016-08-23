"""
The core of python-can - contains implementations of all
the major classes in the library, which form abstractions of the
functionality provided by each CAN interface.

Copyright (C) 2010 Dynamic Controls
"""
from __future__ import print_function

import logging
from datetime import datetime
import time
import base64

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

    def stop(self):
        """
        Override to cleanup any open resources.
        """


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
        available it blocks for given timeout or until a message is received (whichever
        is shorter),

        :param float timeout: The number of seconds to wait for a new message.
        :return: the :class:`~can.Message` if there is one, or None if there is not.
        """
        try:
            return self.buffer.get(block=True, timeout=timeout)
        except queue.Empty:
            return None


class Logger(object):
    """
    Logs CAN messages to a file.

    The format is determined from the file format which can be one of:
      * .asc: :class:`can.ASCWriter`
      * .csv: :class:`can.CSVWriter`
      * .db: :class:`can.SqliteWriter`
      * other: :class:`can.Printer`
    """

    @classmethod
    def __new__(cls, other, filename):
        if not filename:
            return Printer()
        elif filename.endswith(".asc"):
            return ASCWriter(filename)
        elif filename.endswith(".csv"):
            return CSVWriter(filename)
        elif filename.endswith(".db"):
            return SqliteWriter(filename)
        else:
            return Printer(filename)


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

    def stop(self):
        if self.output_file:
            self.output_file.write("\n")
            self.output_file.close()


class CSVWriter(Listener):
    """Writes a comma separated text file of
    timestamp, arbitrationid, flags, dlc, data
    for each messages received.
    """

    def __init__(self, filename):
        self.csv_file = open(filename, 'wt')

        # Write a header row
        self.csv_file.write("timestamp, arbitration id, extended, remote, error, dlc, data\n")

    def on_message_received(self, msg):
        row = ','.join([
            str(msg.timestamp),
            hex(msg.arbitration_id),
            '1' if msg.id_type else '0',
            '1' if msg.is_remote_frame else '0',
            '1' if msg.is_error_frame else '0',
            str(msg.dlc),
            base64.b64encode(msg.data).decode('utf8')
            ])
        self.csv_file.write(row + '\n')

    def stop(self):
        self.csv_file.flush()
        self.csv_file.close()


class SqliteWriter(Listener):
    """TODO"""

    def __init__(self, filename):
        self.db_file = open(filename, 'wt')

        # create table structure
        raise NotImplementedError("TODO")

    def on_message_received(self, msg):
        # add row
        raise NotImplementedError("TODO")


class ASCWriter(Listener):
    """Logs CAN data to an ASCII log file (.asc)"""

    LOG_STRING = "{time: 9.4f} {channel}  {id:<15} Rx   d {dlc} {data}\n"

    def __init__(self, filename):
        now = datetime.now().strftime("%a %b %m %I:%M:%S %p %Y")
        self.start = time.time()
        self.log_file = open(filename, "w")
        self.log_file.write("date %s\n" % now)
        self.log_file.write("base hex  timestamps absolute\n")
        self.log_file.write("internal events logged\n")
        self.log_file.write("Begin Triggerblock %s\n" % now)
        self.log_file.write("   0.0000 Start of measurement\n")

    def stop(self):
        """Stops logging and closes the file."""
        if self.log_file:
            self.log_file.write("End TriggerBlock\n")
            self.log_file.close()
            self.log_file = None

    def on_message_received(self, msg):
        data = ["{:02X}".format(byte) for byte in msg.data]
        arb_id = "{:X}".format(msg.arbitration_id)
        if msg.id_type:
            arb_id = arb_id + "x"
        timestamp = msg.timestamp
        if timestamp >= self.start:
            timestamp -= self.start

        line = self.LOG_STRING.format(time=timestamp,
                                      channel=1,
                                      id=arb_id,
                                      dlc=msg.dlc,
                                      data=" ".join(data))
        if self.log_file:
            self.log_file.write(line)
