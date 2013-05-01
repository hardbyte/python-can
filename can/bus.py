# -*- coding: utf-8 -*-

import abc
import logging
import queue

logger = logging.getLogger(__name__)

class BusABC(object):
    """CAN Bus Abstract Base Class

    External API:

        * send(message)
            Transmit message to CAN bus.

        * recv()
            Blocks until a message is available from the bus.

        * channel_info
            str attribute describing underlying bus

    Concrete implementations must implement the following methods:
        * send
        * recv
        
    As well as setting the `channel_info` attribute to a string describing the
    interface.
    
    """
    
    # a string describing the channel
    channel_info = 'unknown'

    @abc.abstractmethod
    def recv(self, timeout=None):
        """Block waiting for a message from the Bus.  
        
        :return:
            None on timeout or a :class:`can.Message` object.
        """
        raise NotImplementedError("Trying to read from a write only bus?")

    @abc.abstractmethod
    def send(self, msg):
        """Override this method to enable the transmit path.

        :param :class:`can.Message` msg:

        :raise :class:`can.CanError`:
            if the message could not be written.
        """
        raise NotImplementedError("Trying to write to a readonly bus?")

    def __iter__(self):
        """Allow iteration on messages as they are received.

            >>> for msg in bus:
            ...     print(msg)


        :yields: :class:`can.Message` msg objects.
        """
        while True:
            yield self.recv()
        logger.debug("done iterating over bus messages")

    def flush_tx_buffer(self):
        pass

    def shutdown(self):
        self.flush_tx_buffer()


    __metaclass__ = abc.ABCMeta
