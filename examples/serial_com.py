#!/usr/bin/env python
# coding: utf-8

"""
This example sends every second a messages over the serial interface and also 
receives incoming messages.

python3 -m examples.serial_com

Expects two serial ports (/dev/ttyS10 and /dev/ttyS11) connected to each other:
    Linux:
    To connect two ports use socat.
    sudo apt-get install socat
    sudo socat PTY,link=/dev/ttyS10 PTY,link=/dev/ttyS11

    Windows:
    This example was not tested on Windows. To create and connect virtual
    ports on Windows, the following software can be used:
        com0com: http://com0com.sourceforge.net/
"""

from __future__ import print_function

import time
import threading

import can


def send_cyclic(bus, msg, stop_event):
    print("Start to send a message every 1s")
    start_time = time.time()
    while not stop_event.is_set():
        msg.timestamp = time.time() - start_time
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
    server = can.interface.Bus(bustype='serial', channel='/dev/ttyS10')
    client = can.interface.Bus(bustype='serial', channel='/dev/ttyS11')

    tx_msg = can.Message(arbitration_id=0x01, data=[0x11, 0x22, 0x33, 0x44,
                                                    0x55, 0x66, 0x77, 0x88])

    # Thread for sending and receiving messages
    stop_event = threading.Event()
    t_send_cyclic = threading.Thread(target=send_cyclic, args=(server, tx_msg,
                                                               stop_event))
    t_receive = threading.Thread(target=receive, args=(client, stop_event))
    t_receive.start()
    t_send_cyclic.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    stop_event.set()
    server.shutdown()
    client.shutdown()
    print("Stopped script")
