import argparse
import errno
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from can import Logger, SizedRotatingLogger
from can.cli import (
    _add_extra_args,
    _parse_additional_config,
    _set_logging_level_from_namespace,
    add_bus_arguments,
    create_bus_from_namespace,
)
from can.typechecking import TAdditionalCliArgs
from can.util import _warn_listen_only_deprecated

if TYPE_CHECKING:
    from can.io import BaseRotatingLogger
    from can.io.generic import MessageWriter


def _parse_logger_args(
    args: list[str],
) -> tuple[argparse.Namespace, TAdditionalCliArgs]:
    """Parse command line arguments for logger script."""

    parser = argparse.ArgumentParser(
        description="Log CAN traffic, printing messages to stdout or to a "
        "given file.",
    )

    logger_group = parser.add_argument_group("logger arguments")

    logger_group.add_argument(
        "-f",
        "--file_name",
        dest="log_file",
        help="Path and base log filename, for supported types see can.Logger.",
        default=None,
    )

    logger_group.add_argument(
        "-a",
        "--append",
        dest="append",
        help="Append to the log file if it already exists.",
        action="store_true",
    )

    logger_group.add_argument(
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

    logger_group.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        help="""How much information do you want to see at the command line?
                        You can add several of these e.g., -vv is DEBUG""",
        default=2,
    )

    state_group = logger_group.add_mutually_exclusive_group(required=False)
    # deprecated, hidden from the help output
    state_group.add_argument("--active", help=argparse.SUPPRESS, action="store_true")
    state_group.add_argument("--passive", help=argparse.SUPPRESS, action="store_true")

    # handle remaining arguments
    _add_extra_args(logger_group)

    # add bus options
    add_bus_arguments(parser, filter_arg=True)

    # print help message when no arguments were given
    if not args:
        parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    results, unknown_args = parser.parse_known_args(args)
    if results.active and "listen_only" in results:
        parser.error("argument --active: not allowed with argument --listen-only")
    additional_config = _parse_additional_config([*results.extra_args, *unknown_args])
    return results, additional_config


def main() -> None:
    results, additional_config = _parse_logger_args(sys.argv[1:])
    bus_kwargs: dict[str, Any] = {}
    if results.active:
        _warn_listen_only_deprecated("The '--active' argument", replacement=None)
    elif results.passive:
        _warn_listen_only_deprecated("The '--passive' argument", "'--listen-only'")
        bus_kwargs["listen_only"] = True

    bus = create_bus_from_namespace(results, **bus_kwargs)
    _set_logging_level_from_namespace(results)

    # --active used to set bus.state = BusState.ACTIVE after opening the bus,
    # which overrides a listen-only mode from the configuration, e.g.
    # "state = PASSIVE" for pcan or systec. Keep that behaviour until --active
    # is removed in 5.0.0; --active together with --listen-only is rejected
    # by the argument parser, so this only undoes a configured listen-only mode.
    if results.active and bus.listen_only:
        bus.listen_only = False

    print(f"Connected to {bus.__class__.__name__}: {bus.channel_info}")
    print(f"Can Logger (Started on {datetime.now(tz=UTC)})")

    logger: MessageWriter | BaseRotatingLogger
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
