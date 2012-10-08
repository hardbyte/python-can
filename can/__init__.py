"""
This is an object-orient Controller Area Network interface module.

Modules include:

    :mod:`can.message`
        defines the :class:`~can.message.Message` class which is the 
        lowest level of OO access to the library.
"""

class CANError(IOError):
    pass

from CAN import BufferedReader
from CAN import Listener

from CAN import set_logging_level

from interfaces import Bus
from message import Message

