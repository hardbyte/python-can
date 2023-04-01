"""
The ``can`` package provides controller area network support for
Python developers; providing common abstractions to
different hardware devices, and a suite of utilities for sending and receiving
messages on a can bus.
"""

import logging
from typing import Any, Dict

__version__ = "4.1.0"
__all__ = [
    "ASCReader",
    "ASCWriter",
    "AsyncBufferedReader",
    "BitTiming",
    "BitTimingFd",
    "BLFReader",
    "BLFWriter",
    "broadcastmanager",
    "BufferedReader",
    "Bus",
    "BusABC",
    "BusState",
    "CanError",
    "CanInitializationError",
    "CanInterfaceNotImplementedError",
    "CanOperationError",
    "CanTimeoutError",
    "CanutilsLogReader",
    "CanutilsLogWriter",
    "CSVReader",
    "CSVWriter",
    "CyclicSendTaskABC",
    "detect_available_configs",
    "interface",
    "LimitedDurationCyclicSendTaskABC",
    "Listener",
    "Logger",
    "LogReader",
    "ModifiableCyclicTaskABC",
    "Message",
    "MessageSync",
    "Notifier",
    "Printer",
    "RedirectReader",
    "RestartableCyclicTaskABC",
    "set_logging_level",
    "SizedRotatingLogger",
    "SqliteReader",
    "SqliteWriter",
    "ThreadSafeBus",
    "typechecking",
    "TRCFileVersion",
    "TRCReader",
    "TRCWriter",
    "util",
    "VALID_INTERFACES",
]

log = logging.getLogger("can")

rc: Dict[str, Any] = {}

from . import typechecking  # isort:skip
from . import util  # isort:skip
from . import broadcastmanager, interface
from .bit_timing import BitTiming, BitTimingFd
from .broadcastmanager import (
    CyclicSendTaskABC,
    LimitedDurationCyclicSendTaskABC,
    ModifiableCyclicTaskABC,
    RestartableCyclicTaskABC,
)
from .bus import BusABC, BusState
from .exceptions import (
    CanError,
    CanInitializationError,
    CanInterfaceNotImplementedError,
    CanOperationError,
    CanTimeoutError,
)
from .interface import Bus, detect_available_configs
from .interfaces import VALID_INTERFACES
from .io import (
    ASCReader,
    ASCWriter,
    BLFReader,
    BLFWriter,
    CanutilsLogReader,
    CanutilsLogWriter,
    CSVReader,
    CSVWriter,
    Logger,
    LogReader,
    MessageSync,
    Printer,
    SizedRotatingLogger,
    SqliteReader,
    SqliteWriter,
    TRCFileVersion,
    TRCReader,
    TRCWriter,
)
from .listener import AsyncBufferedReader, BufferedReader, Listener, RedirectReader
from .message import Message
from .notifier import Notifier
from .thread_safe_bus import ThreadSafeBus
from .util import set_logging_level
