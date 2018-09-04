#!/usr/bin/env python
# coding: utf-8

"""
logger.py logs CAN traffic to the terminal and to a file on disk.

    logger.py can0

See candump in the can-utils package for a C implementation.
Efficient filtering has been implemented for the socketcan backend.
For example the command

    logger.py can0 F03000:FFF000

Will filter for can frames with a can_id containing XXF03XXX.

Dynamic Controls 2010
"""

from __future__ import absolute_import, print_function

import sys
import argparse
import socket
from datetime import datetime

import can
from can import Bus, BusState, Logger


def main():
    parser = argparse.ArgumentParser(
        "python -m can.logger",
        description="Log CAN traffic, printing messages to stdout or to a given file.")

    parser.add_argument("-f", "--file_name", dest="log_file",
                        help="""Path and base log filename, for supported types see can.Logger.""",
                        default=None)

    parser.add_argument("-v", action="count", dest="verbosity",
                        help='''How much information do you want to see at the command line?
                        You can add several of these e.g., -vv is DEBUG''', default=2)

    parser.add_argument('-c', '--channel', help='''Most backend interfaces require some sort of channel.
    For example with the serial interface the channel might be a rfcomm device: "/dev/rfcomm0"
    With the socketcan interfaces valid channel examples include: "can0", "vcan0"''')

    parser.add_argument('-i', '--interface', dest="interface",
                        help='''Specify the backend CAN interface to use. If left blank,
                        fall back to reading from configuration files.''',
                        choices=can.VALID_INTERFACES)

    parser.add_argument('--filter', help='''Comma separated filters can be specified for the given CAN interface:
        <can_id>:<can_mask> (matches when <received_can_id> & mask == can_id & mask)
        <can_id>~<can_mask> (matches when <received_can_id> & mask != can_id & mask)
    ''', nargs=argparse.REMAINDER, default='')

    parser.add_argument('-b', '--bitrate', type=int,
                        help='''Bitrate to use for the CAN bus.''')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--active', help="Start the bus as active, this is applied the default.",
                       action='store_true')
    group.add_argument('--passive', help="Start the bus as passive.",
                       action='store_true')

    # print help message when no arguments wre given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        import errno
        raise SystemExit(errno.EINVAL)

    results = parser.parse_args()

    verbosity = results.verbosity

    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)

    can_filters = []
    if len(results.filter) > 0:
        print('Adding filter/s', results.filter)
        for filt in results.filter:
            if ':' in filt:
                _ = filt.split(":")
                can_id, can_mask = int(_[0], base=16), int(_[1], base=16)
            elif "~" in filt:
                can_id, can_mask = filt.split("~")
                can_id = int(can_id, base=16) | 0x20000000    # CAN_INV_FILTER
                can_mask = int(can_mask, base=16) & socket.CAN_ERR_FLAG
            can_filters.append({"can_id": can_id, "can_mask": can_mask})

    config = {"can_filters": can_filters, "single_handle": True}
    if results.interface:
        config["interface"] = results.interface
    if results.bitrate:
        config["bitrate"] = results.bitrate
    bus = Bus(results.channel, **config)

    if results.active:
        bus.state = BusState.ACTIVE

    if results.passive:
        bus.state = BusState.PASSIVE

    print('Connected to {}: {}'.format(bus.__class__.__name__, bus.channel_info))
    print('Can Logger (Started on {})\n'.format(datetime.now()))
    logger = Logger(results.log_file)

    try:
        while True:
            msg = bus.recv(1)
            if msg is not None:
                logger(msg)
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()
        logger.stop()

if __name__ == "__main__":
    main()
