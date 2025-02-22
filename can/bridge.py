"""
Creates a bridge between two CAN busses.

This will connect to two CAN busses. Messages received on one
bus will be sent to the other bus and vice versa.
"""

import argparse
import errno
import sys
from datetime import datetime

from .logger import _create_base_argument_parser, _create_bus, _parse_additional_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge two CAN busses.")

    _create_base_argument_parser(parser)

    parser.add_argument(
        "--error-frames",
        help="Also send error frames to the interface.",
        action="store_true",
    )

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    results, unknown_args = parser.parse_known_args()
    additional_config = _parse_additional_config([*results.extra_args, *unknown_args])

    verbosity = results.verbosity

    error_frames = results.error_frames

    with _create_bus(results, **additional_config) as bus_a
        with _create_bus(results, **additional_config) as bus_b
            print(f"CAN Bridge (Started on {datetime.now()})")

    print(f"CAN Bridge (Stopped on {datetime.now()})")


if __name__ == "__main__":
    main()
