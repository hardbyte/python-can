"""
Creates a bridge between two CAN busses.

This will connect to two CAN busses. Messages received on one
bus will be sent to the other bus and vice versa.
"""

import argparse
import errno
import sys
import time
import logging
from datetime import datetime

from .logger import _create_base_argument_parser, _create_bus, _parse_additional_config

import can


USAGE = """
usage: can_bridge [{general config} --] {can A config} -- {can B config}

Bridge two CAN busses.

Both can busses will be connected so that messages from bus A will be sent on bus B and messages on bus B will be sent to bus A. The busses are separated by a `--`

positional arguments:
  {general config}      The configuration for this program excluding the config for each bus. Can be omitted
  {can A config}        The configuration for the first bus
  {can B config}        The configuration for the second bus

Example usage:
    can_bridge -i socketcan -c can0 -- -i socketcan can1
    can_bridge -vvv -- -i socketcan -c can0 -- -i socketcan can1

Type `can_bridge help_bus` for information about single bus configuration.
"""

LOG = logging.getLogger(__name__)


class UserError(Exception):
    pass


def get_config_list(it, separator, conf):
    while True:
        el = next(it)
        if el == separator:
            break
        else:
            conf.append(el)


def split_configurations(arg_list, separator="--"):
    general = []
    conf_a = []
    conf_b = []

    found_sep = False
    it = iter(arg_list)
    try:
        get_config_list(it, separator, conf_a)
        found_sep = True
        get_config_list(it, separator, conf_b)

        # When we reached this point we found two separators so we have
        # a general config. We will treate the first config as general
        general = conf_a
        conf_a = conf_b
        get_config_list(it, separator, conf_b)

        # When we reached this point we found three separators so this is
        # an error.
        raise UserError("To many configurations")
    except StopIteration:
        LOG.debug("All configurations were split")
        if not found_sep:
            raise UserError("Missing separator") from None

    return general, conf_a, conf_b


def main() -> None:
    general_parser = argparse.ArgumentParser()
    general_parser.add_argument(
        "-v",
        action="count",
        dest="verbosity",
        help="""How much information do you want to see at the command line?
                        You can add several of these e.g., -vv is DEBUG""",
        default=2,
    )

    bus_parser = argparse.ArgumentParser(description="Bridge two CAN busses.")

    _create_base_argument_parser(bus_parser)

    parser = argparse.ArgumentParser(description="Bridge two CAN busses.")
    parser.add_argument("configs", nargs=argparse.REMAINDER)

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        print(USAGE, file=sys.stderr)
        raise SystemExit(errno.EINVAL)

    args = sys.argv[1:]
    try:
        general, conf_a, conf_b = split_configurations(args)
    except UserError as exc:
        if len(args) == 1 and args[0] == "help_bus":
            bus_parser.print_help(sys.stderr)
        else:
            print(f"Error while processing arguments: {exc}", file=sys.stderr)
        raise SystemExit(errno.EINVAL) from exc

    LOG.debug("General configuration: %s", general)
    LOG.debug("Bus A configuration: %s", conf_a)
    LOG.debug("Bus B configuration: %s", conf_b)
    g_results = general_parser.parse_args(general)
    verbosity = g_results.verbosity

    a_results, a_unknown_args = bus_parser.parse_known_args(conf_a)
    a_additional_config = _parse_additional_config(
        [*a_results.extra_args, *a_unknown_args]
    )
    a_results.__dict__["verbosity"] = verbosity

    b_results, b_unknown_args = bus_parser.parse_known_args(conf_b)
    b_additional_config = _parse_additional_config(
        [*b_results.extra_args, *b_unknown_args]
    )
    b_results.__dict__["verbosity"] = verbosity

    LOG.debug("General configuration results: %s", g_results)
    LOG.debug("Bus A configuration results: %s", a_results)
    LOG.debug("Bus A additional configuration results: %s", a_additional_config)
    LOG.debug("Bus B configuration results: %s", b_results)
    LOG.debug("Bus B additional configuration results: %s", b_additional_config)
    with _create_bus(a_results, **a_additional_config) as bus_a:
        with _create_bus(b_results, **b_additional_config) as bus_b:
            reader_a = can.RedirectReader(bus_b)
            reader_b = can.RedirectReader(bus_a)
            can.Notifier(bus_a, [reader_a])
            can.Notifier(bus_b, [reader_b])
            print(f"CAN Bridge (Started on {datetime.now()})")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

    print(f"CAN Bridge (Stopped on {datetime.now()})")


if __name__ == "__main__":
    main()
