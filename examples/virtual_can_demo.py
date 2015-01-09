"""
This demo creates multiple processes of Producers to spam a socketcan bus.
"""

import time
import logging
import concurrent.futures

import can
can.rc['interface'] = 'socketcan_native'
from can.interfaces.interface import Bus
can_interface = 'vcan0'


def producer(id):
    """:param id: Spam the bus with messages including the data id."""

    bus = Bus(can_interface)
    for i in range(16):
        msg = can.Message(arbitration_id=0x0cf02200, data=[id, i, 0, 1, 3, 1, 4, 1])
        bus.send(msg)
    # TODO Issue #3: Need to keep running to ensure the writing threads stay alive. ?
    time.sleep(2)

if __name__ == "__main__":
    #logging.getLogger('').setLevel(logging.DEBUG)
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        executor.map(producer, range(5))

time.sleep(2)
