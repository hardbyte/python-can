#!/usr/bin/env python

"""
Shows how the receive messages via polling.
"""

import can
from can.bus import BusState


def receive_all():
    """Receives all messages and prints them to the console until Ctrl+C is pressed."""

    with can.interface.Bus(
        bustype="pcan", channel="PCAN_USBBUS1", bitrate=250000
    ) as bus:
        # bus = can.interface.Bus(bustype='ixxat', channel=0, bitrate=250000)
        # bus = can.interface.Bus(bustype='vector', app_name='CANalyzer', channel=0, bitrate=250000)

        # set to read-only, only supported on some interfaces
        bus.state = BusState.PASSIVE

        try:
            while True:
                msg = bus.recv(1)
                if msg is not None:
                    print(msg)

        except KeyboardInterrupt:
            pass  # exit normally


if __name__ == "__main__":
    receive_all()
