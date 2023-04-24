#!/usr/bin/env python

"""
This shows how message filtering works.
"""

import time

import can


def main():
    """Send some messages to itself and apply filtering."""
    with can.Bus(interface="virtual", receive_own_messages=True) as bus:
        can_filters = [{"can_id": 1, "can_mask": 0xF, "extended": True}]
        bus.set_filters(can_filters)

        # print all incoming messages, which includes the ones sent,
        # since we set receive_own_messages to True
        # assign to some variable so it does not garbage collected
        notifier = can.Notifier(bus, [can.Printer()])  # pylint: disable=unused-variable

        bus.send(can.Message(arbitration_id=1, is_extended_id=True))
        bus.send(can.Message(arbitration_id=2, is_extended_id=True))
        bus.send(can.Message(arbitration_id=1, is_extended_id=False))

        time.sleep(1.0)


if __name__ == "__main__":
    main()
