import datetime
import argparse

import can
from can import interfaces
from can.protocols import j1939

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log CAN traffic, printing messages to stdout")
    
    interfaces._add_subparsers(parser)
    results = parser.parse_args()
    can.rc['interface'] = results.interface
    
    from can.interfaces.interface import *
    bus = Bus(**results.__dict__)