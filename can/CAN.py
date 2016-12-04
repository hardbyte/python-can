"""
The core of python-can - contains implementations of all
the major classes in the library, which form abstractions of the
functionality provided by each CAN interface.

Copyright (C) 2010 Dynamic Controls
"""
from __future__ import print_function

import logging
import sys
import threading
from datetime import datetime
import time
import base64
import sqlite3

from can.message import Message

try:
    import queue
except ImportError:
    import Queue as queue


if sys.version_info > (3,):
    buffer = memoryview

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

class RedirectReader(Listener):
    """
    A RedirectReader sends all received messages
    to another Bus.

    """

    def __init__(self, bus):
        self.bus = bus

    def on_message_received(self, msg):
        self.bus.send(msg)


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


class LogReader(object):
    """
    Replay logged CAN messages from a file.

    The format is determined from the file format which can be one of:
      * .asc: :class:`can.ASCWriter`
      * .csv: :class:`can.CSVWriter`
      * .db: :class:`can.SqliteWriter`

    Options:

    - Ignore timestamps
    - Minimum time between messages
    - Skip periods of inactivity greater than X

    """

    @classmethod
    def __new__(cls, other, filename):
        if filename.endswith(".asc"):
            raise NotImplemented
        #     return ASCReader(filename)
        if filename.endswith(".csv"):
            raise NotImplemented
        #     return CSVReader(filename)
        if filename.endswith(".db"):
            return SqliteReader(filename)


class MessageSync:

    def __init__(self, messages, timestamps=True, gap=0.0001, skip=60):
        """

        :param messages: An iterable of :class:`can.Message` instances.
        :param timestamps: Use the messages' timestamps.
        :param gap: Minimum time between sent messages
        :param skip: Skip periods of inactivity greater than this.
        """
        self.raw_messages = messages
        self.timestamps = timestamps
        self.gap = gap
        self.skip = skip

    def __iter__(self):
        log.debug("Iterating over messages at real speed")
        playback_start_time = time.time()
        recorded_start_time = None

        for m in self.raw_messages:
            if recorded_start_time is None:
                recorded_start_time = m.timestamp

            if self.timestamps:
                # Work out the correct wait time
                now = time.time()
                current_offset = now - playback_start_time
                recorded_offset_from_start = m.timestamp - recorded_start_time
                remaining_gap = recorded_offset_from_start - current_offset

                sleep_period = max(self.gap, min(self.skip, remaining_gap))
            else:
                sleep_period = self.gap

            time.sleep(sleep_period)
            yield m


class SqliteReader:
    def __init__(self, filename):
        log.debug("Starting sqlitereader with {}".format(filename))
        conn = sqlite3.connect(filename)

        self.c = conn.cursor()
        self.c.execute("SELECT ts FROM messages LIMIT 1")

        self.recorded_start_time = self.c.fetchone()[0]

        self.recorded_start_datetime = datetime.fromtimestamp(self.recorded_start_time)

    @staticmethod
    def create_frame_from_db_tuple(frame_data):
        ts, id, is_extended, is_remote, is_error, dlc, data = frame_data
        return Message(
            ts, is_remote, is_extended, is_error, id, dlc, data
        )

    def __iter__(self):
        log.debug("Iterating through messages from sql db")
        for frame_data in self.c.execute("SELECT * FROM messages"):
            yield SqliteReader.create_frame_from_db_tuple(frame_data)


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


class SqliteWriter(BufferedReader):
    """Logs received CAN data to a simple SQL database.

    The sqlite database may already exist, otherwise it will
    be created when the first message arrives.
    """

    insert_msg_template = '''
        INSERT INTO messages VALUES
        (?, ?, ?, ?, ?, ?, ?)
        '''

    GET_MESSAGE_TIMEOUT = 0.25
    """Number of seconds to wait for messages from internal queue"""

    MAX_TIME_BETWEEN_WRITES = 5
    """Maximum number of seconds to wait between writes to the database"""

    def __init__(self, filename):
        super(SqliteWriter, self).__init__()
        self.db_fn = filename
        self.stop_running_event = threading.Event()
        self.writer_thread = threading.Thread(target=self.db_writer_thread)
        self.writer_thread.start()

    def _create_db(self):
        # Note you can't share sqlite3 connections between threads
        # hence we setup the db here.
        log.info("Creating sqlite db")
        self.conn = sqlite3.connect(self.db_fn)
        c = self.conn.cursor()

        # create table structure
        c.execute('''
        CREATE TABLE IF NOT EXISTS messages
        (
          ts REAL,
          arbitration_id INTEGER,
          extended INTEGER,
          remote INTEGER,
          error INTEGER,
          dlc INTEGER,
          data BLOB
        )
        ''')
        self.conn.commit()

        self.db_setup = True

    def db_writer_thread(self):
        num_frames = 0
        last_write = time.time()
        self._create_db()

        while not self.stop_running_event.is_set():
            messages = []

            m = self.get_message(self.GET_MESSAGE_TIMEOUT)
            while m is not None:
                log.debug("sqlitewriter buffering message")

                messages.append((
                    m.timestamp,
                    m.arbitration_id,
                    m.id_type,
                    m.is_remote_frame,
                    m.is_error_frame,
                    m.dlc,
                    buffer(m.data)
                ))
                m = self.get_message(self.GET_MESSAGE_TIMEOUT)

                if time.time() - last_write > self.MAX_TIME_BETWEEN_WRITES:
                    log.debug("Max timeout between writes reached")
                    break

            if len(messages) > 0:
                with self.conn:
                    log.debug("Writing %s frames to db", len(messages))
                    self.conn.executemany(SqliteWriter.insert_msg_template, messages)
                    num_frames += len(messages)
                    last_write = time.time()

        self.conn.close()
        log.info("Stopped sqlite writer after writing %s messages", num_frames)

    def stop(self):
        self.stop_running_event.set()
        log.debug("Stopping sqlite writer")
        self.writer_thread.join()


class ASCWriter(Listener):
    """Logs CAN data to an ASCII log file (.asc)"""

    LOG_STRING = "{time: 9.4f} {channel}  {id:<15} Rx   d {dlc} {data}\n"
    EVENT_STRING = "{time: 9.4f} {message}\n"

    def __init__(self, filename, channel=1):
        now = datetime.now().strftime("%a %b %m %I:%M:%S %p %Y")
        self.channel = channel
        self.started = time.time()
        self.log_file = open(filename, "w")
        self.log_file.write("date %s\n" % now)
        self.log_file.write("base hex  timestamps absolute\n")
        self.log_file.write("internal events logged\n")
        self.log_file.write("Begin Triggerblock %s\n" % now)
        self.log_event("Start of measurement")

    def stop(self):
        """Stops logging and closes the file."""
        if self.log_file is not None:
            self.log_file.write("End TriggerBlock\n")
            self.log_file.close()
            self.log_file = None

    def log_event(self, message):
        """Add an arbitrary message to the log file."""
        timestamp = time.time() - self.started
        line = self.EVENT_STRING.format(time=timestamp, message=message)
        if self.log_file is not None:
            self.log_file.write(line)

    def on_message_received(self, msg):
        data = ["{:02X}".format(byte) for byte in msg.data]
        arb_id = "{:X}".format(msg.arbitration_id)
        if msg.id_type:
            arb_id = arb_id + "x"
        timestamp = msg.timestamp
        if timestamp >= self.started:
            timestamp -= self.started

        line = self.LOG_STRING.format(time=timestamp,
                                      channel=self.channel,
                                      id=arb_id,
                                      dlc=msg.dlc,
                                      data=" ".join(data))
        if self.log_file is not None:
            self.log_file.write(line)
