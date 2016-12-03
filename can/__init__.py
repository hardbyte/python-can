"""
can is an object-orient Controller Area Network interface module.
"""
import logging
log = logging.getLogger('can')

rc = dict(channel=0)


class CanError(IOError):
    pass

from can.CAN import BufferedReader, Listener, Logger, Printer, CSVWriter, SqliteWriter, ASCWriter, set_logging_level
from can.message import Message
from can.bus import BusABC
from can.notifier import Notifier
from can.broadcastmanager import send_periodic, CyclicSendTaskABC, MultiRateCyclicSendTaskABC
from can.interfaces import interface
