"""
can is an object-orient Controller Area Network interface module.

Modules include:

    :mod:`can.message`
        defines the :class:`~can.Message` class which is the
        lowest level of OO access to the library.

"""
import logging
log = logging.getLogger('can')

rc = dict(channel=0)

class CanError(IOError):
    pass

from can.CAN import BufferedReader, Listener, Printer, CSVWriter, SqliteWriter, set_logging_level
from can.message import Message
from can.bus import BusABC
from can.notifier import Notifier
from can.broadcastmanager import send_periodic, CyclicSendTaskABC, MultiRateCyclicSendTaskABC
from can.interfaces import interface
