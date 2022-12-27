#!/usr/bin/env python

"""
This example exercises the periodic task's multiple message sending capabilities

Expects a vcan0 interface:

    python3 -m examples.cyclic_multiple

"""

import logging
import time

import can

logging.basicConfig(level=logging.INFO)


def cyclic_multiple_send(bus):
    """
    Sends periodic messages every 1 s with no explicit timeout
    Sleeps for 10 seconds then stops the task.
    """
    print("Starting to send a message every 1 s for 10 s")
    messages = []

    messages.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )
    )
    messages.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
            is_extended_id=False,
        )
    )
    messages.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x33, 0x33, 0x33, 0x33, 0x33, 0x33],
            is_extended_id=False,
        )
    )
    messages.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x44, 0x44, 0x44, 0x44, 0x44, 0x44],
            is_extended_id=False,
        )
    )
    messages.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x55, 0x55, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
        )
    )
    task = bus.send_periodic(messages, 1)
    assert isinstance(task, can.CyclicSendTaskABC)
    time.sleep(10)
    task.stop()
    print("stopped cyclic send")


def cyclic_multiple_send_modify(bus):
    """
    Sends initial set of 3 Messages containing Odd data sent every 1 s with
    no explicit timeout. Sleeps for 8 s.

    Then the set is updated to 3 Messages containing Even data.
    Sleeps for 10 s.
    """
    messages_odd = []
    messages_odd.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )
    )
    messages_odd.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x33, 0x33, 0x33, 0x33, 0x33, 0x33],
            is_extended_id=False,
        )
    )
    messages_odd.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x55, 0x55, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False,
        )
    )
    messages_even = []
    messages_even.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
            is_extended_id=False,
        )
    )
    messages_even.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x44, 0x44, 0x44, 0x44, 0x44, 0x44],
            is_extended_id=False,
        )
    )
    messages_even.append(
        can.Message(
            arbitration_id=0x401,
            data=[0x66, 0x66, 0x66, 0x66, 0x66, 0x66],
            is_extended_id=False,
        )
    )
    print("Starting to send a message with odd every 1 s for 8 s with odd data")
    task = bus.send_periodic(messages_odd, 1)
    assert isinstance(task, can.CyclicSendTaskABC)
    time.sleep(8)
    print("Starting to send a message with even data every 1 s for 10 s with even data")
    task.modify_data(messages_even)
    time.sleep(10)
    print("stopped cyclic modify send")


if __name__ == "__main__":
    for interface, channel in [("socketcan", "vcan0")]:
        print(f"Carrying out cyclic multiple tests with {interface} interface")

        with can.Bus(interface=interface, channel=channel, bitrate=500000) as BUS:
            cyclic_multiple_send(BUS)
            cyclic_multiple_send_modify(BUS)

    time.sleep(2)
