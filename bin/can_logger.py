#!/usr/bin/env python
"""
can_logger.py logs CAN traffic to the terminal and to a file on disk.

    can_logger.py can0

Dynamic Controls 2010
"""

import datetime
import argparse
import time

import can
from can import interfaces

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Log CAN traffic, printing messages to stdout or to a given file")


    parser.add_argument("-f", "--file_name", dest="log_file",
                        help="""Path and base log filename, extension can be .txt, .csv, .db, .npz""",
                        default=None)

    parser.add_argument("-v", action="count", dest="verbosity", 
                        help='''How much information do you want to see at the command line? 
                        You can add several of these e.g., -vv is DEBUG''', default=2)

    parser.add_argument("-i", "--interface", dest="interface",
                        help='''Which backend do you want to use?''',
                        default=can.rc['default-interface'],
                        choices=('socketcan', 'kvaser', 'serial'))
    
    parser.add_argument('channel', help='''Most backend interfaces require some sort of channel.
    For example with the serial interface the channel might be a rfcomm device: /dev/rfcomm0
    Other channel examples are: can0, vcan0''')

    results = parser.parse_args()

    if results.interface is not None:
        can.rc['interface'] = results.interface

    verbosity = results.verbosity

    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)

    from can.interfaces.interface import *

    bus = Bus(results.channel)
    print('Can Logger (Started on {})\n'.format(datetime.datetime.now()))
    notifier = can.Notifier(bus, [can.Printer(results.log_file)])

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bus.shutdown()
