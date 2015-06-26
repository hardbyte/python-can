from __future__ import print_function

import can


def main():
    bus = can.interface.Bus()
    msg = can.Message(arbitration_id=0xc0ffee,
                      data=[0, 25, 0, 1, 3, 1, 4, 1],
                      extended_id=False)
    if bus.send(msg) < 0:
        print("Message NOT sent")
    else:
        print("Message sent")

if __name__ == "__main__":
    main()
