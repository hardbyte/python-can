#!/usr/bin/env python
# coding: utf-8

"""
This shows how message filtering works.
"""

import time

import can

if __name__ == '__main__':
    bus = can.interface.Bus(bustype='socketcan',
                            channel='vcan0',
                            receive_own_messages=True)

    can_filters = [{"can_id": 1, "can_mask": 0xf, "extended": True}]
    bus.set_filters(can_filters)
    notifier = can.Notifier(bus, [can.Printer()])
    bus.send(can.Message(arbitration_id=1, extended_id=True))
    bus.send(can.Message(arbitration_id=2, extended_id=True))
    bus.send(can.Message(arbitration_id=1, extended_id=False))

    time.sleep(10)
