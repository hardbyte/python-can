#!/usr/bin/env python
# coding: utf-8

"""
Implements an SQL database writer and reader for storing CAN messages.

.. note:: The database schema is given in the documentation of the loggers.
"""

from __future__ import absolute_import

import sys
import time
import threading
import logging
import sqlite3

from can.listener import BufferedReader
from can.message import Message
from .generic import BaseIOHandler

log = logging.getLogger('can.io.sqlite')

# TODO comment on this
if sys.version_info > (3,):
    buffer = memoryview


class SqliteReader(BaseIOHandler):
    """
    Reads recorded CAN messages from a simple SQL database.

    This class can be iterated over or used to fetch all messages in the
    database with :meth:`~SqliteReader.read_all`.

    Calling :func:`~builtin.len` on this object might not run in constant time.

    .. note:: The database schema is given in the documentation of the loggers.
    """

    def __init__(self, filename, table_name="messages"):
        """
        :param str table_name: the name of the table to look for the messages
        """
        super(SqliteReader, self).__init__(open_file=False)
        self.conn = sqlite3.connect(filename)
        self.cursor = self.conn.cursor()
        self.table_name = table_name

    def __iter__(self):
        for frame_data in self.cursor.execute("SELECT * FROM {}".format(self.table_name)):
            timestamp, can_id, is_extended, is_remote, is_error, dlc, data = frame_data
            yield Message(timestamp, is_remote, is_extended, is_error, can_id, dlc, data)

    def __len__(self):
        # this might not run in constant time
        result = self.cursor.execute("SELECT COUNT(*) FROM {}".format(self.table_name))
        return int(result.fetchone()[0])

    def read_all(self):
        """Fetches all messages in the database.
        """
        result = self.cursor.execute("SELECT * FROM {}".format(self.table_name))
        return result.fetchall()

    def stop(self):
        """Closes the connection to the database.
        """
        super(SqliteReader, self).stop()
        self.conn.close()


class SqliteWriter(BaseIOHandler, BufferedReader):
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
        is received, the internal buffer is written out to the databases file.

        However if the bus is still saturated with messages, the Listener
        will continue receiving until the :attr:`~SqliteWriter.MAX_TIME_BETWEEN_WRITES`
        timeout is reached.

    .. note:: The database schema is given in the documentation of the loggers.

    """

    GET_MESSAGE_TIMEOUT = 0.25
    """Number of seconds to wait for messages from internal queue"""

    MAX_TIME_BETWEEN_WRITES = 5.0
    """Maximum number of seconds to wait between writes to the database"""

    def __init__(self, filename, table_name="messages"):
        """
        :param str table_name: the name of the table to store messages in
        """
        super(SqliteWriter, self).__init__(open_file=False)
        self.table_name = table_name
        self.filename = filename
        self.stop_running_event = threading.Event()
        self.writer_thread = threading.Thread(target=self._db_writer_thread)
        self.writer_thread.start()

    def _create_db(self):
        """Creates a new databae or opens a connection to an existing one.

        .. note::
            You can't share sqlite3 connections between threads hence we
            setup the db here.
        """
        log.debug("Creating sqlite database")
        self.conn = sqlite3.connect(self.filename)
        cursor = self.conn.cursor()

        # create table structure
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS {}
        (
          ts REAL,
          arbitration_id INTEGER,
          extended INTEGER,
          remote INTEGER,
          error INTEGER,
          dlc INTEGER,
          data BLOB
        )
        """.format(self.table_name))
        self.conn.commit()

        self.insert_template = "INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?)".format(self.table_name)

    def _db_writer_thread(self):
        num_frames = 0
        last_write = time.time()
        self._create_db()

        try:
            while not self.stop_running_event.is_set():
                messages = []

                msg = self.get_message(self.GET_MESSAGE_TIMEOUT)
                while msg is not None:
                    #log.debug("SqliteWriter: buffering message")

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
                        #log.debug("Max timeout between writes reached")
                        break

                    msg = self.get_message(self.GET_MESSAGE_TIMEOUT)

                count = len(messages)
                if count > 0:
                    with self.conn:
                        #log.debug("Writing %s frames to db", count)
                        self.conn.executemany(self.insert_template, messages)
                        self.conn.commit() # make the changes visible to the entire database
                        num_frames += count
                        last_write = time.time()

                # go back up and check if we are still supposed to run

        finally:
            self.conn.close()
            log.info("Stopped sqlite writer after writing %s messages", num_frames)

    def stop(self):
        super(SqliteWriter, self).stop()
        self.stop_running_event.set()
        self.writer_thread.join()
