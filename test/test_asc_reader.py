import os

from can import LogReader, Message, ASCReader


class TestAscReader:
    def test_log_reader_asc_detection(self):
        """Validate that LogReader is correctly detecting the .asc files"""
        logfile = os.path.join(os.path.dirname(__file__), "data", "logfile.asc")
        with LogReader(logfile) as reader:
            assert isinstance(reader, ASCReader)

    def test_asc_reader(self):
        logfile = os.path.join(os.path.dirname(__file__), "data", "logfile.asc")
        with ASCReader(logfile) as reader:
            messages = list(reader)

        assert len(messages) == 10
        # TODO: add messages validation

    def test_can_fd_frames(self):
        logfile = os.path.join(os.path.dirname(__file__), "data", "logfile_can_fd.asc")
        with ASCReader(logfile) as reader:
            messages = list(reader)

        assert len(messages) == 4

        validation_messages = [
            Message(
                timestamp=0.045522,
                arbitration_id=0x7D,
                is_extended_id=False,
                channel=61,
                dlc=8,
                data=(0x01, 0x1B, 0xD6, 0xD0, 0x8A, 0x1F, 0xD7, 0xF6),
                is_fd=True,
                bitrate_switch=True,
            ),
            Message(
                timestamp=0.045636,
                arbitration_id=0x88,
                is_extended_id=False,
                channel=61,
                dlc=8,
                data=(0x0, 0x0, 0xF6, 0x90, 0x0, 0x0, 0x0, 0x0),
                is_fd=True,
                bitrate_switch=False,
                error_state_indicator=True,
            ),
            Message(
                timestamp=0.045746,
                arbitration_id=0x167,
                is_extended_id=True,
                channel=61,
                dlc=8,
                data=(0x73, 0x80, 0x0, 0x10, 0x0, 0x9, 0xE3, 0x0),
                is_fd=True,
                bitrate_switch=True,
            ),
            Message(
                timestamp=24.986902,
                arbitration_id=0x716,
                is_extended_id=False,
                channel=6,
                dlc=64,
                data=(
                    0x12,
                    0x3B,
                    0x36,
                    0x01,
                    0x7B,
                    0x0A,
                    0x20,
                    0x20,
                    0x20,
                    0x20,
                    0x22,
                    0x66,
                    0x69,
                    0x6C,
                    0x65,
                    0x43,
                    0x6F,
                    0x75,
                    0x6E,
                    0x74,
                    0x22,
                    0x3A,
                    0x20,
                    0x31,
                    0x2C,
                    0x20,
                    0x0A,
                    0x20,
                    0x20,
                    0x20,
                    0x20,
                    0x22,
                    0x65,
                    0x63,
                    0x75,
                    0x49,
                    0x64,
                    0x22,
                    0x3A,
                    0x20,
                    0x22,
                    0x30,
                    0x78,
                    0x30,
                    0x37,
                    0x31,
                    0x36,
                    0x22,
                    0x2C,
                    0x20,
                    0x0A,
                    0x20,
                    0x20,
                    0x20,
                    0x20,
                    0x22,
                    0x64,
                    0x69,
                    0x64,
                    0x22,
                    0x3A,
                    0x20,
                    0x22,
                    0x46,
                ),
                is_fd=True,
                bitrate_switch=True,
            ),
        ]

        for i in range(len(validation_messages)):
            assert messages[i].equals(validation_messages[i])
