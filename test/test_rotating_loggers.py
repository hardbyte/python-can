#!/usr/bin/env python

"""
Test rotating loggers
"""

import os
from pathlib import Path
from unittest.mock import Mock

import can
from .data.example_data import generate_message


class TestBaseRotatingLogger:
    @staticmethod
    def _get_instance(path, *args, **kwargs) -> can.io.BaseRotatingLogger:
        class SubClass(can.io.BaseRotatingLogger):
            """Subclass that implements abstract methods for testing."""

            _supported_formats = {".asc", ".blf", ".csv", ".log", ".txt"}

            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self._writer = can.Printer(file=path / "__unused.txt")

            def should_rollover(self, msg: can.Message) -> bool:
                return False

            def do_rollover(self):
                ...

        return SubClass(*args, **kwargs)

    def test_import(self):
        assert hasattr(can.io, "BaseRotatingLogger")

    def test_attributes(self):
        assert issubclass(can.io.BaseRotatingLogger, can.Listener)
        assert hasattr(can.io.BaseRotatingLogger, "namer")
        assert hasattr(can.io.BaseRotatingLogger, "rotator")
        assert hasattr(can.io.BaseRotatingLogger, "rollover_count")
        assert hasattr(can.io.BaseRotatingLogger, "writer")
        assert hasattr(can.io.BaseRotatingLogger, "rotation_filename")
        assert hasattr(can.io.BaseRotatingLogger, "rotate")
        assert hasattr(can.io.BaseRotatingLogger, "on_message_received")
        assert hasattr(can.io.BaseRotatingLogger, "stop")
        assert hasattr(can.io.BaseRotatingLogger, "should_rollover")
        assert hasattr(can.io.BaseRotatingLogger, "do_rollover")

    def test_get_new_writer(self, tmp_path):
        logger_instance = self._get_instance(tmp_path)

        writer = logger_instance._get_new_writer(tmp_path / "file.ASC")
        assert isinstance(writer, can.ASCWriter)
        writer.stop()

        writer = logger_instance._get_new_writer(tmp_path / "file.BLF")
        assert isinstance(writer, can.BLFWriter)
        writer.stop()

        writer = logger_instance._get_new_writer(tmp_path / "file.CSV")
        assert isinstance(writer, can.CSVWriter)
        writer.stop()

        writer = logger_instance._get_new_writer(tmp_path / "file.LOG")
        assert isinstance(writer, can.CanutilsLogWriter)
        writer.stop()

        writer = logger_instance._get_new_writer(tmp_path / "file.TXT")
        assert isinstance(writer, can.Printer)
        writer.stop()

    def test_rotation_filename(self, tmp_path):
        logger_instance = self._get_instance(tmp_path)

        default_name = "default"
        assert logger_instance.rotation_filename(default_name) == "default"

        logger_instance.namer = lambda x: x + "_by_namer"
        assert logger_instance.rotation_filename(default_name) == "default_by_namer"

    def test_rotate_without_rotator(self, tmp_path):
        logger_instance = self._get_instance(tmp_path)

        source = str(tmp_path / "source.txt")
        dest = str(tmp_path / "dest.txt")

        assert os.path.exists(source) is False
        assert os.path.exists(dest) is False

        logger_instance._writer = logger_instance._get_new_writer(source)
        logger_instance.stop()

        assert os.path.exists(source) is True
        assert os.path.exists(dest) is False

        logger_instance.rotate(source, dest)

        assert os.path.exists(source) is False
        assert os.path.exists(dest) is True

    def test_rotate_with_rotator(self, tmp_path):
        logger_instance = self._get_instance(tmp_path)

        rotator_func = Mock()
        logger_instance.rotator = rotator_func

        source = str(tmp_path / "source.txt")
        dest = str(tmp_path / "dest.txt")

        assert os.path.exists(source) is False
        assert os.path.exists(dest) is False

        logger_instance._writer = logger_instance._get_new_writer(source)
        logger_instance.stop()

        assert os.path.exists(source) is True
        assert os.path.exists(dest) is False

        logger_instance.rotate(source, dest)
        rotator_func.assert_called_with(source, dest)

        # assert that no rotation was performed since rotator_func
        # does not do anything
        assert os.path.exists(source) is True
        assert os.path.exists(dest) is False

    def test_stop(self, tmp_path):
        """Test if stop() method of writer is called."""
        with self._get_instance(tmp_path) as logger_instance:
            logger_instance._writer = logger_instance._get_new_writer(
                tmp_path / "file.ASC"
            )

            # replace stop method of writer with Mock
            original_stop = logger_instance.writer.stop
            mock_stop = Mock()
            logger_instance.writer.stop = mock_stop

            logger_instance.stop()
            mock_stop.assert_called()

            # close file.ASC to enable cleanup of temp_dir
            original_stop()

    def test_on_message_received(self, tmp_path):
        logger_instance = self._get_instance(tmp_path)

        logger_instance._writer = logger_instance._get_new_writer(tmp_path / "file.ASC")

        # Test without rollover
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

        # Test with rollover
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
        assert hasattr(can.SizedRotatingLogger, "namer")
        assert hasattr(can.SizedRotatingLogger, "rotator")
        assert hasattr(can.SizedRotatingLogger, "should_rollover")
        assert hasattr(can.SizedRotatingLogger, "do_rollover")

    def test_create_instance(self, tmp_path):
        base_filename = "mylogfile.ASC"
        max_bytes = 512

        logger_instance = can.SizedRotatingLogger(
            base_filename=tmp_path / base_filename, max_bytes=max_bytes
        )
        assert Path(logger_instance.base_filename).name == base_filename
        assert logger_instance.max_bytes == max_bytes
        assert logger_instance.rollover_count == 0
        assert isinstance(logger_instance.writer, can.ASCWriter)

        logger_instance.stop()

    def test_should_rollover(self, tmp_path):
        base_filename = "mylogfile.ASC"
        max_bytes = 512

        logger_instance = can.SizedRotatingLogger(
            base_filename=tmp_path / base_filename, max_bytes=max_bytes
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

    def test_logfile_size(self, tmp_path):
        base_filename = "mylogfile.ASC"
        max_bytes = 1024
        msg = generate_message(0x123)

        logger_instance = can.SizedRotatingLogger(
            base_filename=tmp_path / base_filename, max_bytes=max_bytes
        )
        for _ in range(128):
            logger_instance.on_message_received(msg)

        for file_path in os.listdir(tmp_path):
            assert os.path.getsize(tmp_path / file_path) <= 1100

        logger_instance.stop()

    def test_logfile_size_context_manager(self, tmp_path):
        base_filename = "mylogfile.ASC"
        max_bytes = 1024
        msg = generate_message(0x123)

        with can.SizedRotatingLogger(
            base_filename=tmp_path / base_filename, max_bytes=max_bytes
        ) as logger_instance:
            for _ in range(128):
                logger_instance.on_message_received(msg)

            for file_path in os.listdir(tmp_path):
                assert os.path.getsize(os.path.join(tmp_path, file_path)) <= 1100
