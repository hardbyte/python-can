"""
Interface for CANtact devices from Linklayer Labs
"""

import time
import logging
import cantact

from can import BusABC, Message

logger = logging.getLogger(__name__)

class CANtact(BusABC):
    """CANtact interface"""

    @staticmethod
    def _detect_available_configs():
        interface = cantact.Interface()
        channels = []

        for i in range(0, interface.channel_count()):
            channels.append({"interface": "cantact", "channel": "ch:%d" % i})

        return channels

    def __init__(self, channel, bitrate=500000, poll_interval=0.01, monitor=False, **kwargs):
        """
        :param int channel:
            Device number
        :param int bitrate:
            Bitrate in bits/s
        :param bool monitor:
            If true, operate in listen-only monitoring mode
        """

        self.channel = int(channel)
        self.channel_info = "CANtact: ch:%s" % channel

        # configure the interface
        self.interface = cantact.Interface()
        self.interface.set_bitrate(int(channel), int(bitrate))
        self.interface.set_enabled(int(channel), True)
        self.interface.set_monitor(int(channel), monitor)
        self.interface.start()

        super().__init__(
            channel=channel, bitrate=bitrate, poll_interval=poll_interval, **kwargs
        )

    def _recv_internal(self, timeout):
        frame = self.interface.recv(int(timeout * 1000))
        if frame is None:
            # timeout occured
            return None, False

        msg = Message(
            arbitration_id=frame['id'],
            is_extended_id=frame['extended'],
            timestamp=time.time(),  # Better than nothing...
            is_remote_frame=frame['rtr'],
            dlc=frame['dlc'],
            data=frame['data'][: frame['dlc']],
            channel=frame['channel']
        )
        return msg, False

    def send(self, msg, timeout=None):
        self.interface.send(self.channel, msg.arbitration_id, bool(
            msg.is_extended_id), bool(msg.is_remote_frame), msg.dlc, msg.data)

    def shutdown(self):
        self.interface.stop()
