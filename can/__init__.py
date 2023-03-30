"""
The ``can`` package provides controller area network support for
Python developers; providing common abstractions to
different hardware devices, and a suite of utilities for sending and receiving
messages on a can bus.
"""

import logging
from typing import Any, Dict

__version__ = "4.1.0"

log = logging.getLogger("can")

rc: Dict[str, Any] = {}

from . import typechecking as typechecking  # isort:skip
from . import util as util  # isort:skip
from . import broadcastmanager as broadcastmanager
from . import interface as interface
from .bit_timing import BitTiming as BitTiming
from .bit_timing import BitTimingFd as BitTimingFd
from .bus import BusABC as BusABC
from .bus import BusState as BusState
from .exceptions import CanError as CanError
from .exceptions import CanInitializationError as CanInitializationError
from .exceptions import (
    CanInterfaceNotImplementedError as CanInterfaceNotImplementedError,
)
from .exceptions import CanOperationError as CanOperationError
from .exceptions import CanTimeoutError as CanTimeoutError
from .interface import Bus as Bus
from .interface import detect_available_configs as detect_available_configs
from .interfaces import VALID_INTERFACES as VALID_INTERFACES
from .io import ASCReader as ASCReader
from .io import ASCWriter as ASCWriter
from .io import BLFReader as BLFReader
from .io import BLFWriter as BLFWriter
from .io import CanutilsLogReader as CanutilsLogReader
from .io import CanutilsLogWriter as CanutilsLogWriter
from .io import CSVReader as CSVReader
from .io import CSVWriter as CSVWriter
from .io import Logger as Logger
from .io import LogReader as LogReader
from .io import MessageSync as MessageSync
from .io import Printer as Printer
from .io import SizedRotatingLogger as SizedRotatingLogger
from .io import SqliteReader as SqliteReader
from .io import SqliteWriter as SqliteWriter
from .io import TRCFileVersion as TRCFileVersion
from .io import TRCReader as TRCReader
from .io import TRCWriter as TRCWriter
from .listener import AsyncBufferedReader as AsyncBufferedReader
from .listener import BufferedReader as BufferedReader
from .listener import Listener as Listener
from .listener import RedirectReader as RedirectReader
from .message import Message as Message
from .notifier import Notifier as Notifier
from .thread_safe_bus import ThreadSafeBus as ThreadSafeBus
from .util import set_logging_level as set_logging_level
