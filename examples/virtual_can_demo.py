#!/usr/bin/env python

"""
This demo creates multiple processes of producers to spam a socketcan bus.
"""

from time import sleep
from concurrent.futures import ProcessPoolExecutor

import can


def producer(id, message_count=16):
    """Spam the bus with messages including the data id.

    :param int id: the id of the thread/process
    """

    with can.Bus(bustype="socketcan", channel="vcan0") as bus:
        for i in range(message_count):
            msg = can.Message(
                arbitration_id=0x0CF02200 + id, data=[id, i, 0, 1, 3, 1, 4, 1]
            )
            bus.send(msg)
        sleep(1.0)

    print("Producer #{} finished sending {} messages".format(id, message_count))


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        executor.map(producer, range(5))
