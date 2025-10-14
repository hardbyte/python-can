"""
Replays CAN traffic saved with can.logger back
to a CAN bus.

Similar to canplayer in the can-utils package.
"""

import argparse
import errno
import math
import sys
from datetime import datetime
from typing import TYPE_CHECKING, cast

from can import LogReader, MessageSync
from can.cli import (
    _add_extra_args,
    _parse_additional_config,
    _set_logging_level_from_namespace,
    add_bus_arguments,
    create_bus_from_namespace,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from can import Message


def _parse_loop(value: str) -> int | float:
    """Parse the loop argument, allowing integer or 'i' for infinite."""
    if value == "i":
        return float("inf")
    try:
        return int(value)
    except ValueError as exc:
        err_msg = "Loop count must be an integer or 'i' for infinite."
        raise argparse.ArgumentTypeError(err_msg) from exc


def _format_player_start_message(iteration: int, loop_count: int | float) -> str:
    """
    Generate a status message indicating the start of a CAN log replay iteration.

    :param iteration:
        The current loop iteration (zero-based).
    :param loop_count:
        Total number of replay loops, or infinity for endless replay.
    :return:
        A formatted string describing the replay start and loop information.
    """
    if loop_count < 2:
        loop_info = ""
    else:
        loop_val = "∞" if math.isinf(loop_count) else str(loop_count)
        loop_info = f" [loop {iteration + 1}/{loop_val}]"
    return f"Can LogReader (Started on {datetime.now()}){loop_info}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay CAN traffic.")

    player_group = parser.add_argument_group("Player arguments")

    player_group.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        help="""Also print can frames to stdout.
                        You can add several of these to enable debugging""",
        default=2,
    )

    player_group.add_argument(
        "--ignore-timestamps",
        dest="timestamps",
        help="""Ignore timestamps (send all frames immediately with minimum gap between frames)""",
        action="store_false",
    )

    player_group.add_argument(
        "--error-frames",
        help="Also send error frames to the interface.",
        action="store_true",
    )

    player_group.add_argument(
        "-g",
        "--gap",
        type=float,
        help="<s> minimum time between replayed frames",
        default=0.0001,
    )
    player_group.add_argument(
        "-s",
        "--skip",
        type=float,
        default=60 * 60 * 24,
        help="Skip gaps greater than 's' seconds between messages. "
        "Default is 86400 (24 hours), meaning only very large gaps are skipped. "
        "Set to 0 to never skip any gaps (all delays are preserved). "
        "Set to a very small value (e.g., 1e-4) "
        "to skip all gaps and send messages as fast as possible.",
    )
    player_group.add_argument(
        "-l",
        "--loop",
        type=_parse_loop,
        metavar="NUM",
        default=1,
        help="Replay file NUM times. Use 'i' for infinite loop (default: 1)",
    )
    player_group.add_argument(
        "infile",
        metavar="input-file",
        type=str,
        help="The file to replay. For supported types see can.LogReader.",
    )

    # handle remaining arguments
    _add_extra_args(player_group)

    # add bus options
    add_bus_arguments(parser)

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    results, unknown_args = parser.parse_known_args()
    additional_config = _parse_additional_config([*results.extra_args, *unknown_args])

    _set_logging_level_from_namespace(results)
    verbosity = results.verbosity

    error_frames = results.error_frames

    with create_bus_from_namespace(results) as bus:
        loop_count: int | float = results.loop
        iteration = 0
        try:
            while iteration < loop_count:
                with LogReader(results.infile, **additional_config) as reader:
                    in_sync = MessageSync(
                        cast("Iterable[Message]", reader),
                        timestamps=results.timestamps,
                        gap=results.gap,
                        skip=results.skip,
                    )
                    print(_format_player_start_message(iteration, loop_count))

                    for message in in_sync:
                        if message.is_error_frame and not error_frames:
                            continue
                        if verbosity >= 3:
                            print(message)
                        bus.send(message)
                iteration += 1
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
