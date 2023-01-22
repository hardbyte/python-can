#!/usr/bin/env python

"""
This demo creates multiple processes of producers to spam a socketcan bus.
"""

from time import sleep
from concurrent.futures import ProcessPoolExecutor

import can


def producer(thread_id: int, message_count: int = 16) -> None:
    """Spam the bus with messages including the data id.

    :param thread_id: the id of the thread/process
    :param message_count: the number of messages that shall be sent
    """

    # this uses the default configuration (for example from environment variables, or a
    # config file) see https://python-can.readthedocs.io/en/stable/configuration.html
    with can.Bus() as bus:
        for i in range(message_count):
            msg = can.Message(
                arbitration_id=0x0CF02200 + thread_id,
                data=[thread_id, i, 0, 1, 3, 1, 4, 1],
            )
            bus.send(msg)
        sleep(1.0)

    print(f"Producer #{thread_id} finished sending {message_count} messages")


if __name__ == "__main__":
    with ProcessPoolExecutor() as executor:
        executor.map(producer, range(5))
