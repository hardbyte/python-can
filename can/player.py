#!/usr/bin/env python
"""
Replays CAN traffic saved with can.logger back
to a CAN bus.

Similar to canplayer in the can-utils package.
"""
from __future__ import print_function
import argparse
import datetime

import can
from can.io.player import LogReader, MessageSync


def main():
    parser = argparse.ArgumentParser(
        "python -m can.player",
        description="Replay CAN traffic")

    parser.add_argument("-f", "--file_name", dest="log_file",
                        help="""Path and base log filename, extension can be .txt, .asc, .csv, .db, .npz""",
                        default=None)

    parser.add_argument("-v", action="count", dest="verbosity",
                        help='''Also print can frames to stdout.
                        You can add several of these to enable debugging''', default=2)

    parser.add_argument('-c', '--channel',
                        help='''Most backend interfaces require some sort of channel.
    For example with the serial interface the channel might be a rfcomm device: "/dev/rfcomm0"
    With the socketcan interfaces valid channel examples include: "can0", "vcan0"''')

    parser.add_argument('-i', '--interface', dest="interface",
                        help='''Specify the backend CAN interface to use. If left blank,
                        fall back to reading from configuration files.''',
                        choices=can.VALID_INTERFACES)

    parser.add_argument('-b', '--bitrate', type=int,
                        help='''Bitrate to use for the CAN bus.''')

    parser.add_argument('--ignore-timestamps', dest='timestamps',
                        help='''Ignore timestamps (send all frames immediately with minimum gap between
    frames)''', action='store_false')

    parser.add_argument('-g', '--gap', type=float, help='''<s> minimum time between replayed frames''')
    parser.add_argument('-s', '--skip', type=float, default=60*60*24,
                        help='''<s> skip gaps greater than 's' seconds''')

    parser.add_argument('infile', metavar='input-file', type=str,
                        help='The file to replay. Supported types: .db, .blf')

    results = parser.parse_args()

    verbosity = results.verbosity
    gap = 0.0001 if results.gap is None else results.gap

    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)

    config = {"single_handle": True}
    if results.interface:
        config["bustype"] = results.interface
    if results.bitrate:
        config["bitrate"] = results.bitrate
    bus = can.interface.Bus(results.channel, **config)

    player = LogReader(results.infile)

    in_sync = MessageSync(player, timestamps=results.timestamps,
                          gap=gap, skip=results.skip)

    print('Can LogReader (Started on {})'.format(
        datetime.datetime.now()))

    try:
        for m in in_sync:
            if verbosity >= 3:
                print(m)
            bus.send(m)
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()


if __name__ == "__main__":
    main()
