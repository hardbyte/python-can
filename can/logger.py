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

import sys
import argparse
from datetime import datetime
import errno
from typing import Any, Dict, List, Union

import can
from . import Bus, BusState, Logger, SizedRotatingLogger
from .typechecking import CanFilter, CanFilters


def _create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Adds common options to an argument parser."""

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
        "-b", "--bitrate", type=int, help="Bitrate to use for the CAN bus."
    )

    parser.add_argument("--fd", help="Activate CAN-FD support", action="store_true")

    parser.add_argument(
        "--data_bitrate",
        type=int,
        help="Bitrate to use for the data phase in case of CAN-FD.",
    )

    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="""\
        The remaining arguments will be used for the interface initialisation.
        For example, `-i vector -c 1 --app-name=MyCanApp` is the equivalent to 
        opening the bus with `Bus('vector', channel=1, app_name='MyCanApp')`
        """,
    )


def _append_filter_argument(
    parser: Union[
        argparse.ArgumentParser,
        argparse._ArgumentGroup,  # pylint: disable=protected-access
    ],
    *args: str,
    **kwargs: Any,
) -> None:
    """Adds the ``filter`` option to an argument parser."""

    parser.add_argument(
        *args,
        "--filter",
        help="R|Space separated CAN filters for the given CAN interface:"
        "\n      <can_id>:<can_mask> (matches when <received_can_id> & mask == can_id & mask)"
        "\n      <can_id>~<can_mask> (matches when <received_can_id> & mask != can_id & mask)"
        "\nFx to show only frames with ID 0x100 to 0x103 and 0x200 to 0x20F:"
        "\n      python -m can.viewer -f 100:7FC 200:7F0"
        "\nNote that the ID and mask are always interpreted as hex values",
        metavar="{<can_id>:<can_mask>,<can_id>~<can_mask>}",
        nargs=argparse.ONE_OR_MORE,
        default="",
        **kwargs,
    )


def _create_bus(parsed_args: Any, **kwargs: Any) -> can.Bus:
    logging_level_names = ["critical", "error", "warning", "info", "debug", "subdebug"]
    can.set_logging_level(logging_level_names[min(5, parsed_args.verbosity)])

    config: Dict[str, Any] = {"single_handle": True, **kwargs}
    if parsed_args.interface:
        config["interface"] = parsed_args.interface
    if parsed_args.bitrate:
        config["bitrate"] = parsed_args.bitrate
    if parsed_args.fd:
        config["fd"] = True
    if parsed_args.data_bitrate:
        config["data_bitrate"] = parsed_args.data_bitrate

    return Bus(parsed_args.channel, **config)  # type: ignore


def _parse_filters(parsed_args: Any) -> CanFilters:
    can_filters: List[CanFilter] = []

    if parsed_args.filter:
        print(f"Adding filter(s): {parsed_args.filter}")
        for filt in parsed_args.filter:
            if ":" in filt:
                parts = filt.split(":")
                can_id = int(parts[0], base=16)
                can_mask = int(parts[1], base=16)
            elif "~" in filt:
                parts = filt.split("~")
                can_id = int(parts[0], base=16) | 0x20000000  # CAN_INV_FILTER
                can_mask = int(parts[1], base=16) & 0x20000000  # socket.CAN_ERR_FLAG
            else:
                raise argparse.ArgumentError(None, "Invalid filter argument")
            can_filters.append({"can_id": can_id, "can_mask": can_mask})

    return can_filters


def _parse_additonal_config(unknown_args):
    return dict(
        (arg.split("=", 1)[0].lstrip("--").replace("-", "_"), arg.split("=", 1)[1])
        for arg in unknown_args
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Log CAN traffic, printing messages to stdout or to a given file.",
    )

    _create_base_argument_parser(parser)

    parser.add_argument(
        "-f",
        "--file_name",
        dest="log_file",
        help="Path and base log filename, for supported types see can.Logger.",
        default=None,
    )

    parser.add_argument(
        "-s",
        "--file_size",
        dest="file_size",
        type=int,
        help="Maximum file size in bytes. Rotate log file when size threshold is reached.",
        default=None,
    )

    parser.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        help="""How much information do you want to see at the command line?
                        You can add several of these e.g., -vv is DEBUG""",
        default=2,
    )

    _append_filter_argument(parser)

    state_group = parser.add_mutually_exclusive_group(required=False)
    state_group.add_argument(
        "--active",
        help="Start the bus as active, this is applied by default.",
        action="store_true",
    )
    state_group.add_argument(
        "--passive", help="Start the bus as passive.", action="store_true"
    )

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    results, unknown_args = parser.parse_known_args()
    additional_config = _parse_additonal_config(unknown_args)
    bus = _create_bus(results, can_filters=_parse_filters(results), **additional_config)

    if results.active:
        bus.state = BusState.ACTIVE
    elif results.passive:
        bus.state = BusState.PASSIVE

    print(f"Connected to {bus.__class__.__name__}: {bus.channel_info}")
    print(f"Can Logger (Started on {datetime.now()})")

    if results.file_size:
        logger = SizedRotatingLogger(
            base_filename=results.log_file, max_bytes=results.file_size
        )
    else:
        logger = Logger(filename=results.log_file)  # type: ignore

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
