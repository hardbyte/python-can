#!/usr/bin/env python3
"""
This example sends every second a messages over the serial interface and also 
receives incoming messages.

Expects a /dev/ttyACM0 interface:

    python3 -m examples.serial_com

"""

import time
import can
import threading


def time_millis():
    return int(round(time.time() * 1000))


def send_cyclic(bus, msg, stop_event):
    print("Start to send a message every 1s")
    start_time = time_millis()
    while not stop_event.is_set():
        msg.timestamp = time_millis() - start_time
        bus.send(msg)
        print("tx: {}".format(tx_msg))
        time.sleep(1)
    print("Stopped sending messages")


def receive(bus, stop_event):
    print("Start receiving messages")
    while not stop_event.is_set():
        rx_msg = bus.recv(1)
        if rx_msg is not None:
            print("rx: {}".format(rx_msg))
    print("Stopped receiving messages")

if __name__ == "__main__":
    bus = can.interface.Bus(bustype='serial', channel='/dev/ttyACM0')
    tx_msg = can.Message(arbitration_id=0x01, data=[0x11, 0x22, 0x33, 0x44,
                                                    0x55, 0x66, 0x77, 0x88])

    # Thread for sending and receiving messages
    stop_event = threading.Event()
    t_send_cyclic = threading.Thread(target=send_cyclic, args=(bus, tx_msg,
                                                               stop_event))
    t_receive = threading.Thread(target=receive, args=(bus, stop_event))
    t_receive.start()
    t_send_cyclic.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    stop_event.set()
    bus.shutdown()
    print("Stopped script")
