#!/usr/bin/env python
# coding: utf-8

"""
This module contains the base implementation of `can.Bus` as well
as a list of all avalibale backends and some implemented
CyclicSendTasks.
"""

from __future__ import absolute_import, print_function

import sys
import importlib
import logging
import re

import can
from .bus import BusABC
from .broadcastmanager import CyclicSendTaskABC, MultiRateCyclicSendTaskABC
from .util import load_config
from .interfaces import BACKENDS

# Required by "detect_available_configs" for argument interpretation
if sys.version_info.major > 2:
    basestring = str

log = logging.getLogger('can.interface')
log_autodetect = log.getChild('detect_available_configs')

def _get_class_for_interface(interface):
    """
    Returns the main bus class for the given interface.

    :raises:
        NotImplementedError if the interface is not known
    :raises:
        ImportError     if there was a problem while importing the
                        interface or the bus class within that
    """

    # filter out the socketcan special case
    if interface == 'socketcan':
        try:
            interface = can.util.choose_socketcan_implementation()
        except Exception as e:
            raise ImportError("Cannot choose socketcan implementation: {}".format(e))

    # Find the correct backend
    try:
        module_name, class_name = BACKENDS[interface]
    except KeyError:
        raise NotImplementedError("CAN interface '{}' not supported".format(interface))

    # Import the correct interface module
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        raise ImportError(
            "Cannot import module {} for CAN interface '{}': {}".format(module_name, interface, e)
        )

    # Get the correct class
    try:
        bus_class = getattr(module, class_name)
    except Exception as e:
        raise ImportError(
            "Cannot import class {} from module {} for CAN interface '{}': {}"
                .format(class_name, module_name, interface, e)
        )

    return bus_class


class Bus(BusABC):
    """
    Instantiates a CAN Bus of the given `bustype`, falls back to reading a
    configuration file from default locations.
    """

    @staticmethod
    def __new__(cls, *args, **config):
        """
        Takes the same arguments as :class:`can.BusABC.__init__` with the addition of:

        :param dict config:
            Should contain an ``interface`` key with a valid interface name. If not,
            it is completed using :meth:`can.util.load_config`.

        :raises: NotImplementedError
            if the ``interface`` isn't recognized

        :raises: ValueError
            if the ``channel`` could not be determined
        """

        # figure out the rest of the configuration; this might raise an error
        config = load_config(config=config)

        # resolve the bus class to use for that interface
        cls = _get_class_for_interface(config['interface'])

        # remove the 'interface' key so it doesn't get passed to the backend
        del config['interface']

        # make sure the bus can handle this config
        if 'channel' not in config:
            raise ValueError("channel argument missing")

        # parameters like the channel attribute might be present in both
        # the *args list (=positional arguments) and the **config dict
        # (=keyowrd arguments)
        # 
        # One possible problem: this error could come from a subroutine
        # calling another __init__() in a wrong way (might inspect the
        # stack trace for that), although this would be catched by the
        # "if argument not in config" eventually, it would result in
        # one strange method call to the bus constructor first
        # 
        # TODO: solve more robustly

        while True:
            try:
                return cls(*args, **config)
            except TypeError as error:
                search_for = r"__init__\(\) got multiple values for argument '(\w+)'"
                match = re.match(search_for, error.message, re.UNICODE)
                if match:
                    argument = match.group(0)
                    if argument not in config:
                        raise
                    else:
                        log.warn("removing duplicate argument %s from keywaord arguments "
                                 "since it was also given as a positional argument", config[argument])
                        del config[argument]
                else:
                    raise


def detect_available_configs(interfaces=None):
    """Detect all configurations/channels that the interfaces could
    currently connect with.

    This might be quite time consuming.

    Automated configuration detection may not be implemented by
    every interface on every platform. This method will not raise
    an error in that case, but with rather return an empty list
    for that interface.

    :param interfaces: either
        - the name of an interface to be searched in as a string,
        - an iterable of interface names to search in, or
        - `None` to search in all known interfaces.
    :rtype: list of `dict`s
    :return: an iterable of dicts, each suitable for usage in
             :class:`can.interface.Bus`'s constructor.
    """

    # Figure out where to search
    if interfaces is None:
        # use an iterator over the keys so we do not have to copy it
        interfaces = BACKENDS.keys()
    elif isinstance(interfaces, basestring):
        interfaces = [interfaces, ]
    # else it is supposed to be an iterable of strings

    result = []
    for interface in interfaces:

        try:
            bus_class = _get_class_for_interface(interface)
        except ImportError:
            log_autodetect.debug('interface "%s" can not be loaded for detection of available configurations', interface)
            continue

        # get available channels
        try:
            available = list(bus_class._detect_available_configs())
        except NotImplementedError:
            log_autodetect.debug('interface "%s" does not support detection of available configurations', interface)
        else:
            log_autodetect.debug('interface "%s" detected %i available configurations', interface, len(available))

            # add the interface name to the configs if it is not already present
            for config in available:
                if 'interface' not in config:
                    config['interface'] = interface

            # append to result
            result += available

    return result


class CyclicSendTask(CyclicSendTaskABC):

    @staticmethod
    def __new__(cls, channel, *args, **kwargs):

        config = load_config(config={'channel': channel})

        # Import the correct implementation of CyclicSendTask
        if config['interface'] == 'socketcan_ctypes':
            from can.interfaces.socketcan.socketcan_ctypes import CyclicSendTask as _ctypesCyclicSendTask
            cls = _ctypesCyclicSendTask
        elif config['interface'] == 'socketcan_native':
            from can.interfaces.socketcan.socketcan_native import CyclicSendTask as _nativeCyclicSendTask
            cls = _nativeCyclicSendTask
        else:
            raise can.CanError("Current CAN interface doesn't support CyclicSendTask")

        return cls(config['channel'], *args, **kwargs)


class MultiRateCyclicSendTask(MultiRateCyclicSendTaskABC):

    @staticmethod
    def __new__(cls, channel, *args, **kwargs):

        config = load_config(config={'channel': channel})

        # Import the correct implementation of CyclicSendTask
        if config['interface'] == 'socketcan_ctypes':
            from can.interfaces.socketcan.socketcan_ctypes import MultiRateCyclicSendTask as _ctypesMultiRateCyclicSendTask
            cls = _ctypesMultiRateCyclicSendTask
        elif config['interface'] == 'socketcan_native':
            from can.interfaces.socketcan.socketcan_native import MultiRateCyclicSendTask as _nativeMultiRateCyclicSendTask
            cls = _nativeMultiRateCyclicSendTask
        else:
            can.log.info("Current CAN interface doesn't support CyclicSendTask")

        return cls(config['channel'], *args, **kwargs)
