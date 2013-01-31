import datetime
import argparse

import can
can.rc['interface'] = 'socketcan_native'
from can import interfaces
from can.interfaces import interface
from can.protocols import j1939
b = j1939.Bus(channel='vcan0')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log CAN traffic, printing messages to stdout")
    
    interfaces._add_subparsers(parser)
    results = parser.parse_args()
    can.rc['interface'] = results.interface
    
    from can.interfaces.interface import *
    from can.protocols import j1939

    bus = Bus(**results.__dict__)