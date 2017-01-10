"""
Read and Write CAN bus messages using a range of Readers
and Writers based off the file extension.
"""

from .asc import ASCWriter
from .blf import BLFReader, BLFWriter
from .csv import CSVWriter
from .sqlite import SqlReader, SqliteWriter
from .stdout import Printer


class Logger(object):
    """
    Logs CAN messages to a file.

    The format is determined from the file format which can be one of:
      * .asc: :class:`can.ASCWriter`
      * .blf :class:`can.BLFWriter`
      * .csv: :class:`can.CSVWriter`
      * .db: :class:`can.SqliteWriter`
      * other: :class:`can.Printer`

    Note this class itself is just a dispatcher,
    an object that inherits from Listener will
    be created when instantiating this class.
    """

    @classmethod
    def __new__(cls, other, filename):
        if not filename:
            return Printer()
        elif filename.endswith(".asc"):
            return ASCWriter(filename)
        elif filename.endswith(".blf"):
            return BLFWriter(filename)
        elif filename.endswith(".csv"):
            return CSVWriter(filename)
        elif filename.endswith(".db"):
            return SqliteWriter(filename)
        else:
            return Printer(filename)


class LogReader(object):
    """
    Replay logged CAN messages from a file.

    The format is determined from the file format which can be one of:
      * .asc
      * .blf
      * .csv
      * .db

    Exposes a simple iterator interface, to use simply:

        >>> for m in LogReader(my_file):
        ...     print(m)

    Note there are no time delays, if you want to reproduce
    the measured delays between messages look at the
    :class:`can.util.MessageSync` class.
    """

    @classmethod
    def __new__(cls, other, filename):
        if filename.endswith(".asc"):
            raise NotImplemented
        #     return ASCReader(filename)
        if filename.endswith(".blf"):
            return BLFReader(filename)
        if filename.endswith(".csv"):
            raise NotImplemented
        #     return CSVReader(filename)
        if filename.endswith(".db"):
            return SqlReader(filename)
