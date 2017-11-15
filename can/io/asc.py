from can.listener import Listener
from can.message import Message

from datetime import datetime
import time
CAN_MSG_EXT = 0x80000000
CAN_ID_MASK = 0x1FFFFFFF

class ASCReader(object):
    """
    Iterator of CAN messages from a ASC Logging File.
    """

    def __init__(self, filename):
        self.fp = open(filename, "r")

    def __iter__(self):
        def extractCanId(strCanId):
            if strCanId[-1:].lower() == "x":
                isExtended = True
                can_id = int(strCanId[0:-1], 16)
            else:
                isExtended = False
                can_id = int(strCanId, 16)
            return (can_id, isExtended)

        for line in self.fp:
            temp = line.strip()
            if len(temp) == 0 or not temp[0].isdigit():
                continue
            (time, channel, dummy) =  temp.split(None,2) # , frameType, dlc, frameData

            time = float(time)
            if dummy.strip()[0:10] == "ErrorFrame":
                time = float(time)
                msg = Message(timestamp=time, is_error_frame=True)
                yield msg
                continue
            if not channel.isdigit() or dummy.strip()[0:10] == "Statistic:":
                continue
            if dummy[-1:].lower() == "r":
                (canId, _) = dummy.split(None, 1)
                msg = Message(timestamp=time,
                              arbitration_id=extractCanId(canId)[0] & CAN_ID_MASK,
                              extended_id=extractCanId(canId)[1],
                              is_remote_frame=True)
                yield msg
            else:
                (canId, direction,_,dlc,data) = dummy.split(None,4)

                dlc = int(dlc)
                frame = bytearray()
                data = data.split()
                for byte in data[0:dlc]:
                    frame.append(int(byte,16))
                msg = Message(timestamp=time,
                            arbitration_id=extractCanId(canId)[0] & CAN_ID_MASK,
                            extended_id=extractCanId(canId)[1],
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
