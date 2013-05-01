"""
can is an object-orient Controller Area Network interface module.

Modules include:

    :mod:`can.message`
        defines the :class:`~can.Message` class which is the 
        lowest level of OO access to the library.

"""
import logging

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('CAN')


class CanError(IOError):
    pass

from can.CAN import BufferedReader, Listener, Printer, set_logging_level
from can.message import Message
from can.bus import BusABC
from can.notifier import Notifier

# Interface can be kvaser, socketcan, socketcan_ctypes, socketcan_native, serial
rc = {
      'default-interface': 'kvaser',
      'interface': 'kvaser'
      }

