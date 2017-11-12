from can.listener import Listener
from can.message import Message

from datetime import datetime
import time
CAN_MSG_EXT = 0x80000000


class ASCReader(object):
    """
    Iterator of CAN messages from a ASC Logging File.

    Only CAN messages are supported (no Errorframes).
    """

    def __init__(self, filename):
        self.fp = open(filename, "r")

    def __iter__(self):
        for line in self.fp:
            temp = line.strip()
            if len(temp) > 0:
                if temp[0].isdigit():
                    lineArray = temp.split()
                    if lineArray[2] == "ErrorFrame":
                        time = float(lineArray[0])
                        msg = Message(timestamp=time, is_error_frame=True)
                        yield msg
                        continue
                    if lineArray[1].isdigit() and lineArray[2] != "Statistic:":
                        time = float(lineArray[0])
                        channel = lineArray[1]
                        if lineArray[2].endswith("x") or lineArray[2].endswith("X"):
                            isExtended = True
                            can_id = int(lineArray[2][0:-1], 16)
                        else:
                            isExtended = False
                            can_id = int(lineArray[2],16)
                        frameType = lineArray[4]
                        if frameType == 'r' or frameType == 'R':
                            msg = Message(timestamp=time,
                                        arbitration_id=can_id & 0x1FFFFFFF,
                                        extended_id=isExtended,
                                        is_remote_frame=True)
                        else:
                            dlc = int(lineArray[5])
                            frame = bytearray()
                            for byte in lineArray[6:6 + dlc]:
                                frame.append(int(byte,16))
                            msg = Message(timestamp=time,
                                        arbitration_id=can_id & 0x1FFFFFFF,
                                        extended_id=isExtended,
                                        is_remote_frame=False,
                                        dlc=dlc,
                                        data=frame)
                        yield msg


class ASCWriter(Listener):
    """Logs CAN data to an ASCII log file (.asc)"""

    LOG_STRING = "{time: 9.4f} {channel}  {id:<15} Rx   {dtype} {data}\n"
    EVENT_STRING = "{time: 9.4f} {message}\n"

    def __init__(self, filename, channel=1):
        now = datetime.now().strftime("%a %b %m %I:%M:%S %p %Y")
        self.channel = channel
        self.started = time.time()
        self.log_file = open(filename, "w")
        self.log_file.write("date %s\n" % now)
        self.log_file.write("base hex  timestamps absolute\n")
        self.log_file.write("internal events logged\n")
        self.log_file.write("Begin Triggerblock %s\n" % now)
        self.log_event("Start of measurement")

    def stop(self):
        """Stops logging and closes the file."""
        if self.log_file is not None:
            self.log_file.write("End TriggerBlock\n")
            self.log_file.close()
            self.log_file = None

    def log_event(self, message, timestamp=None):
        """Add an arbitrary message to the log file."""
        timestamp = (timestamp or time.time())
        if timestamp >= self.started:
            timestamp -= self.started

        line = self.EVENT_STRING.format(time=timestamp, message=message)
        if self.log_file is not None:
            self.log_file.write(line)

    def on_message_received(self, msg):
        if msg.is_error_frame:
            self.log_event("{} ErrorFrame".format(self.channel), msg.timestamp)
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

        line = self.LOG_STRING.format(time=timestamp,
                                      channel=self.channel,
                                      id=arb_id,
                                      dtype=dtype,
                                      data=" ".join(data))
        if self.log_file is not None:
            self.log_file.write(line)
