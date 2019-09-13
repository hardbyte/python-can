"""
Replays CAN traffic saved with can.logger back
to a CAN bus.

Similar to canplayer in the can-utils package.
"""

import sys
import argparse
from datetime import datetime

import can
from can import Bus, LogReader, MessageSync


def main():
    parser = argparse.ArgumentParser(
        "python -m can.player", description="Replay CAN traffic."
    )

    parser.add_argument(
        "-f",
        "--file_name",
        dest="log_file",
        help="""Path and base log filename, for supported types see can.LogReader.""",
        default=None,
    )

    parser.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        help="""Also print can frames to stdout.
                        You can add several of these to enable debugging""",
        default=2,
    )

    parser.add_argument(
        "-c",
        "--channel",
        help='''Most backend interfaces require some sort of channel.
    For example with the serial interface the channel might be a rfcomm device: "/dev/rfcomm0"
    With the socketcan interfaces valid channel examples include: "can0", "vcan0"''',
    )

    parser.add_argument(
        "-i",
        "--interface",
        dest="interface",
        help="""Specify the backend CAN interface to use. If left blank,
                        fall back to reading from configuration files.""",
        choices=can.VALID_INTERFACES,
    )

    parser.add_argument(
        "-b", "--bitrate", type=int, help="""Bitrate to use for the CAN bus."""
    )

    parser.add_argument("--fd", help="Activate CAN-FD support", action="store_true")

    parser.add_argument(
        "--data_bitrate",
        type=int,
        help="""Bitrate to use for the data phase in case of CAN-FD.""",
    )

    parser.add_argument(
        "--ignore-timestamps",
        dest="timestamps",
        help="""Ignore timestamps (send all frames immediately with minimum gap between frames)""",
        action="store_false",
    )

    parser.add_argument(
        "--error-frames",
        help="Also send error frames to the interface.",
        action="store_true",
    )

    parser.add_argument(
        "-g",
        "--gap",
        type=float,
        help="""<s> minimum time between replayed frames""",
        default=0.0001,
    )
    parser.add_argument(
        "-s",
        "--skip",
        type=float,
        default=60 * 60 * 24,
        help="""<s> skip gaps greater than 's' seconds""",
    )

    parser.add_argument(
        "infile",
        metavar="input-file",
        type=str,
        help="The file to replay. For supported types see can.LogReader.",
    )

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        import errno

        raise SystemExit(errno.EINVAL)

    results = parser.parse_args()

    verbosity = results.verbosity

    logging_level_name = ["critical", "error", "warning", "info", "debug", "subdebug"][
        min(5, verbosity)
    ]
    can.set_logging_level(logging_level_name)

    error_frames = results.error_frames

    config = {"single_handle": True}
    if results.interface:
        config["interface"] = results.interface
    if results.bitrate:
        config["bitrate"] = results.bitrate
    if results.fd:
        config["fd"] = True
    if results.data_bitrate:
        config["data_bitrate"] = results.data_bitrate
    bus = Bus(results.channel, **config)

    reader = LogReader(results.infile)

    in_sync = MessageSync(
        reader, timestamps=results.timestamps, gap=results.gap, skip=results.skip
    )

    print(f"Can LogReader (Started on {datetime.now()})")

    try:
        for m in in_sync:
            if m.is_error_frame and not error_frames:
                continue
            if verbosity >= 3:
                print(m)
            bus.send(m)
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()
        reader.stop()


if __name__ == "__main__":
    main()
