#!/usr/bin/env python
# coding: utf-8

"""
Contains the ABC bus implementation and documentation.
"""

from __future__ import print_function, absolute_import

from abc import ABCMeta, abstractmethod
import logging
import threading
from time import time

from can.broadcastmanager import ThreadBasedCyclicSendTask

logger = logging.getLogger(__name__)


class BusABC(object):

    """CAN Bus Abstract Base Class.

    Concrete implementations *must* implement the following:
        * :meth:`~can.BusABC.send`
        * :meth:`~can.BusABC._recv_internal`
        * set the :attr:`~can.BusABC.channel_info` attribute to a string describing
          the interface and/or channel

    The *may* implement the following:
        * :meth:`~can.BusABC.flush_tx_buffer` to allow discrading any
          messages yet to be sent
        * :meth:`~can.BusABC.shutdown` to override how the bus should
          shut down, in which case the class has to either call through
          `super().shutdown()` or call :meth:`~can.BusABC.flush_tx_buffer`
          on its own
        * :meth:`~can.BusABC.send_periodic` to override the software based
          periodic sending and push it down to the kernel or hardware
        * :meth:`~can.BusABC._apply_filters` to apply efficient filters
          to lower level systems

    """

    #: a string describing the underlying bus channel
    channel_info = 'unknown'

    @abstractmethod
    def __init__(self, channel=None, can_filters=None, **config):
        """
        :param channel:
            The can interface identifier. Expected type is backend dependent.

        :param list can_filters:
            See :meth:`~can.BusABC.set_filters` for details.

        :param dict config:
            Any backend dependent configurations are passed in this dictionary
        """
        self.set_filters(can_filters)

    def __str__(self):
        return self.channel_info

    def recv(self, timeout=None):
        """Block waiting for a message from the Bus.

        :param float timeout: Seconds to wait for a message.

        :return:
            None on timeout or a :class:`can.Message` object.
        :raises can.CanError:
            if an error occurred while reading
        """
        start = time()
        time_left = timeout

        while True:

            # try to get a message
            msg, already_filtered = self._recv_internal(timeout=time_left)

            # return it, if it matches
            if msg and (already_filtered or self._matches_filters(msg)):
                return msg

            # if not, and timeout is None, try indefinitely
            elif timeout is None:
                continue

            # try next one only if there still is time, and with reduced timeout
            else:

                time_left = timeout - (time() - start)

                if time_left > 0:
                    continue
                else:
                    return None

    @abstractmethod
    def _recv_internal(self, timeout):
        """
        Read a message from the bus and tell whether it was filtered.

        :raises can.CanError:
            if an error occurred while reading
        """
        raise NotImplementedError("Trying to read from a write only bus?")

    @abstractmethod
    def send(self, msg, timeout=None):
        """Transmit a message to CAN bus.
        Override this method to enable the transmit path.

        :param can.Message msg: A message object.
        :param float timeout:
            If > 0, wait up to this many seconds for message to be ACK:ed or
            for transmit queue to be ready depending on driver implementation.
            If timeout is exceeded, an exception will be raised.
            Might not be supported by all interfaces.

        :raises can.CanError:
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
            # Create a send lock for this bus
            self._lock = threading.Lock()
        return ThreadBasedCyclicSendTask(self, self._lock, msg, period, duration)

    def __iter__(self):
        """Allow iteration on messages as they are received.

            >>> for msg in bus:
            ...     print(msg)


        :yields:
            :class:`can.Message` msg objects.
        """
        while True:
            msg = self.recv(timeout=1.0)
            if msg is not None:
                yield msg

    @property
    def filters(self):
        return self._can_filters

    @filters.setter
    def filters(self, filters):
        self.set_filters(filters)

    def set_filters(self, can_filters=None):
        """Apply filtering to all messages received by this Bus.

        All messages that match at least one filter are returned.
        If `can_filters` is `None`, all messages are matched.
        If it is a zero size interable, no messages are matched.

        Calling without passing any filters will reset the applied
        filters to `None`.

        :param Iterator[dict] can_filters:
            A iterable of dictionaries each containing a "can_id", a "can_mask",
            and an optional "extended" key.

            >>> [{"can_id": 0x11, "can_mask": 0x21, "extended": False}]

            A filter matches, when ``<received_can_id> & can_mask == can_id & can_mask``.
            If ``extended`` is set as well, it only matches messages where
            ``<received_is_extended> == extended``. Else it matches every messages based
            only on the arbitration ID and mask.

        """
        # TODO: would it be faster to precompute `can_id & can_mask` here, and then
        # instead of (can_id, can_mask, ext) store (masked_can_id, can_mask, ext)?
        # Or maybe store it as a tuple/.../? for faster iteration & access?
        self._can_filters = can_filters
        self._apply_filters()

    def _apply_filters(self):
        """
        Hook for applying the filters to the underlying kernel or
        hardware if supported/implemented by the interface.
        """
        pass

    def _matches_filters(self, msg):
        """Checks whether the given message matches at least one of the
        current filters.

        See :meth:`~can.BusABC.set_filters` for details.
        """

        # TODO: add unit testing for this method

        # if no filters are set, all messages are matched
        if self._can_filters is None:
            return True

        for can_filter in self._can_filters:
            # check if this filter even applies to the message
            if 'extended' in can_filter and \
                can_filter['extended'] != msg.is_extended_id:
                continue

            # then check for the mask and id
            can_id = can_filter['can_id']
            can_mask = can_filter['can_mask']

            # basically, we compute `msg.arbitration_id & can_mask == can_id & can_mask`
            # by using the faster, but equivalent from below:
            if (can_id ^ msg.arbitration_id) & can_mask == 0:
                return True

        # nothing matched
        return False

    def flush_tx_buffer(self):
        """Discard every message that may be queued in the output buffer(s).
        """
        pass

    def shutdown(self):
        """
        Called to carry out any interface specific cleanup required
        in shutting down a bus. Calls :meth:`~can.BusABC.flush_tx_buffer`.
        """
        self.flush_tx_buffer()

    __metaclass__ = ABCMeta
