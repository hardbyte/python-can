#!/usr/bin/env python

"""
This example demonstrates how to send a periodic message containing
an automatically updating counter and checksum.

Expects a virtual interface:

    python3 -m examples.cyclic_checksum
"""

import logging
import time

import can

logging.basicConfig(level=logging.INFO)


def cyclic_checksum_send(bus: can.BusABC) -> None:
    """
    Sends periodic messages every 1 s with no explicit timeout.
    The message's counter and checksum is updated before each send.
    Sleeps for 10 seconds then stops the task.
    """
    message = can.Message(arbitration_id=0x78, data=[0, 1, 2, 3, 4, 5, 6, 0])
    print("Starting to send an auto-updating message every 100ms for 3 s")
    task = bus.send_periodic(msgs=message, period=0.1, modifier_callback=update_message)
    time.sleep(3)
    task.stop()
    print("stopped cyclic send")


def update_message(message: can.Message) -> None:
    counter = increment_counter(message)
    checksum = compute_xbr_checksum(message, counter)
    message.data[7] = (checksum << 4) + counter


def increment_counter(message: can.Message) -> int:
    counter = message.data[7] & 0x0F
    counter += 1
    counter %= 16

    return counter


def compute_xbr_checksum(message: can.Message, counter: int) -> int:
    """
    Computes an XBR checksum as per SAE J1939 SPN 3188.
    """
    checksum = sum(message.data[:7])
    checksum += sum(message.arbitration_id.to_bytes(length=4, byteorder="big"))
    checksum += counter & 0x0F
    xbr_checksum = ((checksum >> 4) + checksum) & 0x0F

    return xbr_checksum


if __name__ == "__main__":
    with can.Bus(channel=0, interface="virtual", receive_own_messages=True) as _bus:
        notifier = can.Notifier(bus=_bus, listeners=[print])
        cyclic_checksum_send(_bus)
        notifier.stop()
