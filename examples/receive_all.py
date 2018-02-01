from __future__ import print_function

import can
from can.bus import BusState


def receive_all():
    bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000)
    # bus = can.interface.Bus(bustype='ixxat', channel=0, bitrate=250000)
    # bus = can.interface.Bus(bustype='vector', app_name='CANalyzer', channel=0, bitrate=250000)

    # active mode
    # bus.state = BusState.OPERATIONAL

    # currently only implemented for pcan
    # passive mode
    bus.state = BusState.LISTEN_ONLY

    try:
        while True:
            msg = bus.recv(1)
            if msg is not None:
                print(msg)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    receive_all()
