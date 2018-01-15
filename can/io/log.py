from can.listener import Listener
import datetime
import time
from can.message import Message

CAN_MSG_EXT = 0x80000000
CAN_ERR_FLAG = 0x20000000
CAN_ERR_BUSERROR = 0x00000080
CAN_ERR_DLC = 8


class CanutilsLogReader(object):
    """
    Iterator of CAN messages from a .log Logging File (candump -L).

    .log-format looks like this:
    (0.0) vcan0 001#8d00100100820100
    """

    def __init__(self, filename):
        self.fp = open(filename, "r")

    def __iter__(self):
        for line in self.fp:
            temp = line.strip()
            if len(temp) > 0:
                (timestamp, bus, frame) = temp.split()
                timestamp = float(timestamp[1:-1])
                (canId, data) = frame.split("#")
                if len(canId) > 3:
                    isExtended = True
                else:
                    isExtended = False
                canId = int(canId, 16)
                if len(data) > 0 and data[0].lower() == "r":
                    isRemoteFrame = True
                    if len(data) > 1:
                        dlc = int(data[1:])
                    else:
                        dlc = 0
                else:
                    isRemoteFrame = False

                    dlc = int(len(data) / 2)
                    dataBin = bytearray()
                    for i in range(0, 2 * dlc, 2):
                        dataBin.append(int(data[i:(i + 2)], 16))


                if canId & CAN_ERR_FLAG and canId & CAN_ERR_BUSERROR:
                    msg = Message(timestamp=timestamp, is_error_frame=True)
                else:
                    msg = Message(timestamp=timestamp, arbitration_id=canId & 0x1FFFFFFF,
                              extended_id=isExtended, is_remote_frame=isRemoteFrame, dlc=dlc, data=dataBin)
                yield msg


class CanutilsLogWriter(Listener):
    """Logs CAN data to an ASCII log file (.log)
    compatible to candump -L """

    def __init__(self, filename, channel="vcan0"):
        self.channel = channel
        self.started = time.time()
        self.log_file = open(filename, "w")

    def stop(self):
        """Stops logging and closes the file."""
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None

    def on_message_received(self, msg):
        if self.log_file is None:
            return
        if msg.is_error_frame:
            self.log_file.write("(%f) vcan0 %08X#0000000000000000\n" % (msg.timestamp, CAN_ERR_FLAG | CAN_ERR_BUSERROR, ))
            return

        timestamp = msg.timestamp
        if timestamp >= self.started:
            timestamp -= self.started

        if msg.is_remote_frame:
            data = []
            if msg.is_extended_id:
                self.log_file.write("(%f) vcan0 %08X#R\n" % (msg.timestamp, msg.arbitration_id ))
            else:
                self.log_file.write("(%f) vcan0 %03X#R\n" % (msg.timestamp, msg.arbitration_id ))
        else:
            data = ["{:02X}".format(byte) for byte in msg.data]
            if msg.is_extended_id:
                self.log_file.write("(%f) vcan0 %08X#%s\n" % (msg.timestamp, msg.arbitration_id, "".join(data)))
            else:
                self.log_file.write("(%f) vcan0 %03X#%s\n" % (msg.timestamp, msg.arbitration_id, "".join(data)))



