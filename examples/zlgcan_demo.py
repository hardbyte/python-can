"""
Your project like this:
    - demo
      - main.py
      - bitrate.cfg.yaml
      - library
       - ...
"""
import can
from can.interfaces.zlgcan import ZCanTxMode, ZCANDeviceType

with can.Bus(interface="zlgcan", device_type=ZCANDeviceType.ZCAN_USBCANFD_200U,
             configs=[{'bitrate': 500000, 'resistance': 1}, {'bitrate': 500000, 'resistance': 1}]) as bus:
    bus.send(can.Message(
        arbitration_id=0x123,
        is_extended_id=False,
        channel=0,
        data=[0x01, 0x02, 0x03, ],
        dlc=3,
    ), tx_mode=ZCanTxMode.SELF_SR)

    _msg = bus.recv()
    print(_msg)

