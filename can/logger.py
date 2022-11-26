import re
import sys
import argparse
from datetime import datetime
import errno
from typing import Any, Dict, List, Union, Sequence, Tuple

import can
from can.io import BaseRotatingLogger
from can.io.generic import MessageWriter
from . import Bus, BusState, Logger, SizedRotatingLogger
from .typechecking import CanFilter, CanFilters


def _create_base_argument_parser(parser: argparse.ArgumentParser) -> None:
    """Adds common options to an argument parser."""

    parser.add_argument(
        "-c",
        "--channel",
        help=r"Most backend interfaces require some sort of channel. For "
        r"example with the serial interface the channel might be a rfcomm"
        r' device: "/dev/rfcomm0". With the socketcan interface valid '
        r'channel examples include: "can0", "vcan0".',
    )

    parser.add_argument(
        "-i",
        "--interface",
        dest="interface",
        help="""Specify the backend CAN interface to use. If left blank,
                        fall back to reading from configuration files.""",
        choices=sorted(can.VALID_INTERFACES),
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
        help="The remaining arguments will be used for the interface and "
        "logger/player initialisation. "
        "For example, `-i vector -c 1 --app-name=MyCanApp` is the equivalent "
        "to opening the bus with `Bus('vector', channel=1, app_name='MyCanApp')",
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
        "\n      <can_id>:<can_mask> (matches when <received_can_id> & mask =="
        " can_id & mask)"
        "\n      <can_id>~<can_mask> (matches when <received_can_id> & mask !="
        " can_id & mask)"
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


def _parse_additional_config(
    unknown_args: Sequence[str],
) -> Dict[str, Union[str, int, float, bool]]:
    for arg in unknown_args:
        if not re.match(r"^--[a-zA-Z\-]*?=\S*?$", arg):
            raise ValueError(f"Parsing argument {arg} failed")

    def _split_arg(_arg: str) -> Tuple[str, str]:
        left, right = _arg.split("=", 1)
        return left.lstrip("--").replace("-", "_"), right

    args: Dict[str, Union[str, int, float, bool]] = {}
    for key, string_val in map(_split_arg, unknown_args):
        if re.match(r"^[-+]?\d+$", string_val):
            # value is integer
            args[key] = int(string_val)
        elif re.match(r"^[-+]?\d*\.\d+$", string_val):
            # value is float
            args[key] = float(string_val)
        elif re.match(r"^(?:True|False)$", string_val):
            # value is bool
            args[key] = string_val == "True"
        else:
            # value is string
            args[key] = string_val
    return args


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Log CAN traffic, printing messages to stdout or to a "
        "given file.",
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
        "-a",
        "--append",
        dest="append",
        help="Append to the log file if it already exists.",
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--file_size",
        dest="file_size",
        type=int,
        help="Maximum file size in bytes. Rotate log file when size threshold "
        "is reached. (The resulting file sizes will be consistent, but are not "
        "guaranteed to be exactly what is specified here due to the rollover "
        "conditions being logger implementation specific.)",
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
    additional_config = _parse_additional_config([*results.extra_args, *unknown_args])
    bus = _create_bus(results, can_filters=_parse_filters(results), **additional_config)

    if results.active:
        bus.state = BusState.ACTIVE
    elif results.passive:
        bus.state = BusState.PASSIVE

    print(f"Connected to {bus.__class__.__name__}: {bus.channel_info}")
    print(f"Can Logger (Started on {datetime.now()})")

    logger: Union[MessageWriter, BaseRotatingLogger]
    if results.file_size:
        logger = SizedRotatingLogger(
            base_filename=results.log_file,
            max_bytes=results.file_size,
            append=results.append,
            **additional_config,
        )
    else:
        logger = Logger(
            filename=results.log_file,
            append=results.append,
            **additional_config,
        )

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
