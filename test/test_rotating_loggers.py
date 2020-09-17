#!/usr/bin/env python
# coding: utf-8

"""
Test rotating loggers
"""
import os
from pathlib import Path
import tempfile
from unittest.mock import Mock

import pytest

import can
from .data.example_data import generate_message


class TestBaseRotatingLogger:
    @staticmethod
    def _get_instance(*args, **kwargs):
        class SubClass(can.io.BaseRotatingLogger):
            """Subclass that implements abstract methods for testing."""

            def should_rollover(self, msg):
                ...

            def do_rollover(self):
                ...

        return SubClass(*args, **kwargs)

    def test_import(self):
        assert hasattr(can.io, "BaseRotatingLogger")

    def test_attributes(self):
        assert issubclass(can.io.BaseRotatingLogger, can.Listener)
        assert hasattr(can.io.BaseRotatingLogger, "supported_writers")
        assert hasattr(can.io.BaseRotatingLogger, "namer")
        assert hasattr(can.io.BaseRotatingLogger, "rotator")
        assert hasattr(can.io.BaseRotatingLogger, "rollover_count")
        assert hasattr(can.io.BaseRotatingLogger, "writer")
        assert hasattr(can.io.BaseRotatingLogger, "rotation_filename")
        assert hasattr(can.io.BaseRotatingLogger, "rotate")
        assert hasattr(can.io.BaseRotatingLogger, "on_message_received")
        assert hasattr(can.io.BaseRotatingLogger, "get_new_writer")
        assert hasattr(can.io.BaseRotatingLogger, "stop")
        assert hasattr(can.io.BaseRotatingLogger, "should_rollover")
        assert hasattr(can.io.BaseRotatingLogger, "do_rollover")

    def test_supported_writers(self):
        supported_writers = can.io.BaseRotatingLogger.supported_writers
        assert supported_writers[".asc"] == can.ASCWriter
        assert supported_writers[".blf"] == can.BLFWriter
        assert supported_writers[".csv"] == can.CSVWriter
        assert supported_writers[".log"] == can.CanutilsLogWriter
        assert supported_writers[".txt"] == can.Printer

    def test_get_new_writer(self):
        logger_instance = self._get_instance()

        # access to non existing writer shall raise ValueError
        with pytest.raises(ValueError):
            _ = logger_instance.writer

        with tempfile.TemporaryDirectory() as temp_dir:
            logger_instance.get_new_writer(os.path.join(temp_dir, "file.ASC"))
            assert isinstance(logger_instance.writer, can.ASCWriter)
            logger_instance.stop()

            logger_instance.get_new_writer(os.path.join(temp_dir, "file.BLF"))
            assert isinstance(logger_instance.writer, can.BLFWriter)
            logger_instance.stop()

            logger_instance.get_new_writer(os.path.join(temp_dir, "file.CSV"))
            assert isinstance(logger_instance.writer, can.CSVWriter)
            logger_instance.stop()

            logger_instance.get_new_writer(os.path.join(temp_dir, "file.LOG"))
            assert isinstance(logger_instance.writer, can.CanutilsLogWriter)
            logger_instance.stop()

            logger_instance.get_new_writer(os.path.join(temp_dir, "file.TXT"))
            assert isinstance(logger_instance.writer, can.Printer)
            logger_instance.stop()

    def test_rotation_filename(self):
        logger_instance = self._get_instance()

        default_name = "default"
        assert logger_instance.rotation_filename(default_name) == "default"

        logger_instance.namer = lambda x: x + "_by_namer"
        assert logger_instance.rotation_filename(default_name) == "default_by_namer"

    def test_rotate(self):
        logger_instance = self._get_instance()

        # test without rotator
        with tempfile.TemporaryDirectory() as temp_dir:
            source = os.path.join(temp_dir, "source.txt")
            dest = os.path.join(temp_dir, "dest.txt")

            assert os.path.exists(source) is False
            assert os.path.exists(dest) is False

            logger_instance.get_new_writer(source)
            logger_instance.stop()

            assert os.path.exists(source) is True
            assert os.path.exists(dest) is False

            logger_instance.rotate(source, dest)

            assert os.path.exists(source) is False
            assert os.path.exists(dest) is True

        # test with rotator
        rotator_func = Mock()
        logger_instance.rotator = rotator_func
        with tempfile.TemporaryDirectory() as temp_dir:
            source = os.path.join(temp_dir, "source.txt")
            dest = os.path.join(temp_dir, "dest.txt")

            assert os.path.exists(source) is False
            assert os.path.exists(dest) is False

            logger_instance.get_new_writer(source)
            logger_instance.stop()

            assert os.path.exists(source) is True
            assert os.path.exists(dest) is False

            logger_instance.rotate(source, dest)
            rotator_func.assert_called_with(source, dest)

            # assert that no rotation was performed since rotator_func
            # does not do anything
            assert os.path.exists(source) is True
            assert os.path.exists(dest) is False

    def test_stop(self):
        """Test if stop() method of writer is called."""
        logger_instance = self._get_instance()

        with tempfile.TemporaryDirectory() as temp_dir:
            logger_instance.get_new_writer(os.path.join(temp_dir, "file.ASC"))

            # replace stop method of writer with Mock
            org_stop = logger_instance.writer.stop
            mock_stop = Mock()
            logger_instance.writer.stop = mock_stop

            logger_instance.stop()
            mock_stop.assert_called()

            # close file.ASC to enable cleanup of temp_dir
            org_stop()

    def test_on_message_received(self):
        logger_instance = self._get_instance()

        with tempfile.TemporaryDirectory() as temp_dir:
            logger_instance.get_new_writer(os.path.join(temp_dir, "file.ASC"))

            """Test without rollover"""
            should_rollover = Mock(return_value=False)
            do_rollover = Mock()
            writers_on_message_received = Mock()

            logger_instance.should_rollover = should_rollover
            logger_instance.do_rollover = do_rollover
            logger_instance.writer.on_message_received = writers_on_message_received

            msg = generate_message(0x123)
            logger_instance.on_message_received(msg)

            should_rollover.assert_called_with(msg)
            do_rollover.assert_not_called()
            writers_on_message_received.assert_called_with(msg)

            """Test with rollover"""
            should_rollover = Mock(return_value=True)
            do_rollover = Mock()
            writers_on_message_received = Mock()

            logger_instance.should_rollover = should_rollover
            logger_instance.do_rollover = do_rollover
            logger_instance.writer.on_message_received = writers_on_message_received

            msg = generate_message(0x123)
            logger_instance.on_message_received(msg)

            should_rollover.assert_called_with(msg)
            do_rollover.assert_called()
            writers_on_message_received.assert_called_with(msg)

            # stop writer to enable cleanup of temp_dir
            logger_instance.stop()


class TestSizedRotatingLogger:
    def test_import(self):
        assert hasattr(can.io, "SizedRotatingLogger")
        assert hasattr(can, "SizedRotatingLogger")

    def test_attributes(self):
        assert issubclass(can.SizedRotatingLogger, can.io.BaseRotatingLogger)
        assert hasattr(can.SizedRotatingLogger, "supported_writers")
        assert hasattr(can.SizedRotatingLogger, "namer")
        assert hasattr(can.SizedRotatingLogger, "rotator")
        assert hasattr(can.SizedRotatingLogger, "should_rollover")
        assert hasattr(can.SizedRotatingLogger, "do_rollover")

    def test_create_instance(self):
        base_filename = "mylogfile.ASC"
        max_bytes = 512

        with tempfile.TemporaryDirectory() as temp_dir:
            logger_instance = can.SizedRotatingLogger(
                base_filename=os.path.join(temp_dir, base_filename), max_bytes=max_bytes
            )
            assert Path(logger_instance.base_filename).name == base_filename
            assert logger_instance.max_bytes == max_bytes
            assert logger_instance.rollover_count == 0
            assert isinstance(logger_instance.writer, can.ASCWriter)

            logger_instance.stop()

    def test_should_rollover(self):
        base_filename = "mylogfile.ASC"
        max_bytes = 512

        with tempfile.TemporaryDirectory() as temp_dir:
            logger_instance = can.SizedRotatingLogger(
                base_filename=os.path.join(temp_dir, base_filename), max_bytes=max_bytes
            )
            msg = generate_message(0x123)
            do_rollover = Mock()
            logger_instance.do_rollover = do_rollover

            logger_instance.writer.file.tell = Mock(return_value=511)
            assert logger_instance.should_rollover(msg) is False
            logger_instance.on_message_received(msg)
            do_rollover.assert_not_called()

            logger_instance.writer.file.tell = Mock(return_value=512)
            assert logger_instance.should_rollover(msg) is True
            logger_instance.on_message_received(msg)
            do_rollover.assert_called()

            logger_instance.stop()

    def test_logfile_size(self):
        base_filename = "mylogfile.ASC"
        max_bytes = 1024
        msg = generate_message(0x123)

        with tempfile.TemporaryDirectory() as temp_dir:
            logger_instance = can.SizedRotatingLogger(
                base_filename=os.path.join(temp_dir, base_filename), max_bytes=max_bytes
            )
            for _ in range(128):
                logger_instance.on_message_received(msg)

            for file_path in os.listdir(temp_dir):
                assert os.path.getsize(os.path.join(temp_dir, file_path)) <= 1100

            logger_instance.stop()
