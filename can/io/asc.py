from can.listener import Listener

from datetime import datetime
import time


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
        timestamp = (timestamp or time.time()) - self.started
        line = self.EVENT_STRING.format(time=timestamp, message=message)
        if self.log_file is not None:
            self.log_file.write(line)

    def on_message_received(self, msg):
        if msg.is_error_frame:
            self.log_event("ErrorFrame", msg.timestamp)
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
