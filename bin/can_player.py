#!/usr/bin/env python
"""
can_player.py replays CAN traffic saved with can_logger.py back
to a CAN bus.

Similar to canplayer in the can-utils package.
"""
from __future__ import print_function
import datetime
import argparse
import time
import socket

import can

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Replay CAN traffic")

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
                        choices=can.interface.VALID_INTERFACES)


    parser.add_argument('--ignore-timestamps', dest='timestamps',
                        help='''Ignore timestamps (send all frames immediately with minimum gap between
    frames)''', action='store_false')

    parser.add_argument('-g', '--gap', type=float, help='''<ms> minimum time between replayed frames''')
    parser.add_argument('-s', '--skip', type=float, default=60*60*24,
                        help='''<s> skip gaps greater than 's' seconds''')

    parser.add_argument('infile', metavar='input-file', type=str,
                        help='The file to replay. Supported types: .db')

    results = parser.parse_args()

    verbosity = results.verbosity
    gap = 0.0001 if results.gap is None else results.gap

    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)

    bus = can.interface.Bus(results.channel, bustype=results.interface)

    # TODO refactor all sqlite specifics out
    def create_frame_from_db_tuple(frame_data):
        ts, id, is_extended, is_remote, is_error, dlc, data = frame_data
        return can.Message(
            ts, is_remote, is_extended, is_error, id, dlc, data
        )

    def iterate_all_messages(c):
        for frame_data in c.execute("SELECT * FROM messages"):
            yield create_frame_from_db_tuple(frame_data)


    import sqlite3
    conn = sqlite3.connect(results.infile)
    c = conn.cursor()
    c.execute("SELECT ts FROM messages LIMIT 1")
    recorded_start_time = c.fetchone()[0]

    print('Can Player (Started on {})'.format(datetime.datetime.now()))
    print('Replaying data from {}'.format(datetime.datetime.fromtimestamp(recorded_start_time)))

    try:
        playback_start_time = time.time()
        for m in iterate_all_messages(c):
            if results.timestamps:
                # Work out the correct wait time
                now = time.time()
                current_offset = now - playback_start_time
                recorded_offset_from_start = m.timestamp - recorded_start_time
                remaining_gap = recorded_offset_from_start - current_offset

                sleep_period = max(gap, min(results.skip, remaining_gap))
            else:
                sleep_period = gap
                time.sleep(sleep_period)

            bus.send(m)

    except KeyboardInterrupt:
        bus.shutdown()

