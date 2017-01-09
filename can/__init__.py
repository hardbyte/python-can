"""
can is an object-orient Controller Area Network interface module.
"""
import logging
log = logging.getLogger('can')

rc = dict(channel=0)


class CanError(IOError):
    pass

from can.listener import Listener, BufferedReader, RedirectReader

from can.io import Logger, Printer, LogReader
from can.io import ASCWriter
from can.io import BLFReader, BLFWriter
from can.io import CSVWriter
from can.io import SqliteWriter, SqlReader

from can.util import set_logging_level

from can.message import Message
from can.bus import BusABC
from can.notifier import Notifier
from can.broadcastmanager import send_periodic, CyclicSendTaskABC, MultiRateCyclicSendTaskABC
from can.interfaces import interface
