#!/usr/bin/env python
# coding: utf-8

"""
"""

from __future__ import absolute_import

from time import sleep
import unittest
import random
import logging
import tempfile
import os.path
import sqlite3

import can

from .data.example_data import generate_message

channel = 'vcan0'
can.rc['interface'] = 'virtual'

logging.getLogger('').setLevel(logging.DEBUG)

# make tests more reproducible
random.seed(13339115)


class ListenerImportTest(unittest.TestCase):

    def testClassesImportable(self):
        self.assertTrue(hasattr(can, 'Listener'))
        self.assertTrue(hasattr(can, 'BufferedReader'))
        self.assertTrue(hasattr(can, 'Notifier'))
        self.assertTrue(hasattr(can, 'Logger'))

        self.assertTrue(hasattr(can, 'ASCWriter'))
        self.assertTrue(hasattr(can, 'ASCReader'))

        self.assertTrue(hasattr(can, 'BLFReader'))
        self.assertTrue(hasattr(can, 'BLFWriter'))

        self.assertTrue(hasattr(can, 'CSVWriter'))

        self.assertTrue(hasattr(can, 'CanutilsLogWriter'))
        self.assertTrue(hasattr(can, 'CanutilsLogReader'))

        self.assertTrue(hasattr(can, 'SqliteReader'))
        self.assertTrue(hasattr(can, 'SqliteWriter'))

        self.assertTrue(hasattr(can, 'Printer'))

        self.assertTrue(hasattr(can, 'LogReader'))

        self.assertTrue(hasattr(can.io.player, 'MessageSync'))


class BusTest(unittest.TestCase):

    def setUp(self):
        self.bus = can.interface.Bus()

    def tearDown(self):
        self.bus.shutdown()


class ListenerTest(BusTest):

    def testBasicListenerCanBeAddedToNotifier(self):
        a_listener = can.Listener()
        notifier = can.Notifier(self.bus, [a_listener], 0.1)
        notifier.stop()
        self.assertIn(a_listener, notifier.listeners)

    def testLogger(self):
        def test_filetype_to_instance(extension, klass):
            can_logger = can.Logger("test.{}".format(extension))
            self.assertIsInstance(can_logger, klass)
            can_logger.stop()

        test_filetype_to_instance('asc', can.ASCWriter)
        test_filetype_to_instance('log', can.CanutilsLogWriter)
        test_filetype_to_instance("blf", can.BLFWriter)
        test_filetype_to_instance("csv", can.CSVWriter)
        test_filetype_to_instance("db",  can.SqliteWriter)
        test_filetype_to_instance("txt", can.Printer)

    def testBufferedListenerReceives(self):
        a_listener = can.BufferedReader()
        a_listener(generate_message(0xDADADA))
        m = a_listener.get_message(0.2)
        self.assertIsNotNone(m)


if __name__ == '__main__':
    unittest.main()
