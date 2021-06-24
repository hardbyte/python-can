"""
Interface for CANtact devices from Linklayer Labs
"""

import time
import logging
from unittest.mock import Mock

from can import BusABC, Message

logger = logging.getLogger(__name__)

try:
    import cantact
except ImportError:
    logger.warning(
        "The CANtact module is not installed. Install it using `python3 -m pip install cantact`"
    )


class CantactBus(BusABC):
    """CANtact interface"""

    @staticmethod
    def _detect_available_configs():
        try:
            interface = cantact.Interface()
        except (NameError, SystemError):
            # couldn't import cantact, so no configurations are available
            return []

        channels = []
        for i in range(0, interface.channel_count()):
            channels.append({"interface": "cantact", "channel": "ch:%d" % i})
        return channels

    def __init__(
        self,
        channel,
        bitrate=500000,
        poll_interval=0.01,
        monitor=False,
        bit_timing=None,
        _testing=False,
        **kwargs
    ):
        """
        :param int channel:
            Channel number (zero indexed, labeled on multi-channel devices)
        :param int bitrate:
            Bitrate in bits/s
        :param bool monitor:
            If true, operate in listen-only monitoring mode
        :param BitTiming bit_timing
            Optional BitTiming to use for custom bit timing setting. Overrides bitrate if not None.
        """

        if _testing:
            self.interface = MockInterface()
        else:
            self.interface = cantact.Interface()

        self.channel = int(channel)
        self.channel_info = "CANtact: ch:%s" % channel

        # configure the interface
        if bit_timing is None:
            # use bitrate
            self.interface.set_bitrate(int(channel), int(bitrate))
        else:
            # use custom bit timing
            self.interface.set_bit_timing(
                int(channel),
                int(bit_timing.brp),
                int(bit_timing.tseg1),
                int(bit_timing.tseg2),
                int(bit_timing.sjw),
            )
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
            arbitration_id=frame["id"],
            is_extended_id=frame["extended"],
            timestamp=frame["timestamp"],
            is_remote_frame=frame["rtr"],
            dlc=frame["dlc"],
            data=frame["data"][: frame["dlc"]],
            channel=frame["channel"],
            is_rx=(not frame["loopback"]),  # received if not loopback frame
        )
        return msg, False

    def send(self, msg, timeout=None):
        self.interface.send(
            self.channel,
            msg.arbitration_id,
            bool(msg.is_extended_id),
            bool(msg.is_remote_frame),
            msg.dlc,
            msg.data,
        )

    def shutdown(self):
        self.interface.stop()


def mock_recv(timeout):
    if timeout > 0:
        frame = {}
        frame["id"] = 0x123
        frame["extended"] = False
        frame["timestamp"] = time.time()
        frame["loopback"] = False
        frame["rtr"] = False
        frame["dlc"] = 8
        frame["data"] = [1, 2, 3, 4, 5, 6, 7, 8]
        frame["channel"] = 0
        return frame
    else:
        # simulate timeout when timeout = 0
        return None


class MockInterface:
    """
    Mock interface to replace real interface when testing.
    This allows for tests to run without actual hardware.
    """

    start = Mock()
    set_bitrate = Mock()
    set_bit_timing = Mock()
    set_enabled = Mock()
    set_monitor = Mock()
    start = Mock()
    stop = Mock()
    send = Mock()
    channel_count = Mock(return_value=1)

    recv = Mock(side_effect=mock_recv)
