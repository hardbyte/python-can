#!/usr/bin/env python3
"""
This example exercises the periodic sending capabilities.

Expects a vcan0 interface:

    python3 -m examples.cyclic

"""

import logging
import time

import can
logging.basicConfig(level=logging.INFO)


channel = 'vcan0'



def test_simple_periodic_send():
    print("Trying to send a message...")
    msg = can.Message(arbitration_id=0x0cf02200, data=[0, 1, 3, 1, 4, 1])
    task = can.send_periodic('vcan0', msg, 0.020)
    time.sleep(2)

    print("Trying to change data")
    msg.data[0] = 99
    task.modify_data(msg)
    time.sleep(2)

    task.stop()
    print("stopped cyclic send")

    time.sleep(1)
    task.start()
    print("starting again")
    time.sleep(1)
    print("done")


def test_dual_rate_periodic_send():
    """Send a message 10 times at 1ms intervals, then continue to send every 500ms"""
    msg = can.Message(arbitration_id=0x0c112200, data=[0, 1, 2, 3, 4, 5])
    print("Creating cyclic task to send message 10 times at 1ms, then every 500ms")
    task = can.interface.MultiRateCyclicSendTask('vcan0', msg, 10, 0.001, 0.50)
    time.sleep(2)

    print("Changing data[0] = 0x42")
    msg.data[0] = 0x42
    task.modify_data(msg)
    time.sleep(2)

    task.stop()
    print("stopped cyclic send")

    time.sleep(2)

    task.start()
    print("starting again")
    time.sleep(2)
    print("done")


if __name__ == "__main__":

    for interface in {'socketcan_ctypes', 'socketcan_native'}:
        print("Carrying out cyclic tests with {} interface".format(interface))
        can.rc['interface'] = interface
        test_simple_periodic_send()


    for interface in {'socketcan_ctypes', }:
        print("Carrying out cyclic tests with {} interface".format(interface))
        can.rc['interface'] = interface
        test_dual_rate_periodic_send()

    print("socketcan_native doesn't yet support MultiRate Cyclic Tasks")