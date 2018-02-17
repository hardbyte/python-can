"""
This demo shows a usage of an Lawicel CANUSB device.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import can

# import logging
# logging.basicConfig(level=logging.DEBUG)

serialMatcher="PID_6001"
bus = can.interface.Bus(bustype="canal", dll="canusbdrv64.dll", serialMatcher=serialMatcher, bitrate=100000, flags=4)

# alternative: specify device serial:
# bus = can.interface.Bus(bustype="canal", dll="canusbdrv64.dll", serial = "LW19ZSBR", bitrate=100000, flags=4)

def send_one():
    msg = can.Message(arbitration_id=0x00c0ffee,
                      data=[0, 25, 0, 1, 3, 1, 4, 1],
                      extended_id=True)
    try:
        bus.send(msg)
        print ("Message sent:")
        print (msg)
    except can.CanError:
        print ("ERROR: Message send failure")

def receive_one():
    print ("Wait for CAN message...")
    try:
        # blocking receive
        msg = bus.recv(timeout=0)
        if msg:
            print ("Message received:")
            print (msg)
        else:
            print ("ERROR: Unexpected bus.recv reply")

    except can.CanError:
        print ("ERROR: Message not received")

def demo():
    print ("=====  CANAL interface demo =====")
    print ("Device: {}".format(bus.channel_info))
    send_one()
    receive_one()

if __name__ == '__main__':
    demo()
