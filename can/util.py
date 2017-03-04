#!/usr/bin/env python3
"""
Utilities and configuration file parsing.
"""

import time

import can
from can.interfaces import VALID_INTERFACES

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser
import os
import os.path
import sys
import platform
import re
import logging

log = logging.getLogger('can.util')

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
            os.path.join(os.getenv('APPDATA'), 'can.ini')
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
        if key in REQUIRED_KEYS
    )


def load_environment_config():
    """
    Loads config dict from environmental variables (if set):

    * CAN_INTERFACE
    * CAN_CHANNEL

    """
    mapper = {
        'interface': 'CAN_INTERFACE',
        'channel': 'CAN_CHANNEL',
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
    - Environment variables CAN_INTERFACE, CAN_CHANNEL
    - Config files ``/etc/can.conf`` or ``~/.can`` or ``~/.canrc``
      where the latter may add or replace values of the former.

    Interface can be any of the strings from ``can.VALID_INTERFACES`` for example:
    kvaser, socketcan, pcan, usb2can, ixxat, nican, remote, virtual.

    .. note::

        If you pass ``"socketcan"`` this automatically selects between the
        native and ctypes version.

    :param path:
        Optional path to config file.
    :param config:
        A dict which may set the 'interface', and/or the 'channel', or neither.

    :return:
        A config dictionary that should contain 'interface' & 'channel'::

            {
                'interface': 'python-can backend interface to use',
                'channel': 'default channel to use',
            }

        Note ``None`` will be used if all the options are exhausted without
        finding a value.
    """


    system_config = {}
    configs = [
        config,
        can.rc,
        load_environment_config,
        lambda: load_file_config(path)
    ]

    # Slightly complex here to only search for the file config if required
    for cfg in configs:
        if callable(cfg):
            cfg = cfg()
        for key in REQUIRED_KEYS:
            if key not in system_config and key in cfg and cfg[key] is not None:
                system_config[key] = cfg[key]

        if all(k in system_config for k in REQUIRED_KEYS):
            break

    # substitute None for all values not found
    for key in REQUIRED_KEYS:
        if key not in system_config:
            system_config[key] = None

    if system_config['interface'] == 'socketcan':
        system_config['interface'] = choose_socketcan_implementation()

    if system_config['interface'] not in VALID_INTERFACES:
        raise NotImplementedError('Invalid CAN Bus Type - {}'.format(can.rc['interface']))

    can.log.debug("can config: {}".format(system_config))
    return system_config


def choose_socketcan_implementation():
    """Set the best version of SocketCAN for this system.

    :param config: The can.rc configuration dictionary
    :raises Exception: If the system doesn't support SocketCAN
    """
    # Check OS: SocketCAN is available only under Linux
    if not sys.platform.startswith('linux'):
        msg = 'SocketCAN not available under {}'.format(
            sys.platform)
        raise Exception(msg)
    else:
        # Check release: SocketCAN was added to Linux 2.6.25
        rel_string = platform.release()
        m = re.match('\d+\.\d+\.\d', rel_string)
        if m is None:
            msg = 'Bad linux release {}'.format(rel_string)
            raise Exception(msg)
        rel_num = [int(i) for i in rel_string[:m.end()].split('.')]
        if (rel_num >= [2, 6, 25]):
            # Check Python version: SocketCAN was added in 3.3
            return 'socketcan_native' if sys.version_info >= (3, 3) else 'socketcan_ctypes'
        else:
            msg = 'SocketCAN not available under Linux {}'.format(
                    rel_string)
            raise Exception(msg)


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


if __name__ == "__main__":
    print("Searching for configuration named:")
    print("\n".join(CONFIG_FILES))

    print("Settings:")
    print(load_config())
