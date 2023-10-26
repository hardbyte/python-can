"""
The ``can`` package provides controller area network support for
Python developers; providing common abstractions to
different hardware devices, and a suite of utilities for sending and receiving
messages on a can bus.
"""

import logging
from typing import Any, Dict

__version__ = "4.3.0rc0"
__all__ = [
    "ASCReader",
    "ASCWriter",
    "AsyncBufferedReader",
    "BitTiming",
    "BitTimingFd",
    "BLFReader",
    "BLFWriter",
    "BufferedReader",
    "Bus",
    "BusABC",
    "BusState",
    "CanError",
    "CanInitializationError",
    "CanInterfaceNotImplementedError",
    "CanOperationError",
    "CanProtocol",
    "CanTimeoutError",
    "CanutilsLogReader",
    "CanutilsLogWriter",
    "CSVReader",
    "CSVWriter",
    "CyclicSendTaskABC",
    "LimitedDurationCyclicSendTaskABC",
    "Listener",
    "Logger",
    "LogReader",
    "ModifiableCyclicTaskABC",
    "Message",
    "MessageSync",
    "MF4Reader",
    "MF4Writer",
    "Notifier",
    "Printer",
    "RedirectReader",
    "RestartableCyclicTaskABC",
    "SizedRotatingLogger",
    "SqliteReader",
    "SqliteWriter",
    "ThreadSafeBus",
    "TRCFileVersion",
    "TRCReader",
    "TRCWriter",
    "VALID_INTERFACES",
    "bit_timing",
    "broadcastmanager",
    "bus",
    "ctypesutil",
    "detect_available_configs",
    "exceptions",
    "interface",
    "interfaces",
    "io",
    "listener",
    "logconvert",
    "log",
    "logger",
    "message",
    "notifier",
    "player",
    "set_logging_level",
    "thread_safe_bus",
    "typechecking",
    "util",
    "viewer",
]

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
from .bus import BusABC, BusState, CanProtocol
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
    MF4Reader,
    MF4Writer,
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

log = logging.getLogger("can")

rc: Dict[str, Any] = {}
