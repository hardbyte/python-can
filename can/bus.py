# -*- coding: utf-8 -*-

"""
Contains the ABC bus implementation.
"""

from __future__ import print_function, absolute_import
import abc
import logging
import threading
from can.broadcastmanager import ThreadBasedCyclicSendTask


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
            A list of dictionaries each containing a "can_id", a "can_mask",
            and an "extended" key.

            >>> [{"can_id": 0x11, "can_mask": 0x21, "extended": False}]

            A filter matches, when ``<received_can_id> & can_mask == can_id & can_mask``

        :param dict config:
            Any backend dependent configurations are passed in this dictionary
        """
        pass

    def __str__(self):
        return self.channel_info

    @abc.abstractmethod
    def recv(self, timeout=None):
        """Block waiting for a message from the Bus.

        :param float timeout: Seconds to wait for a message.

        :return:
            None on timeout or a :class:`can.Message` object.
        """
        raise NotImplementedError("Trying to read from a write only bus?")

    @abc.abstractmethod
    def send(self, msg, timeout=None):
        """Transmit a message to CAN bus.
        Override this method to enable the transmit path.

        :param can.Message msg: A message object.
        :param float timeout:
            If > 0, wait up to this many seconds for message to be ACK:ed or
            for transmit queue to be ready depending on driver implementation.
            If timeout is exceeded, an exception will be raised.
            Might not be supported by all interfaces.

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
        if not hasattr(self, "_lock"):
            # Create send lock for this bus
            self._lock = threading.Lock()
        return ThreadBasedCyclicSendTask(self, self._lock, msg, period, duration)

    def __iter__(self):
        """Allow iteration on messages as they are received.

            >>> for msg in bus:
            ...     print(msg)


        :yields: :class:`can.Message` msg objects.
        """
        while True:
            msg = self.recv(timeout=1.0)
            if msg is not None:
                yield msg

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
        """Discard every message that may be queued in the output buffer(s).
        """
        pass

    def shutdown(self):
        """
        Called to carry out any interface specific cleanup required
        in shutting down a bus.
        """
        self.flush_tx_buffer()

    __metaclass__ = abc.ABCMeta
