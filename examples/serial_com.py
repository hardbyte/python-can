#!/usr/bin/env python

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

import time
import threading

import can


def send_cyclic(bus, msg, stop_event):
    """The loop for sending."""
    print("Start to send a message every 1s")
    start_time = time.time()
    while not stop_event.is_set():
        msg.timestamp = time.time() - start_time
        bus.send(msg)
        print(f"tx: {msg}")
        time.sleep(1)
    print("Stopped sending messages")


def receive(bus, stop_event):
    """The loop for receiving."""
    print("Start receiving messages")
    while not stop_event.is_set():
        rx_msg = bus.recv(1)
        if rx_msg is not None:
            print(f"rx: {rx_msg}")
    print("Stopped receiving messages")


def main():
    """Controls the sender and receiver."""
    with can.Bus(interface="serial", channel="/dev/ttyS10") as server:
        with can.Bus(interface="serial", channel="/dev/ttyS11") as client:
            tx_msg = can.Message(
                arbitration_id=0x01,
                data=[0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88],
            )

            # Thread for sending and receiving messages
            stop_event = threading.Event()
            t_send_cyclic = threading.Thread(
                target=send_cyclic, args=(server, tx_msg, stop_event)
            )
            t_receive = threading.Thread(target=receive, args=(client, stop_event))
            t_receive.start()
            t_send_cyclic.start()

            try:
                while True:
                    time.sleep(0)  # yield
            except KeyboardInterrupt:
                pass  # exit normally

            stop_event.set()
            time.sleep(0.5)

    print("Stopped script")


if __name__ == "__main__":
    main()
