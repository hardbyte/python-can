"""
Implements an SQL database writer and reader for storing CAN messages.
"""

from can.listener import BufferedReader
from can.message import Message

import sys
import time
import threading
import sqlite3
import logging

log = logging.getLogger('can.io.sql')

if sys.version_info > (3,):
    buffer = memoryview


class SqlReader:
    def __init__(self, filename):
        log.debug("Starting SqlReader with %s", filename)
        conn = sqlite3.connect(filename)

        self.cursor = conn.cursor()


    @staticmethod
    def _create_frame_from_db_tuple(frame_data):
        timestamp, id, is_extended, is_remote, is_error, dlc, data = frame_data
        return Message(
            timestamp, is_remote, is_extended, is_error, id, dlc, data
        )

    def __iter__(self):
        log.debug("Iterating through messages from sql db")
        for frame_data in self.cursor.execute("SELECT * FROM messages"):
            yield SqlReader._create_frame_from_db_tuple(frame_data)


class SqliteWriter(BufferedReader):
    """Logs received CAN data to a simple SQL database.

    The sqlite database may already exist, otherwise it will
    be created when the first message arrives.

    Messages are internally buffered and written to the SQL file in a background
    thread.

    .. note::

        When the listener's :meth:`~SqliteWriter.stop` method is called the
        thread writing to the sql file will continue to receive and internally
        buffer messages if they continue to arrive before the
        :attr:`~SqliteWriter.GET_MESSAGE_TIMEOUT`.

        If the :attr:`~SqliteWriter.GET_MESSAGE_TIMEOUT` expires before a message
        is received, the internal buffer is written out to the sql file.

        However if the bus is still saturated with messages, the Listener
        will continue receiving until the :attr:`~SqliteWriter.MAX_TIME_BETWEEN_WRITES`
        timeout is reached.

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
        self.writer_thread = threading.Thread(target=self._db_writer_thread)
        self.writer_thread.start()

    def _create_db(self):
        # Note: you can't share sqlite3 connections between threads
        # hence we setup the db here.
        log.info("Creating sqlite database")
        self.conn = sqlite3.connect(self.db_fn)
        cursor = self.conn.cursor()

        # create table structure
        cursor.execute('''
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

    def _db_writer_thread(self):
        num_frames = 0
        last_write = time.time()
        self._create_db()

        while not self.stop_running_event.is_set():
            messages = []

            msg = self.get_message(self.GET_MESSAGE_TIMEOUT)
            while msg is not None:
                log.debug("SqliteWriter: buffering message")

                messages.append((
                    msg.timestamp,
                    msg.arbitration_id,
                    msg.id_type,
                    msg.is_remote_frame,
                    msg.is_error_frame,
                    msg.dlc,
                    buffer(msg.data)
                ))

                if time.time() - last_write > self.MAX_TIME_BETWEEN_WRITES:
                    log.debug("Max timeout between writes reached")
                    break

                msg = self.get_message(self.GET_MESSAGE_TIMEOUT)

            count = len(messages)
            if count > 0:
                with self.conn:
                    log.debug("Writing %s frames to db", count)
                    self.conn.executemany(SqliteWriter.insert_msg_template, messages)
                    num_frames += count
                    last_write = time.time()

            # go back up and check if we are still supposed to run

        self.conn.close()
        log.info("Stopped sqlite writer after writing %s messages", num_frames)

    def stop(self):
        self.stop_running_event.set()
        log.debug("Stopping sqlite writer")
        self.writer_thread.join()
