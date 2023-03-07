#!/usr/bin/env python

import time
import can


def main():
    with can.Bus(receive_own_messages=True) as bus:
        print_listener = can.Printer()
        can.Notifier(bus, [print_listener])

        bus.send(can.Message(arbitration_id=1, is_extended_id=True))
        bus.send(can.Message(arbitration_id=2, is_extended_id=True))
        bus.send(can.Message(arbitration_id=1, is_extended_id=False))

        time.sleep(1.0)


if __name__ == "__main__":
    main()
