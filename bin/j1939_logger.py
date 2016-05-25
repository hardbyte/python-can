from __future__ import print_function

import argparse
import datetime
import textwrap
import json

import can


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""\
        Log J1939 traffic, printing messages to stdout or to a given file.

        Values for SOURCE and PGN can be provided as either hex or decimals.
        e.g. 0xEE00 or 60928

        The interface or channel can also be loaded from
        a configuration file - see the README for detail.
        """),
        epilog="""Pull requests and issues
        https://bitbucket.org/hardbyte/python-can""",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-v", action="count", dest="verbosity",
                        help=textwrap.dedent('''\
    command line verbosity
    How much information do you want to see at the command line?
    You can add several of these e.g., -vv is DEBUG'''), default=2)

    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument('--pgn',
                              help=textwrap.dedent('''\
    Filter messages with given Parameter Group Number (PGN).
    Can be passed multiple times. Only messages that match will
    be logged.'''), action="append")

    filter_group.add_argument('--source', help=textwrap.dedent('''\
    Only listen for messages from the given Source address
    Can be used more than once.'''), action="append")

    filter_group.add_argument('--filter',
                              type=argparse.FileType('r'),
                              help=textwrap.dedent('''\
    Provide a json file with filtering rules.

    An example file that subscribes to all messages from SRC=0
    and two particular PGNs from SRC=1:

    [
      {
        "source": 1,
        "pgn": 61475
      }
      {
        "source": 1,
        "pgn": 61474
      }
      {
        "source": 0
      }
    ]

    '''))

    parser.add_argument('-c', '--channel',
                        help=textwrap.dedent('''\
    Most backend interfaces require some sort of channel.
    For example with the serial interface the channel might be a rfcomm device: "/dev/rfcomm0"
    With the socketcan interfaces valid channel examples include: "can0", "vcan0".

    Alternatively the CAN_CHANNEL environment variable can be set.
    '''))

    parser.add_argument('-i', '--interface', dest="interface",
                        #choices=can.interface.VALID_INTERFACES,
                        help=textwrap.dedent('''\
    Specify the backend CAN interface to use.

    Valid choices:
        {}

    Alternatively the CAN_INTERFACE environment variable can be set.
    '''.format(can.interface.VALID_INTERFACES)))

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_arguments()

    verbosity = args.verbosity
    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)

    from can.interfaces.interface import *
    from can.protocols import j1939

    filters = []
    if args.pgn is not None:
        print('Have to filter pgns: ', args.pgn)
        for pgn in args.pgn:
            if pgn.startswith('0x'):
                pgn = int(pgn[2:], base=16)

            filters.append({'pgn': int(pgn)})
    if args.source is not None:
        for src in args.source:
            if src.startswith("0x"):
                src = int(src[2:], base=16)
            filters.append({"source": int(src)})
    if args.filter is not None:
        filters = json.load(args.filter)
        #print("Loaded filters from file: ", filters)

    bus = j1939.Bus(channel=args.channel, bustype=args.interface, j1939_filters=filters)
    log_start_time = datetime.datetime.now()
    print('can.j1939 logger started on {}\n'.format(log_start_time))

    try:
        for msg in bus:
            print(msg)
    except KeyboardInterrupt:
        bus.shutdown()
        print()
