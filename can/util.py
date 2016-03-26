#!/usr/bin/env python3
"""
Configuration file parsing.
"""
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser
import os
import os.path
import sys
import platform
import re


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
elif platform.system() == "Windows":
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

    :param path: path to config file. If not specified, several sensible
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


def load_config(path=None):
    """
    Returns a dict with configuration details which is loaded from (in this order):

    * Environment variables CAN_INTERFACE, CAN_CHANNEL
    * Config files ``/etc/can.conf`` or ``~/.can`` or ``~/.canrc``
      where the latter may add or replace values of the former.

    Interface can be kvaser, socketcan, socketcan_ctypes, socketcan_native, serial

    The returned dictionary may look like this::

        {
            'interface': '<python-can backend interface to use',
            'channel': 'default channel to use',
        }

    :param path: Optional path to config file.
    """
    config = load_file_config(path)
    config.update(load_environment_config())

    # substitute None for all values not found
    for key in REQUIRED_KEYS:
        if key not in config:
            config[key] = None

    return config

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


if __name__ == "__main__":
    print("Searching for configuration named:")
    print("\n".join(CONFIG_FILES))

    print("Settings:")
    print(load_config())
