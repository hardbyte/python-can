#!/usr/bin/env python
import logging
logging.basicConfig(format='%(asctime)-15s %(message)s')
import argparse
import can
from can.interfaces import remote


def main():
    parser = argparse.ArgumentParser(description="Remote CAN server")

    parser.add_argument('-v', action='count', dest="verbosity",
                        help='''How much information do you want to see at the command line?
                        You can add several of these e.g., -vv is DEBUG''', default=3)

    parser.add_argument('-c', '--channel', help='''Most backend interfaces require some sort of channel.
    For example with the serial interface the channel might be a rfcomm device: "/dev/rfcomm0"
    With the socketcan interfaces valid channel examples include: "can0", "vcan0".
    The server will only serve this channel. Start additional servers at different
    ports to share more channels.''')

    parser.add_argument('-i', '--interface',
                        help='''Specify the backend CAN interface to use. If left blank,
                        fall back to reading from configuration files.''',
                        choices=can.interface.VALID_INTERFACES)

    parser.add_argument('-b', '--bitrate', type=int,
                        help='''Force to use a specific bitrate.
                        This will override any requested bitrate by the clients.''')

    parser.add_argument('-H', '--host',
                        help='''Host to listen to (default 0.0.0.0).''',
                        default='0.0.0.0')

    parser.add_argument('-p', '--port', type=int,
                        help='''TCP port to listen on (default %d).''' % remote.DEFAULT_PORT,
                        default=remote.DEFAULT_PORT)

    results = parser.parse_args()

    verbosity = results.verbosity
    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)

    config = {}
    if results.channel:
        config["channel"] = results.channel
    if results.interface:
        config["bustype"] = results.interface
    if results.bitrate:
        config["bitrate"] = results.bitrate

    server = remote.RemoteServer(results.host, results.port, **config)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    logging.info("Closing server")
    server.shutdown()


if __name__ == "__main__":
    main()
