#!/usr/bin/env python
# coding: utf-8

"""
This module contains the base implementation of `can.Bus` as well
as a list of all avalibale backends and some implemented
CyclicSendTasks.
"""

from __future__ import absolute_import

import sys
import importlib
from pkg_resources import iter_entry_points
import logging

import can
from .bus import BusABC
from .broadcastmanager import CyclicSendTaskABC, MultiRateCyclicSendTaskABC
from .util import load_config

if sys.version_info.major > 2:
    basestring = str


log = logging.getLogger('can.interface')
log_autodetect = log.getChild('detect_available_configs')

# interface_name => (module, classname)
BACKENDS = {
    'kvaser':           ('can.interfaces.kvaser',           'KvaserBus'),
    'socketcan_ctypes': ('can.interfaces.socketcan',        'SocketcanCtypes_Bus'),
    'socketcan_native': ('can.interfaces.socketcan',        'SocketcanNative_Bus'),
    'serial':           ('can.interfaces.serial.serial_can','SerialBus'),
    'pcan':             ('can.interfaces.pcan',             'PcanBus'),
    'usb2can':          ('can.interfaces.usb2can',          'Usb2canBus'),
    'ixxat':            ('can.interfaces.ixxat',            'IXXATBus'),
    'nican':            ('can.interfaces.nican',            'NicanBus'),
    'iscan':            ('can.interfaces.iscan',            'IscanBus'),
    'virtual':          ('can.interfaces.virtual',          'VirtualBus'),
    'neovi':            ('can.interfaces.ics_neovi',        'NeoViBus'),
    'vector':           ('can.interfaces.vector',           'VectorBus'),
    'slcan':            ('can.interfaces.slcan',            'slcanBus')
}

BACKENDS.update({
    interface.name: (interface.module_name, interface.attrs[0])
    for interface in iter_entry_points('python_can.interface')
})


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

    @classmethod
    def __new__(cls, other, channel=None, *args, **kwargs):
        """
        Takes the same arguments as :class:`can.BusABC` with the addition of:

        :param kwargs:
            Should contain a bustype key with a valid interface name.

        :raises:
            NotImplementedError if the bustype isn't recognized
        :raises:
            ValueError if the bustype or channel isn't either passed as an argument
            or set in the can.rc config.

        """

        # Figure out the configuration
        config = load_config(config={
            'interface': kwargs.get('bustype', kwargs.get('interface')),
            'channel': channel
        })

        # remove the bustype & interface so it doesn't get passed to the backend
        if 'bustype' in kwargs:
            del kwargs['bustype']
        if 'interface' in kwargs:
            del kwargs['interface']

        cls = _get_class_for_interface(config['interface'])
        return cls(channel=config['channel'], *args, **kwargs)


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

    @classmethod
    def __new__(cls, other, channel, *args, **kwargs):

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

    @classmethod
    def __new__(cls, other, channel, *args, **kwargs):

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
