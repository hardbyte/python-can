#!/usr/bin/env python

"""
This example exercises the periodic task's multiple message sending capabilities
to send a message containing a counter and a checksum.

Expects a vcan0 interface:

    python3 -m examples.crc

"""

import logging
import time

import can

logging.basicConfig(level=logging.INFO)


def crc_send(bus):
    """
    Sends periodic messages every 1 s with no explicit timeout. Modifies messages
    after 8 seconds, sends for 10 more seconds, then stops.
    """
    msg = can.Message(arbitration_id=0x12345678, data=[1, 2, 3, 4, 5, 6, 7, 0])
    messages = build_crc_msgs(msg)

    print(
        "Starting to send a message with updating counter and checksum every 1 s for 8 s"
    )
    task = bus.send_periodic(messages, 1)
    assert isinstance(task, can.CyclicSendTaskABC)
    time.sleep(8)

    msg = can.Message(arbitration_id=0x12345678, data=[8, 9, 10, 11, 12, 13, 14, 0])
    messages = build_crc_msgs(msg)

    print("Sending modified message data every 1 s for 10 s")
    task.modify_data(messages)
    time.sleep(10)
    task.stop()
    print("stopped cyclic send")


def build_crc_msgs(msg):
    """
    Using the input message as base, create 16 messages with SAE J1939 SPN 3189 counters
    and SPN 3188 checksums placed in the final byte.
    """
    messages = []

    for counter in range(16):
        checksum = compute_xbr_checksum(msg, counter)
        msg.data[7] = counter + (checksum << 4)
        messages.append(
            can.Message(arbitration_id=msg.arbitration_id, data=msg.data[:])
        )

    return messages


def compute_xbr_checksum(message, counter):
    """
    Computes an XBR checksum per SAE J1939 SPN 3188.
    """
    checksum = sum(message.data[:7])
    checksum += sum(message.arbitration_id.to_bytes(length=4, byteorder="big"))
    checksum += counter & 0x0F
    xbr_checksum = ((checksum >> 4) + checksum) & 0x0F

    return xbr_checksum


if __name__ == "__main__":
    for interface, channel in [("socketcan", "vcan0")]:
        print(f"Carrying out crc test with {interface} interface")

        with can.Bus(interface=interface, channel=channel, bitrate=500000) as BUS:
            crc_send(BUS)

    time.sleep(2)
