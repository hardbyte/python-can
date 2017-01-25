# -*- coding: utf-8 -*-
from __future__ import print_function

import abc
import logging
from can.broadcastmanager import ThreadBasedCyclicSendManager, ThreadBasedCyclicSendTask
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
    def __init__(self, channel=None, can_filters=None, **config):
        """
        :param channel:
            The can interface identifier. Expected type is backend dependent.

        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

            >>> [{"can_id": 0x11, "can_mask": 0x21}]

            A filter matches, when ``<received_can_id> & can_mask == can_id & can_mask``

        :param dict config:
            Any backend dependent configurations are passed in this dictionary
        """

    @abc.abstractmethod
    def recv(self, timeout=None):
        """Block waiting for a message from the Bus.

        :param float timeout: Seconds to wait for a message.

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

    def send_periodic(self, msg, period, duration=None):
        """Start sending a message at a given period on this bus.

        :param can.Message msg:
            Message to transmit
        :param float period:
            Period in seconds between each message
        :param float duration:
            The duration to keep sending this message at given rate. If
            no duration is provided, the task will continue indefinitely.

        :return: A started task instance
        :rtype: can.CyclicSendTaskABC

            Note the duration before the message stops being sent may not
            be exactly the same as the duration specified by the user. In
            general the message will be sent at the given rate until at
            least *duration* seconds.

        """
        return ThreadBasedCyclicSendTask(self, msg, period, duration)

    def __iter__(self):
        """Allow iteration on messages as they are received.

            >>> for msg in bus:
            ...     print(msg)


        :yields: :class:`can.Message` msg objects.
        """
        while True:
            m = self.recv(timeout=1.0)
            if m is not None:
                yield m
        logger.debug("done iterating over bus messages")

    def set_filters(self, can_filters=None):
        """Apply filtering to all messages received by this Bus.

        Calling without passing any filters will reset the applied filters.

        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

            >>> [{"can_id": 0x11, "can_mask": 0x21}]

            A filter matches, when ``<received_can_id> & can_mask == can_id & can_mask``

        """
        raise NotImplementedError("Trying to set_filters on unsupported bus")

    def flush_tx_buffer(self):
        """Used for CAN interfaces which need to flush their transmit buffer.

        """
        pass

    def shutdown(self):
        """
        Called to carry out any interface specific cleanup required
        in shutting down a bus.
        """
        self.flush_tx_buffer()

    __metaclass__ = abc.ABCMeta
