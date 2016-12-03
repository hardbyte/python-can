import logging
logger = logging.getLogger(__name__)


class Message(object):
    """
    The :class:`~can.Message` object is used to represent CAN messages for both sending and receiving.

    Messages can use extended identifiers, be remote or error frames, and contain data.
    """

    def __init__(self, timestamp=0.0, is_remote_frame=False, extended_id=True,
                 is_error_frame=False, arbitration_id=0, dlc=None, data=None):

        self.timestamp = timestamp
        self.id_type = extended_id
        self.is_extended_id = extended_id

        self.is_remote_frame = is_remote_frame
        self.is_error_frame = is_error_frame
        self.arbitration_id = arbitration_id

        #if isinstance(data, list):
        #    data = bytes(data)

        if data is None:
            self.data = bytearray()
            self.dlc = 0
        else:
            try:
                self.data = bytearray(data)
            except TypeError:
                logger.error("Couldn't create message from %r (%r)", data, type(data))

        if dlc is None:
            self.dlc = len(self.data)
        else:
            self.dlc = dlc

        assert self.dlc <= 8, "data link count was {} but it must be less than or equal to 8".format(self.dlc)

    def __str__(self):
        field_strings = ["Timestamp: {0:15.6f}".format(self.timestamp)]
        if self.id_type:
            # Extended arbitrationID
            arbitration_id_string = "ID: {0:08x}".format(self.arbitration_id)
        else:
            arbitration_id_string = "ID: {0:04x}".format(self.arbitration_id)
        field_strings.append(arbitration_id_string.rjust(12, " "))

        flag_string = "".join(
            map(
                str,
                map(
                    int, [
                        self.is_remote_frame,
                        self.id_type,
                        self.is_error_frame,
                    ]
                )
            )
        )

        field_strings.append(flag_string)

        field_strings.append("DLC: {0:d}".format(self.dlc))
        data_strings = []
        if self.data is not None:
            for index in range(0, self.dlc):
                data_strings.append("{0:02x}".format(self.data[index]))
        if len(data_strings) > 0:
            field_strings.append(" ".join(data_strings).ljust(24, " "))
        else:
            field_strings.append(" " * 24)

        if (self.data is not None) and (self.data.isalnum()):
            try:
                field_strings.append("'{}'".format(self.data.decode('utf-8')))
            except UnicodeError as e:
                pass

        return "    ".join(field_strings).strip()

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        data = ["{:#02x}".format(byte) for byte in self.data]
        args = ["timestamp={}".format(self.timestamp),
                "is_remote_frame={}".format(self.is_remote_frame),
                "extended_id={}".format(self.id_type),
                "is_error_frame={}".format(self.is_error_frame),
                "arbitration_id={:#x}".format(self.arbitration_id),
                "dlc={}".format(self.dlc),
                "data=[{}]".format(", ".join(data))]
        return "can.Message({})".format(", ".join(args))

    def __eq__(self, other):
        return (self.arbitration_id == other.arbitration_id and
                #self.timestamp == other.timestamp and
                self.id_type == other.id_type and
                self.dlc == other.dlc and
                self.data == other.data and
                self.is_remote_frame == other.is_remote_frame and
                self.is_error_frame == other.is_error_frame)
