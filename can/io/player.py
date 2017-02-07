#!/usr/bin/env python
"""
player.py replays CAN traffic saved with logger.py back
to a CAN bus.

Similar to canplayer in the can-utils package.
"""
from __future__ import print_function
import datetime
import argparse

import can
from .blf import BLFReader
from .sqlite import SqlReader


class LogReader(object):
    """
    Replay logged CAN messages from a file.

    The format is determined from the file format which can be one of:
      * .asc
      * .blf
      * .csv
      * .db

    Exposes a simple iterator interface, to use simply:

        >>> for m in LogReader(my_file):
        ...     print(m)

    Note there are no time delays, if you want to reproduce
    the measured delays between messages look at the
    :class:`can.util.MessageSync` class.
    """

    @classmethod
    def __new__(cls, other, filename):
        if filename.endswith(".blf"):
            return BLFReader(filename)
        if filename.endswith(".db"):
            return SqlReader(filename)
        raise NotImplementedError("No read support for this log format")


class MessageSync(object):

    def __init__(self, messages, timestamps=True, gap=0.0001, skip=60):
        """

        :param messages: An iterable of :class:`can.Message` instances.
        :param timestamps: Use the messages' timestamps.
        :param gap: Minimum time between sent messages
        :param skip: Skip periods of inactivity greater than this.
        """
        self.raw_messages = messages
        self.timestamps = timestamps
        self.gap = gap
        self.skip = skip

    def __iter__(self):
        log.debug("Iterating over messages at real speed")
        playback_start_time = time.time()
        recorded_start_time = None

        for m in self.raw_messages:
            if recorded_start_time is None:
                recorded_start_time = m.timestamp

            if self.timestamps:
                # Work out the correct wait time
                now = time.time()
                current_offset = now - playback_start_time
                recorded_offset_from_start = m.timestamp - recorded_start_time
                remaining_gap = recorded_offset_from_start - current_offset

                sleep_period = max(self.gap, min(self.skip, remaining_gap))
            else:
                sleep_period = self.gap

            time.sleep(sleep_period)
            yield m


def main():
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

    parser.add_argument('-b', '--bitrate', type=int,
                        help='''Bitrate to use for the CAN bus.''')

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

    config = {}
    if results.interface:
        config["bustype"] = results.interface
    if results.bitrate:
        config["bitrate"] = results.bitrate
    bus = can.interface.Bus(results.channel, **config)

    player = LogReader(results.infile)

    in_sync = MessageSync(player, timestamps=True, skip=results.skip)

    print('Can LogReader (Started on {})'.format(
        datetime.datetime.now()))

    try:
        for m in in_sync:
            bus.send(m)
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()


if __name__ == "__main__":
    main()
