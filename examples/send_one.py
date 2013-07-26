import can
can.rc['interface'] = 'socketcan_ctypes'
from can.interfaces.interface import Bus


def main():
    can_interface = 'vcan0'
    bus = Bus(can_interface)
    msg = can.Message(arbitration_id=0xc0ffee, data=[0, 25, 0, 1, 3, 1, 4, 1], extended_id=False)
    bus.send(msg)
    print("Message sent")

if __name__ == "__main__":
    main()
