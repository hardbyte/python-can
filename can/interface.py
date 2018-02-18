from __future__ import absolute_import

import can
import importlib

from can.broadcastmanager import CyclicSendTaskABC, MultiRateCyclicSendTaskABC
from pkg_resources import iter_entry_points
from can.util import load_config

# interface_name => (module, classname)
BACKENDS = {
    'kvaser':           ('can.interfaces.kvaser', 'KvaserBus'),
    'socketcan_ctypes': ('can.interfaces.socketcan', 'SocketcanCtypes_Bus'),
    'socketcan_native': ('can.interfaces.socketcan', 'SocketcanNative_Bus'),
    'serial':           ('can.interfaces.serial.serial_can', 'SerialBus'),
    'pcan':             ('can.interfaces.pcan', 'PcanBus'),
    'usb2can':          ('can.interfaces.usb2can', 'Usb2canBus'),
    'ixxat':            ('can.interfaces.ixxat', 'IXXATBus'),
    'nican':            ('can.interfaces.nican', 'NicanBus'),
    'iscan':            ('can.interfaces.iscan', 'IscanBus'),
    'virtual':          ('can.interfaces.virtual', 'VirtualBus'),
    'neovi':            ('can.interfaces.ics_neovi', 'NeoViBus'),
    'vector':           ('can.interfaces.vector', 'VectorBus'),
    'slcan':            ('can.interfaces.slcan', 'slcanBus')
}


BACKENDS.update({
    interface.name: (interface.module_name, interface.attrs[0])
    for interface in iter_entry_points('python_can.interface')
})


class Bus(object):
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
        config = load_config(config={
            'interface': kwargs.get('bustype'),
            'channel': channel
        })

        if 'bustype' in kwargs:
            # remove the bustype so it doesn't get passed to the backend
            del kwargs['bustype']
        interface = config['interface']
        channel = config['channel']

        # Import the correct Bus backend
        try:
            (module_name, class_name) = BACKENDS[interface]
        except KeyError:
            raise NotImplementedError("CAN interface '{}' not supported".format(interface))

        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            raise ImportError(
                "Cannot import module {} for CAN interface '{}': {}".format(module_name, interface, e)
            )
        try:
            cls = getattr(module, class_name)
        except Exception as e:
            raise ImportError(
                "Cannot import class {} from module {} for CAN interface '{}': {}".format(
                    class_name, module_name, interface, e
                )
            )

        return cls(channel, **kwargs)


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
