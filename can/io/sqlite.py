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
        log.debug("Starting sqlreader with {}".format(filename))
        conn = sqlite3.connect(filename)

        self.c = conn.cursor()


    @staticmethod
    def create_frame_from_db_tuple(frame_data):
        ts, id, is_extended, is_remote, is_error, dlc, data = frame_data
        return Message(
            ts, is_remote, is_extended, is_error, id, dlc, data
        )

    def __iter__(self):
        log.debug("Iterating through messages from sql db")
        for frame_data in self.c.execute("SELECT * FROM messages"):
            yield SqlReader.create_frame_from_db_tuple(frame_data)


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

