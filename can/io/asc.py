from datetime import datetime
import time
import logging

from can.listener import Listener
from can.message import Message

CAN_MSG_EXT = 0x80000000
CAN_ID_MASK = 0x1FFFFFFF

logger = logging.getLogger('can.io.asc')


class ASCReader(object):
    """
    Iterator of CAN messages from a ASC Logging File.
    """

    def __init__(self, filename):
        self.file = open(filename, 'r')

    @staticmethod
    def _extract_can_id(str_can_id):
        if str_can_id[-1:].lower() == "x":
            is_extended = True
            can_id = int(str_can_id[0:-1], 16)
        else:
            is_extended = False
            can_id = int(str_can_id, 16)
        logging.debug('ASCReader: _extract_can_id("%s") -> %x, %r', str_can_id, can_id, is_extended)
        return (can_id, is_extended)

    def __iter__(self):
        for line in self.file:
            logger.debug("ASCReader: parsing line: '%s'", line.splitlines()[0])

            temp = line.strip()
            if not temp or not temp[0].isdigit():
                continue

            try:
                (timestamp, channel, dummy) = temp.split(None, 2) # , frameType, dlc, frameData
            except ValueError:
                # we parsed an empty comment
                continue

            timestamp = float(timestamp)

            if dummy.strip()[0:10] == 'ErrorFrame':
                msg = Message(timestamp=timestamp, is_error_frame=True)
                yield msg

            elif not channel.isdigit() or dummy.strip()[0:10] == 'Statistic:':
                pass

            elif dummy[-1:].lower() == 'r':
                (can_id_str, _) = dummy.split(None, 1)
                (can_id_num, is_extended_id) = self._extract_can_id(can_id_str)
                msg = Message(timestamp=timestamp,
                              arbitration_id=can_id_num & CAN_ID_MASK,
                              extended_id=is_extended_id,
                              is_remote_frame=True)
                yield msg

            else:
                try:
                    # this only works if dlc > 0 and thus data is availabe
                    (can_id_str, _, _, dlc, data) = dummy.split(None, 4)
                except ValueError:
                    # but if not, we only want to get the stuff up to the dlc
                    (can_id_str, _, _, dlc      ) = dummy.split(None, 3)
                    # and we set data to an empty sequence manually
                    data = ''

                dlc = int(dlc)
                frame = bytearray()
                data = data.split()
                for byte in data[0:dlc]:
                    frame.append(int(byte, 16))

                (can_id_num, is_extended_id) = self._extract_can_id(can_id_str)

                msg = Message(
                            timestamp=timestamp,
                            arbitration_id=can_id_num & CAN_ID_MASK,
                            extended_id=is_extended_id,
                            is_remote_frame=False,
                            dlc=dlc,
                            data=frame)
                yield msg


class ASCWriter(Listener):
    """Logs CAN data to an ASCII log file (.asc)"""

    LOG_STRING      = "{time: 9.4f} {channel}  {id:<15} Rx   {dtype} {data}\n"
    EVENT_STRING    = "{time: 9.4f} {message}\n"

    def __init__(self, filename, channel=1):
        now = datetime.now().strftime("%a %b %m %I:%M:%S %p %Y")
        self.channel = channel
        self.started = time.time()
        self.log_file = open(filename, 'w')
        self.log_file.write("date %s\n" % now)
        self.log_file.write("base hex  timestamps absolute\n")
        self.log_file.write("internal events logged\n")
        self.log_file.write("Begin Triggerblock %s\n" % now)
        self.log_event("Start of measurement")

    def stop(self):
        """Stops logging and closes the file."""
        if not self.log_file.closed:
            self.log_file.write("End TriggerBlock\n")
            self.log_file.close()

    def log_event(self, message, timestamp=None):
        """Add an arbitrary message to the log file."""

        if not message: # if empty or None
            logger.debug("ASCWriter: ignoring empty message")
            return

        timestamp = (timestamp or time.time())
        if timestamp >= self.started:
            timestamp -= self.started

        line = self.EVENT_STRING.format(time=timestamp, message=message)
        if not self.log_file.closed:
            self.log_file.write(line)

    def on_message_received(self, msg):
        if msg.is_error_frame:
            self.log_event("{}  ErrorFrame".format(self.channel), msg.timestamp)
            return

        if msg.is_remote_frame:
            dtype = "r"
            data = []
        else:
            dtype = "d {}".format(msg.dlc)
            data = ["{:02X}".format(byte) for byte in msg.data]
        arb_id = "{:X}".format(msg.arbitration_id)
        if msg.id_type:
            arb_id = arb_id + "x"
        timestamp = msg.timestamp
        if timestamp >= self.started:
            timestamp -= self.started

        channel = msg.channel if isinstance(msg.channel, int) else self.channel
        line = self.LOG_STRING.format(time=timestamp,
                                      channel=channel,
                                      id=arb_id,
                                      dtype=dtype,
                                      data=" ".join(data))
        if not self.log_file.closed:
            self.log_file.write(line)
