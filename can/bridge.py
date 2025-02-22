"""
Creates a bridge between two CAN busses.

This will connect to two CAN busses. Messages received on one
bus will be sent to the other bus and vice versa.
"""

import argparse
import errno
import sys
import logging
from datetime import datetime

from .logger import _create_base_argument_parser, _create_bus, _parse_additional_config


LOG = logging.getLogger(__name__)


def get_config_list(it, separator, conf):
    while True:
        el = next(it)
        if el == separator:
            break
        else:
            conf.append(el)


def split_configurations(arg_list, separator='--'):
    general = []
    conf_a = []
    conf_b = []

    it = iter(arg_list)
    try:
        get_config_list(it, separator, conf_a)
        get_config_list(it, separator, conf_b)

        # When we reached this point we found two separators so we have
        # a general config. We will treate the first config as general
        general = conf_a
        conf_a = conf_b
        get_config_list(it, separator, conf_b)

        # When we reached this point we found three separators so this is
        # an error.
        raise Exception("To many configurations")
    except StopIteration:
        LOG.debug("All configurations were split")

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
    parser.add_argument('configs', nargs=argparse.REMAINDER)

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        bus_parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    args = sys.argv[1:]
    general, conf_a, conf_b = split_configurations(args)

    g_results = general_parser.parse_args(general)
    verbosity = g_results.verbosity

    a_results, a_unknown_args = bus_parser.parse_known_args(conf_a)
    a_additional_config = _parse_additional_config([*a_results.extra_args, *a_unknown_args])
    a_results.__dict__['verbosity'] = verbosity

    b_results, b_unknown_args = bus_parser.parse_known_args(conf_b)
    b_additional_config = _parse_additional_config([*b_results.extra_args, *b_unknown_args])
    b_results.__dict__['verbosity'] = verbosity

    with _create_bus(a_results, **a_additional_config) as bus_a:
        with _create_bus(b_results, **b_additional_config) as bus_b:
            print(f"CAN Bridge (Started on {datetime.now()})")

    print(f"CAN Bridge (Stopped on {datetime.now()})")


if __name__ == "__main__":
    main()
