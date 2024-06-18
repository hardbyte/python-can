#!/usr/bin/env python

"""
Test rotating loggers
"""

import os
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import can
from can.io.generic import FileIOMessageWriter
from can.typechecking import StringPathLike

from .data.example_data import generate_message


class TestBaseRotatingLogger:
    @staticmethod
    def _get_instance(file: StringPathLike) -> can.io.BaseRotatingLogger:
        class SubClass(can.io.BaseRotatingLogger):
            """Subclass that implements abstract methods for testing."""

            _supported_formats = {".asc", ".blf", ".csv", ".log", ".txt"}

            def __init__(self, file: StringPathLike, **kwargs) -> None:
                super().__init__(**kwargs)
                suffix = Path(file).suffix.lower()
                if suffix not in self._supported_formats:
                    raise ValueError(f"Unsupported file format: {suffix}")
                self._writer = can.Printer(file=file)

            @property
            def writer(self) -> FileIOMessageWriter:
                return cast(FileIOMessageWriter, self._writer)

            def should_rollover(self, msg: can.Message) -> bool:
                return False

            def do_rollover(self): ...

        return SubClass(file=file)

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
        with self._get_instance(tmp_path / "__unused.txt") as logger_instance:
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
        with self._get_instance(tmp_path / "__unused.txt") as logger_instance:
            default_name = "default"
            assert logger_instance.rotation_filename(default_name) == "default"

            logger_instance.namer = lambda x: x + "_by_namer"
            assert logger_instance.rotation_filename(default_name) == "default_by_namer"

    def test_rotate_without_rotator(self, tmp_path):
        with self._get_instance(tmp_path / "__unused.txt") as logger_instance:
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
        with self._get_instance(tmp_path / "__unused.txt") as logger_instance:
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
        with self._get_instance(tmp_path / "file.ASC") as logger_instance:
            # replace stop method of writer with Mock
            original_stop = logger_instance.writer.stop
            mock_stop = Mock()
            logger_instance.writer.stop = mock_stop

            logger_instance.stop()
            mock_stop.assert_called()

            # close file.ASC to enable cleanup of temp_dir
            original_stop()

    def test_on_message_received(self, tmp_path):
        with self._get_instance(tmp_path / "file.ASC") as logger_instance:
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

    def test_issue_1792(self, tmp_path):
        with self._get_instance(tmp_path / "__unused.log") as logger_instance:
            writer = logger_instance._get_new_writer(
                tmp_path / "2017_Jeep_Grand_Cherokee_3.6L_V6.log"
            )
            assert isinstance(writer, can.CanutilsLogWriter)
            writer.stop()


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

        with can.SizedRotatingLogger(
            base_filename=tmp_path / base_filename, max_bytes=max_bytes
        ) as logger_instance:
            assert Path(logger_instance.base_filename).name == base_filename
            assert logger_instance.max_bytes == max_bytes
            assert logger_instance.rollover_count == 0
            assert isinstance(logger_instance.writer, can.ASCWriter)

    def test_should_rollover(self, tmp_path):
        base_filename = "mylogfile.ASC"
        max_bytes = 512

        with can.SizedRotatingLogger(
            base_filename=tmp_path / base_filename, max_bytes=max_bytes
        ) as logger_instance:
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

    def test_logfile_size(self, tmp_path):
        base_filename = "mylogfile.ASC"
        max_bytes = 1024
        msg = generate_message(0x123)

        with can.SizedRotatingLogger(
            base_filename=tmp_path / base_filename, max_bytes=max_bytes
        ) as logger_instance:
            for _ in range(128):
                logger_instance.on_message_received(msg)

            for file_path in os.listdir(tmp_path):
                assert os.path.getsize(tmp_path / file_path) <= 1100

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
