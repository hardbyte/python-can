

from can import LogReader
import os


class TestAscReader:

    def test_basic_read(self):
        logfile = os.path.join(os.path.dirname(__file__), "data",
                               "logfile_vector_fd.asc")
        reader = LogReader(logfile)
        messages = []
        for msg in reader:
            messages.append(msg)

        assert len(messages) == 4

        first_message = messages[0]
        assert first_message.timestamp == 0.045522
        assert first_message.arbitration_id == 0x7d
        assert first_message.is_extended_id is False
        assert first_message.channel == 61
        assert first_message.dlc == 8
        assert first_message.data == \
               bytearray([0x01, 0x1b, 0xd6, 0xd0, 0x8a, 0x1f, 0xd7, 0xf6])
        assert first_message.is_fd is True
        assert first_message.bitrate_switch is True
        assert first_message.error_state_indicator is False

        second_message = messages[1]
        assert second_message.timestamp == 0.045636
        assert second_message.arbitration_id == 0x88
        assert second_message.is_extended_id is False
        assert second_message.channel == 61
        assert second_message.dlc == 8
        assert second_message.data == \
               bytearray([0x0, 0x0, 0xf6, 0x90, 0x0, 0x0, 0x0, 0x0])
        assert second_message.is_fd is True
        assert second_message.bitrate_switch is False
        assert second_message.error_state_indicator is True

        third_message = messages[2]
        assert third_message.timestamp == 0.045746
        assert third_message.arbitration_id == 0x167
        assert third_message.is_extended_id is True
        assert third_message.channel == 61
        assert third_message.dlc == 8
        assert third_message.data == \
               bytearray([0x73, 0x80, 0x0, 0x10, 0x0, 0x9, 0xe3, 0x0])
        assert third_message.is_fd is True
        assert third_message.bitrate_switch is True
        assert third_message.error_state_indicator is False

        fourth_message = messages[3]
        assert fourth_message.timestamp == 24.986902
        assert fourth_message.arbitration_id == 0x716
        assert fourth_message.is_extended_id is False
        assert fourth_message.channel == 6
        assert fourth_message.dlc == 64
        assert fourth_message.data == bytearray([
            0x12, 0x3b, 0x36, 0x01, 0x7b, 0x0a, 0x20, 0x20,
            0x20, 0x20, 0x22, 0x66, 0x69, 0x6c, 0x65, 0x43,
            0x6f, 0x75, 0x6e, 0x74, 0x22, 0x3a, 0x20, 0x31,
            0x2c, 0x20, 0x0a, 0x20, 0x20, 0x20, 0x20, 0x22,
            0x65, 0x63, 0x75, 0x49, 0x64, 0x22, 0x3a, 0x20,
            0x22, 0x30, 0x78, 0x30, 0x37, 0x31, 0x36, 0x22,
            0x2c, 0x20, 0x0a, 0x20, 0x20, 0x20, 0x20, 0x22,
            0x64, 0x69, 0x64, 0x22, 0x3a, 0x20, 0x22, 0x46
        ])
        assert fourth_message.is_fd is True
        assert fourth_message.bitrate_switch is True
        assert fourth_message.error_state_indicator is False