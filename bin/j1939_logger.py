from __future__ import print_function

import argparse
import datetime
import textwrap
import json

import can


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Log J1939 traffic, printing messages to stdout or to a given file",
        epilog="""Pull requests welcome!
        https://bitbucket.org/hardbyte/python-can""",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-v", action="count", dest="verbosity",
                        help='''
    How much information do you want to see at the command line?
    You can add several of these e.g., -vv is DEBUG''', default=2)

    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument('--pgn',
                              help=textwrap.dedent('''
    Only listen for messages with given Parameter Group Number (PGN).
    Can be used more than once. Give either hex 0xEE00 or decimal 60928'''), action="append")

    filter_group.add_argument('--source', help=textwrap.dedent('''
    Only listen for messages from the given Source address
    Can be used more than once. Give either hex 0x0E or decimal.'''), action="append")

    filter_group.add_argument('--filter',
                              type=argparse.FileType('r'),
                              help=textwrap.dedent('''
    A json file with more complicated filtering rules.

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
    parser.add_argument('-c', '--channel', default=can.rc['channel'],
                        help=textwrap.dedent('''
    Most backend interfaces require some sort of channel. For example with the serial
    interface the channel might be a rfcomm device: /dev/rfcomm0
    Other channel examples are: can0, vcan0'''))

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

    bus = j1939.Bus(channel='can0', j1939_filters=filters)
    log_start_time = datetime.datetime.now()
    print('can.j1939 logger started on {}\n'.format(log_start_time))

    try:
        for msg in bus:
            print(msg)
    except KeyboardInterrupt:
        bus.shutdown()
        print()
