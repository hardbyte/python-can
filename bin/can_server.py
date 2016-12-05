#!/usr/bin/env python
import logging
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
import argparse
import can
from can.interfaces import remote

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remote CAN server")

    parser.add_argument('-v', action='count', dest="verbosity",
                        help='''How much information do you want to see at the command line?
                        You can add several of these e.g., -vv is DEBUG''', default=2)

    parser.add_argument('-c', '--channel', help='''Most backend interfaces require some sort of channel.
    For example with the serial interface the channel might be a rfcomm device: "/dev/rfcomm0"
    With the socketcan interfaces valid channel examples include: "can0", "vcan0"''')

    parser.add_argument('-i', '--interface',
                        help='''Specify the backend CAN interface to use. If left blank,
                        fall back to reading from configuration files.''',
                        choices=can.interface.VALID_INTERFACES)

    parser.add_argument('-p', '--port', type=int,
                        help='''TCP port to listen on (default %d).''' % remote.DEFAULT_PORT,
                        default=remote.DEFAULT_PORT)

    results = parser.parse_args()

    verbosity = results.verbosity
    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)

    server = remote.RemoteServer(results.port,
                                 channel=results.channel,
                                 bustype=results.interface)
    server.start()
