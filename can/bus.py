# -*- coding: utf-8 -*-

import abc
import logging

logger = logging.getLogger(__name__)


class BusABC(object):
    """CAN Bus Abstract Base Class

    Concrete implementations must implement the following methods:
        * send
        * recv
        
    As well as setting the `channel_info` attribute to a string describing the
    interface.
    
    """
    
    #: a string describing the underlying bus channel
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
        """Transmit a message to CAN bus.
        Override this method to enable the transmit path.

        :param msg: A :class:`can.Message` object.

        :raise: :class:`can.CanError`
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
        """Used for CAN backends which need to flush their transmit buffer.

        """
        pass

    def shutdown(self):
        self.flush_tx_buffer()


    __metaclass__ = abc.ABCMeta
