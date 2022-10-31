#!/usr/bin/env python

"""
"""
import asyncio
import unittest
import random
import logging
import tempfile
import os
import warnings
from os.path import join, dirname

import can

from .data.example_data import generate_message

logging.basicConfig(level=logging.DEBUG)

# makes the random number generator deterministic
random.seed(13339115)


class ListenerImportTest(unittest.TestCase):
    def testClassesImportable(self):
        self.assertTrue(hasattr(can, "Listener"))
        self.assertTrue(hasattr(can, "BufferedReader"))
        self.assertTrue(hasattr(can, "Notifier"))
        self.assertTrue(hasattr(can, "Logger"))

        self.assertTrue(hasattr(can, "ASCWriter"))
        self.assertTrue(hasattr(can, "ASCReader"))

        self.assertTrue(hasattr(can, "BLFReader"))
        self.assertTrue(hasattr(can, "BLFWriter"))

        self.assertTrue(hasattr(can, "CSVReader"))
        self.assertTrue(hasattr(can, "CSVWriter"))

        self.assertTrue(hasattr(can, "CanutilsLogWriter"))
        self.assertTrue(hasattr(can, "CanutilsLogReader"))

        self.assertTrue(hasattr(can, "SqliteReader"))
        self.assertTrue(hasattr(can, "SqliteWriter"))

        self.assertTrue(hasattr(can, "Printer"))

        self.assertTrue(hasattr(can, "LogReader"))

        self.assertTrue(hasattr(can, "MessageSync"))


class BusTest(unittest.TestCase):
    def setUp(self):
        # Save all can.rc defaults
        self._can_rc = can.rc
        can.rc = {"interface": "virtual"}
        self.bus = can.interface.Bus()

    def tearDown(self):
        self.bus.shutdown()
        # Restore the defaults
        can.rc = self._can_rc


class ListenerTest(BusTest):
    def testBasicListenerCanBeAddedToNotifier(self):
        a_listener = can.Printer()
        notifier = can.Notifier(self.bus, [a_listener], 0.1)
        notifier.stop()
        self.assertIn(a_listener, notifier.listeners)

    def testAddListenerToNotifier(self):
        a_listener = can.Printer()
        notifier = can.Notifier(self.bus, [], 0.1)
        notifier.stop()
        self.assertNotIn(a_listener, notifier.listeners)
        notifier.add_listener(a_listener)
        self.assertIn(a_listener, notifier.listeners)

    def testRemoveListenerFromNotifier(self):
        a_listener = can.Printer()
        notifier = can.Notifier(self.bus, [a_listener], 0.1)
        notifier.stop()
        self.assertIn(a_listener, notifier.listeners)
        notifier.remove_listener(a_listener)
        self.assertNotIn(a_listener, notifier.listeners)

    def testPlayerTypeResolution(self):
        def test_filetype_to_instance(extension, klass):
            print("testing: {}".format(extension))
            try:
                if extension == ".blf":
                    delete = False
                    file_handler = open(
                        join(dirname(__file__), "data", "test_CanMessage.blf")
                    )
                else:
                    delete = True
                    file_handler = tempfile.NamedTemporaryFile(
                        suffix=extension, delete=False
                    )

                with file_handler as my_file:
                    filename = my_file.name
                with can.LogReader(filename) as reader:
                    self.assertIsInstance(reader, klass)
            finally:
                if delete:
                    os.remove(filename)

        test_filetype_to_instance(".asc", can.ASCReader)
        test_filetype_to_instance(".blf", can.BLFReader)
        test_filetype_to_instance(".csv", can.CSVReader)
        test_filetype_to_instance(".db", can.SqliteReader)
        test_filetype_to_instance(".log", can.CanutilsLogReader)

    def testPlayerTypeResolutionUnsupportedFileTypes(self):
        for should_fail_with in ["", ".", ".some_unknown_extention_42"]:
            with self.assertRaises(ValueError):
                with can.LogReader(should_fail_with):  # make sure we close it anyways
                    pass

    def testLoggerTypeResolution(self):
        def test_filetype_to_instance(extension, klass):
            print("testing: {}".format(extension))
            try:
                with tempfile.NamedTemporaryFile(
                    suffix=extension, delete=False
                ) as my_file:
                    filename = my_file.name
                with can.Logger(filename) as writer:
                    self.assertIsInstance(writer, klass)
            finally:
                os.remove(filename)

        test_filetype_to_instance(".asc", can.ASCWriter)
        test_filetype_to_instance(".blf", can.BLFWriter)
        test_filetype_to_instance(".csv", can.CSVWriter)
        test_filetype_to_instance(".db", can.SqliteWriter)
        test_filetype_to_instance(".log", can.CanutilsLogWriter)
        test_filetype_to_instance(".txt", can.Printer)

        with can.Logger(None) as logger:
            self.assertIsInstance(logger, can.Printer)

    def testLoggerTypeResolutionUnsupportedFileTypes(self):
        for should_fail_with in ["", ".", ".some_unknown_extention_42"]:
            with self.assertRaises(ValueError):
                with can.Logger(should_fail_with):  # make sure we close it anyways
                    pass

    def testBufferedListenerReceives(self):
        a_listener = can.BufferedReader()
        a_listener(generate_message(0xDADADA))
        a_listener(generate_message(0xDADADA))
        self.assertIsNotNone(a_listener.get_message(0.1))
        a_listener.stop()
        self.assertIsNotNone(a_listener.get_message(0.1))


def test_deprecated_loop_arg(recwarn):
    warnings.simplefilter("always")
    can.AsyncBufferedReader(loop=asyncio.get_event_loop())
    assert len(recwarn) > 0
    assert recwarn.pop(DeprecationWarning)
    recwarn.clear()

    # assert that no warning is shown when loop argument is not used
    can.AsyncBufferedReader()
    assert len(recwarn) == 0


if __name__ == "__main__":
    unittest.main()
