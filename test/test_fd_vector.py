from can import LogReader
import os


class TestAscReader:
    def test_basic_read(self):
        logfile = os.path.join(
            os.path.dirname(__file__), "data", "logfile_vector_fd.asc"
        )
        reader = LogReader(logfile)
        messages = []
        for msg in reader:
            messages.append(msg)

        assert len(messages) == 4

        first_message = messages[0]
        assert first_message.timestamp == 0.045522
        assert first_message.arbitration_id == 0x7D
        assert not first_message.is_extended_id
        assert first_message.channel == 61
        assert first_message.dlc == 8
        assert first_message.data == bytearray(
            [0x01, 0x1B, 0xD6, 0xD0, 0x8A, 0x1F, 0xD7, 0xF6]
        )
        assert first_message.is_fd
        assert first_message.bitrate_switch
        assert not first_message.error_state_indicator

        second_message = messages[1]
        assert second_message.timestamp == 0.045636
        assert second_message.arbitration_id == 0x88
        assert not second_message.is_extended_id
        assert second_message.channel == 61
        assert second_message.dlc == 8
        assert second_message.data == bytearray(
            [0x0, 0x0, 0xF6, 0x90, 0x0, 0x0, 0x0, 0x0]
        )
        assert second_message.is_fd
        assert not second_message.bitrate_switch
        assert second_message.error_state_indicator

        third_message = messages[2]
        assert third_message.timestamp == 0.045746
        assert third_message.arbitration_id == 0x167
        assert third_message.is_extended_id
        assert third_message.channel == 61
        assert third_message.dlc == 8
        assert third_message.data == bytearray(
            [0x73, 0x80, 0x0, 0x10, 0x0, 0x9, 0xE3, 0x0]
        )
        assert third_message.is_fd
        assert third_message.bitrate_switch
        assert not third_message.error_state_indicator

        fourth_message = messages[3]
        assert fourth_message.timestamp == 24.986902
        assert fourth_message.arbitration_id == 0x716
        assert not fourth_message.is_extended_id
        assert fourth_message.channel == 6
        assert fourth_message.dlc == 64
        assert fourth_message.data == bytearray(
            [
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
            ]
        )
        assert fourth_message.is_fd
        assert fourth_message.bitrate_switch
        assert not fourth_message.error_state_indicator
