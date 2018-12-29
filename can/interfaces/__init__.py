# coding: utf-8

"""
Interfaces contain low level implementations that interact with CAN hardware.
"""

import warnings
from pkg_resources import iter_entry_points


# interface_name => (module, classname)
BACKENDS = {
    'kvaser':           ('can.interfaces.kvaser',           'KvaserBus'),
    'socketcan':        ('can.interfaces.socketcan',        'SocketcanBus'),
    'serial':           ('can.interfaces.serial.serial_can','SerialBus'),
    'pcan':             ('can.interfaces.pcan',             'PcanBus'),
    'usb2can':          ('can.interfaces.usb2can',          'Usb2canBus'),
    'ixxat':            ('can.interfaces.ixxat',            'IXXATBus'),
    'nican':            ('can.interfaces.nican',            'NicanBus'),
    'iscan':            ('can.interfaces.iscan',            'IscanBus'),
    'virtual':          ('can.interfaces.virtual',          'VirtualBus'),
    'neovi':            ('can.interfaces.ics_neovi',        'NeoViBus'),
    'vector':           ('can.interfaces.vector',           'VectorBus'),
    'slcan':            ('can.interfaces.slcan',            'slcanBus'),
    'canalystii':       ('can.interfaces.canalystii',       'CANalystIIBus'),
    'systec':           ('can.interfaces.systec',           'UcanBus')
}

BACKENDS.update({
    interface.name: (interface.module_name, interface.attrs[0])
    for interface in iter_entry_points('can.interface')
})

# Old entry point name. May be removed >3.0.
for interface in iter_entry_points('python_can.interface'):
    BACKENDS[interface.name] = (interface.module_name, interface.attrs[0])
    warnings.warn('{} is using the deprecated python_can.interface entry point. '.format(interface.name) +
                  'Please change to can.interface instead.', DeprecationWarning)

VALID_INTERFACES = frozenset(list(BACKENDS.keys()) + ['socketcan_native', 'socketcan_ctypes'])
