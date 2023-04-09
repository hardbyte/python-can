"""
Interfaces contain low level implementations that interact with CAN hardware.
"""

import sys
from typing import Dict, Tuple, cast

__all__ = [
    "BACKENDS",
    "VALID_INTERFACES",
    "canalystii",
    "cantact",
    "etas",
    "gs_usb",
    "ics_neovi",
    "iscan",
    "ixxat",
    "kvaser",
    "neousys",
    "nican",
    "nixnet",
    "pcan",
    "robotell",
    "seeedstudio",
    "serial",
    "slcan",
    "socketcan",
    "socketcand",
    "systec",
    "udp_multicast",
    "usb2can",
    "vector",
    "virtual",
]

# interface_name => (module, classname)
BACKENDS: Dict[str, Tuple[str, str]] = {
    "kvaser": ("can.interfaces.kvaser", "KvaserBus"),
    "socketcan": ("can.interfaces.socketcan", "SocketcanBus"),
    "serial": ("can.interfaces.serial.serial_can", "SerialBus"),
    "pcan": ("can.interfaces.pcan", "PcanBus"),
    "usb2can": ("can.interfaces.usb2can", "Usb2canBus"),
    "ixxat": ("can.interfaces.ixxat", "IXXATBus"),
    "nican": ("can.interfaces.nican", "NicanBus"),
    "iscan": ("can.interfaces.iscan", "IscanBus"),
    "virtual": ("can.interfaces.virtual", "VirtualBus"),
    "udp_multicast": ("can.interfaces.udp_multicast", "UdpMulticastBus"),
    "neovi": ("can.interfaces.ics_neovi", "NeoViBus"),
    "vector": ("can.interfaces.vector", "VectorBus"),
    "slcan": ("can.interfaces.slcan", "slcanBus"),
    "robotell": ("can.interfaces.robotell", "robotellBus"),
    "canalystii": ("can.interfaces.canalystii", "CANalystIIBus"),
    "systec": ("can.interfaces.systec", "UcanBus"),
    "seeedstudio": ("can.interfaces.seeedstudio", "SeeedBus"),
    "cantact": ("can.interfaces.cantact", "CantactBus"),
    "gs_usb": ("can.interfaces.gs_usb", "GsUsbBus"),
    "nixnet": ("can.interfaces.nixnet", "NiXNETcanBus"),
    "neousys": ("can.interfaces.neousys", "NeousysBus"),
    "etas": ("can.interfaces.etas", "EtasBus"),
    "socketcand": ("can.interfaces.socketcand", "SocketCanDaemonBus"),
}

if sys.version_info >= (3, 8):
    from importlib.metadata import entry_points

    # See https://docs.python.org/3/library/importlib.metadata.html#entry-points,
    # "Compatibility Note".
    if sys.version_info >= (3, 10):
        BACKENDS.update(
            {
                interface.name: (interface.module, interface.attr)
                for interface in entry_points(group="can.interface")
            }
        )
    else:
        # The entry_points().get(...) causes a deprecation warning on Python >= 3.10.
        BACKENDS.update(
            {
                interface.name: cast(
                    Tuple[str, str], tuple(interface.value.split(":", maxsplit=1))
                )
                for interface in entry_points().get("can.interface", [])
            }
        )
else:
    from pkg_resources import iter_entry_points

    BACKENDS.update(
        {
            interface.name: (interface.module_name, interface.attrs[0])
            for interface in iter_entry_points("can.interface")
        }
    )

VALID_INTERFACES = frozenset(BACKENDS.keys())
