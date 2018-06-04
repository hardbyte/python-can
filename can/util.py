#!/usr/bin/env python
# coding: utf-8

"""
Utilities and configuration file parsing.
"""

from __future__ import absolute_import, print_function

import os
import os.path
import sys
import platform
import re
import logging
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser

import can
from can.interfaces import VALID_INTERFACES

log = logging.getLogger('can.util')

# List of valid data lengths for a CAN FD message
CAN_FD_DLC = [
    0, 1, 2, 3, 4, 5, 6, 7, 8,
    12, 16, 20, 24, 32, 48, 64
]

REQUIRED_KEYS = [
    'interface',
    'channel',
]


CONFIG_FILES = ['~/can.conf']

if platform.system() == "Linux":
    CONFIG_FILES.extend(
        [
            '/etc/can.conf',
            '~/.can',
            '~/.canrc'
        ]
    )
elif platform.system() == "Windows" or platform.python_implementation() == "IronPython":
    CONFIG_FILES.extend(
        [
            'can.ini',
            os.path.join(os.getenv('APPDATA', ''), 'can.ini')
        ]
    )


def load_file_config(path=None):
    """
    Loads configuration from file with following content::

        [default]
        interface = socketcan
        channel = can0

    :param path:
        path to config file. If not specified, several sensible
        default locations are tried depending on platform.

    """
    config = ConfigParser()
    if path is None:
        config.read([os.path.expanduser(path) for path in CONFIG_FILES])
    else:
        config.read(path)

    if not config.has_section('default'):
        return {}

    return dict(
        (key, val)
        for key, val in config.items('default')
    )


def load_environment_config():
    """
    Loads config dict from environmental variables (if set):

    * CAN_INTERFACE
    * CAN_CHANNEL
    * CAN_BITRATE

    """
    mapper = {
        'interface': 'CAN_INTERFACE',
        'channel': 'CAN_CHANNEL',
        'bitrate': 'CAN_BITRATE',
    }
    return dict(
        (key, os.environ.get(val))
        for key, val in mapper.items()
        if val in os.environ
    )


def load_config(path=None, config=None):
    """
    Returns a dict with configuration details which is loaded from (in this order):

    - config
    - can.rc
    - Environment variables CAN_INTERFACE, CAN_CHANNEL, CAN_BITRATE
    - Config files ``/etc/can.conf`` or ``~/.can`` or ``~/.canrc``
      where the latter may add or replace values of the former.

    Interface can be any of the strings from ``can.VALID_INTERFACES`` for example:
    kvaser, socketcan, pcan, usb2can, ixxat, nican, virtual.

    .. note::

        If you pass ``"socketcan"`` this automatically selects between the
        native and ctypes version.

    .. note::
 
            The key ``bustype`` is copied to ``interface`` if that one is missing
            and does never appear in the result.

    :param path:
        Optional path to config file.

    :param config:
        A dict which may set the 'interface', and/or the 'channel', or neither.
        It may set other values that are passed through.

    :return:
        A config dictionary that should contain 'interface' & 'channel'::

            {
                'interface': 'python-can backend interface to use',
                'channel': 'default channel to use',
                # possibly more
            }

        Note ``None`` will be used if all the options are exhausted without
        finding a value.

        All unused values are passed from ``config`` over to this.

    :raises:
        NotImplementedError if the ``interface`` isn't recognized
    """

    # start with an empty dict to apply filtering to all sources
    given_config = config
    config = {}

    # use the given dict for default values
    config_sources = [
        given_config,
        can.rc,
        load_environment_config,
        lambda: load_file_config(path)
    ]

    # Slightly complex here to only search for the file config if required
    for cfg in config_sources:
        if callable(cfg):
            cfg = cfg()
        # remove legacy operator (and copy to interface if not already present)
        if 'bustype' in cfg:
            if 'interface' not in cfg or not cfg['interface']:
                cfg['interface'] = cfg['bustype']
            del cfg['bustype']
        # copy all new parameters
        for key in cfg:
            if key not in config:
                config[key] = cfg[key]

    # substitute None for all values not found
    for key in REQUIRED_KEYS:
        if key not in config:
            config[key] = None

    # this is done later too but better safe than sorry
    if config['interface'] == 'socketcan':
        config['interface'] = choose_socketcan_implementation()

    if config['interface'] not in VALID_INTERFACES:
        raise NotImplementedError('Invalid CAN Bus Type - {}'.format(config['interface']))

    if 'bitrate' in config:
        config['bitrate'] = int(config['bitrate'])

    can.log.debug("loaded can config: {}".format(config))
    return config


def choose_socketcan_implementation():
    """Set the best version of the SocketCAN module for this system.

    :rtype: str
    :return:
        either 'socketcan_ctypes' or 'socketcan_native',
        depending on the current platform and environment
    :raises Exception: If the system doesn't support SocketCAN at all
    """

    # Check OS: SocketCAN is available only under Linux
    if not sys.platform.startswith('linux'):
        msg = 'SocketCAN not available under {}'.format(sys.platform)
        raise Exception(msg)

    # Check release: SocketCAN was added to Linux 2.6.25
    rel_string = platform.release()
    m = re.match(r'\d+\.\d+\.\d', rel_string)
    if not m: # None or empty
        msg = 'Bad linux release {}'.format(rel_string)
        raise Exception(msg)
    rel_num = [int(i) for i in rel_string[:m.end()].split('.')]

    if (rel_num < [2, 6, 25]):
        msg = 'SocketCAN not available under Linux {}'.format(rel_string)
        raise Exception(msg)

    # Check Python version:
    #
    # CPython:
    # Support for SocketCAN was added in Python 3.3, but support for
    # CAN FD frames (with socket.CAN_RAW_FD_FRAMES) was just added
    # to Python in version 3.5.
    # So we want to use socketcan_native only on Python >= 3.5 (see #274).
    #
    # PyPy:
    # Furthermore, socket.CAN_* is not supported by PyPy 2 or 3 (as of
    # April 2018) at all. Thus we want to use socketcan_ctypes there as well.
    #
    # General approach:
    # To support possible future versions of current platforms as well as
    # potential other ones, we take the approach of feature checking instead
    # of platform/version checking.

    try:
        # try to import typical attributes
        from socket import CAN_RAW, CAN_BCM, CAN_RAW_FD_FRAMES
    except ImportError:
        return 'socketcan_ctypes'
    else:
        return 'socketcan_native'


def set_logging_level(level_name=None):
    """Set the logging level for the "can" logger.
    Expects one of: 'critical', 'error', 'warning', 'info', 'debug', 'subdebug'
    """
    can_logger = logging.getLogger('can')

    try:
        can_logger.setLevel(getattr(logging, level_name.upper()))
    except AttributeError:
        can_logger.setLevel(logging.DEBUG)
    log.debug("Logging set to {}".format(level_name))


def len2dlc(length):
    """Calculate the DLC from data length.

    :param int length: Length in number of bytes (0-64)

    :returns: DLC (0-15)
    :rtype: int
    """
    if length <= 8:
        return length
    for dlc, nof_bytes in enumerate(CAN_FD_DLC):
        if nof_bytes >= length:
            return dlc
    return 15


def dlc2len(dlc):
    """Calculate the data length from DLC.

    :param int dlc: DLC (0-15)

    :returns: Data length in number of bytes (0-64)
    :rtype: int
    """
    return CAN_FD_DLC[dlc] if dlc <= 15 else 64


if __name__ == "__main__":
    print("Searching for configuration named:")
    print("\n".join(CONFIG_FILES))
    print()
    print("Settings:")
    print(load_config())
