#!/usr/bin/env python
"""
can_logger.py logs CAN traffic to the terminal and to a file on disk.

Dynamic Controls 2010
"""

import datetime
import argparse
import time

import can
from can import interfaces

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Log CAN traffic, printing messages to stdout")


    parser.add_argument("-f", "--file_name", dest="log_file",
                        help="""Path and base log filename, extension can be .txt, .csv, .db, .npz""",
                        default=None)

    # TODO support this again
    parser.add_argument("-v", action="count", dest="verbosity", 
                        help='''How much information do you want to see at the command line? 
                        You can add several of these e.g., -vv is DEBUG''', default=2)

    
    interfaces._add_subparsers(parser)

    results = parser.parse_args()
    filename = results.log_file
    can.rc['interface'] = results.interface
    verbosity = results.verbosity
    if results.interface == "socketcan" and results.socketcan_interface != 'auto':
        can.rc['interface'] = results.interface + "_" + results.socketcan_interface

    # Assume that the desired interface deals with all command line arguments
    # in the Bus initializer.
    # Don't want to pass on the arguments we have dealt with at this level
    del results.log_file
    del results.verbosity
    del results.interface
    
    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)
    
    from can.interfaces.interface import *
    
    bus = Bus(**results.__dict__)

    log_start_time = datetime.datetime.now()

    # TODO could use this iterator api but need to deal with rx thread better
    # I'll explicitly iterate over the incoming messages, so kill the rx thread
    bus._running.clear()
    print('Can Logger (Started on {})\n'.format(log_start_time))
    for msg in bus:
        print(msg)

"""
    listener = can.Printer(filename)
    bus.listeners.append(listener)

    try:
        while  bus._running:
            # TODO detect if the bus thread has died
            time.sleep(0.5)
                
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()
"""
