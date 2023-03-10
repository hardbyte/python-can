#!/usr/bin/env python

"""
This example exercises the periodic sending capabilities.

Expects a vcan0 interface:

    python3 -m examples.cyclic

"""

import logging
import time

import can

logging.basicConfig(level=logging.INFO)


def simple_periodic_send(bus):
    """
    Sends a message every 20ms with no explicit timeout
    Sleeps for 2 seconds then stops the task.
    """
    print("Starting to send a message every 200ms for 2s")
    msg = can.Message(
        arbitration_id=0x123, data=[1, 2, 3, 4, 5, 6], is_extended_id=False
    )
    task = bus.send_periodic(msg, 0.20)
    assert isinstance(task, can.CyclicSendTaskABC)
    time.sleep(2)
    task.stop()
    print("stopped cyclic send")


def limited_periodic_send(bus):
    """Send using LimitedDurationCyclicSendTaskABC."""
    print("Starting to send a message every 200ms for 1s")
    msg = can.Message(
        arbitration_id=0x12345678, data=[0, 0, 0, 0, 0, 0], is_extended_id=True
    )
    task = bus.send_periodic(msg, 0.20, 1, store_task=False)
    if not isinstance(task, can.LimitedDurationCyclicSendTaskABC):
        print("This interface doesn't seem to support LimitedDurationCyclicSendTaskABC")
        task.stop()
        return

    time.sleep(2)
    print("Cyclic send should have stopped as duration expired")
    # Note the (finished) task will still be tracked by the Bus
    # unless we pass `store_task=False` to bus.send_periodic
    # alternatively calling stop removes the task from the bus
    # task.stop()


def test_periodic_send_with_modifying_data(bus):
    """Send using ModifiableCyclicTaskABC."""
    print("Starting to send a message every 200ms. Initial data is four consecutive 1s")
    msg = can.Message(arbitration_id=0x0CF02200, data=[1, 1, 1, 1])
    task = bus.send_periodic(msg, 0.20)
    if not isinstance(task, can.ModifiableCyclicTaskABC):
        print("This interface doesn't seem to support modification")
        task.stop()
        return
    time.sleep(2)
    print("Changing data of running task to begin with 99")
    msg.data[0] = 0x99
    task.modify_data(msg)
    time.sleep(2)

    task.stop()
    print("stopped cyclic send")
    print("Changing data of stopped task to single ff byte")
    msg.data = bytearray([0xFF])
    msg.dlc = 1
    task.modify_data(msg)
    time.sleep(1)
    print("starting again")
    task.start()
    time.sleep(1)
    task.stop()
    print("done")


# Will have to consider how to expose items like this. The socketcan
# interfaces will continue to support it... but the top level api won't.
# def test_dual_rate_periodic_send():
#     """Send a message 10 times at 1ms intervals, then continue to send every 500ms"""
#     msg = can.Message(arbitration_id=0x123, data=[0, 1, 2, 3, 4, 5])
#     print("Creating cyclic task to send message 10 times at 1ms, then every 500ms")
#     task = can.interface.MultiRateCyclicSendTask('vcan0', msg, 10, 0.001, 0.50)
#     time.sleep(2)
#
#     print("Changing data[0] = 0x42")
#     msg.data[0] = 0x42
#     task.modify_data(msg)
#     time.sleep(2)
#
#     task.stop()
#     print("stopped cyclic send")
#
#     time.sleep(2)
#
#     task.start()
#     print("starting again")
#     time.sleep(2)
#     task.stop()
#     print("done")


def main():
    """Test different cyclic sending tasks."""
    reset_msg = can.Message(
        arbitration_id=0x00, data=[0, 0, 0, 0, 0, 0], is_extended_id=False
    )

    # this uses the default configuration (for example from environment variables, or a
    # config file) see https://python-can.readthedocs.io/en/stable/configuration.html
    with can.Bus() as bus:
        bus.send(reset_msg)

        simple_periodic_send(bus)

        bus.send(reset_msg)

        limited_periodic_send(bus)

        test_periodic_send_with_modifying_data(bus)

        # print("Carrying out multirate cyclic test for {} interface".format(interface))
        # can.rc['interface'] = interface
        # test_dual_rate_periodic_send()

    time.sleep(2)


if __name__ == "__main__":
    main()
