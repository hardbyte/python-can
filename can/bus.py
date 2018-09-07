#!/usr/bin/env python
# coding: utf-8

"""
Contains the ABC bus implementation and its documentation.
"""

from __future__ import print_function, absolute_import

from abc import ABCMeta, abstractmethod
import logging
import threading
from time import time
from collections import namedtuple

from .broadcastmanager import ThreadBasedCyclicSendTask

LOG = logging.getLogger(__name__)

BusState = namedtuple('BusState', 'ACTIVE, PASSIVE, ERROR')


class BusABC(object):
    """The CAN Bus Abstract Base Class that serves as the basis
    for all concrete interfaces.

    This class may be used as an iterator over the received messages.
    """

    #: a string describing the underlying bus and/or channel
    channel_info = 'unknown'

    #: Log level for received messages
    RECV_LOGGING_LEVEL = 9

    @abstractmethod
    def __init__(self, channel, can_filters=None, **config):
        """Construct and open a CAN bus instance of the specified type.

        Subclasses should call though this method with all given parameters
        as it handles generic tasks like applying filters.

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

        :type timeout: float or None
        :param timeout:
            seconds to wait for a message or None to wait indefinitely

        :rtype: can.Message or None
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
                LOG.log(self.RECV_LOGGING_LEVEL, 'Received: %s', msg)
                return msg

            # if not, and timeout is None, try indefinitely
            elif timeout is None:
                continue

            # try next one only if there still is time, and with
            # reduced timeout
            else:

                time_left = timeout - (time() - start)

                if time_left > 0:
                    continue
                else:
                    return None

    def _recv_internal(self, timeout):
        """
        Read a message from the bus and tell whether it was filtered.
        This methods may be called by :meth:`~can.BusABC.recv`
        to read a message multiple times if the filters set by
        :meth:`~can.BusABC.set_filters` do not match and the call has
        not yet timed out.

        New implementations should always override this method instead of
        :meth:`~can.BusABC.recv`, to be able to take advantage of the
        software based filtering provided by :meth:`~can.BusABC.recv`
        as a fallback. This method should never be called directly.

        .. note::

            This method is not an `@abstractmethod` (for now) to allow older
            external implementations to continue using their existing
            :meth:`~can.BusABC.recv` implementation.

        .. note::

            The second return value (whether filtering was already done) may
            change over time for some interfaces, like for example in the
            Kvaser interface. Thus it cannot be simplified to a constant value.

        :param float timeout: seconds to wait for a message,
                              see :meth:`~can.BusABC.send`

        :rtype: tuple[can.Message, bool] or tuple[None, bool]
        :return:
            1.  a message that was read or None on timeout
            2.  a bool that is True if message filtering has already
                been done and else False

        :raises can.CanError:
            if an error occurred while reading
        :raises NotImplementedError:
            if the bus provides it's own :meth:`~can.BusABC.recv`
            implementation (legacy implementation)

        """
        raise NotImplementedError("Trying to read from a write only bus?")

    @abstractmethod
    def send(self, msg, timeout=None):
        """Transmit a message to the CAN bus.

        Override this method to enable the transmit path.

        :param can.Message msg: A message object.

        :type timeout: float or None
        :param timeout:
            If > 0, wait up to this many seconds for message to be ACK'ed or
            for transmit queue to be ready depending on driver implementation.
            If timeout is exceeded, an exception will be raised.
            Might not be supported by all interfaces.
            None blocks indefinitly.

        :raises can.CanError:
            if the message could not be sent
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
        :rtype: can.broadcastmanager.CyclicSendTaskABC

        .. note::

            Note the duration before the message stops being sent may not
            be exactly the same as the duration specified by the user. In
            general the message will be sent at the given rate until at
            least **duration** seconds.

        """
        if not hasattr(self, "_lock_send_periodic"):
            # Create a send lock for this bus
            self._lock_send_periodic = threading.Lock()
        return ThreadBasedCyclicSendTask(
            self, self._lock_send_periodic, msg, period, duration)

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
        """
        Modify the filters of this bus. See :meth:`~can.BusABC.set_filters`
        for details.
        """
        return self._filters

    @filters.setter
    def filters(self, filters):
        self.set_filters(filters)

    def set_filters(self, filters=None):
        """Apply filtering to all messages received by this Bus.

        All messages that match at least one filter are returned.
        If `filters` is `None` or a zero length sequence, all
        messages are matched.

        Calling without passing any filters will reset the applied
        filters to `None`.

        :param filters:
            A iterable of dictionaries each containing a "can_id",
            a "can_mask", and an optional "extended" key.

            >>> [{"can_id": 0x11, "can_mask": 0x21, "extended": False}]

            A filter matches, when
            ``<received_can_id> & can_mask == can_id & can_mask``.
            If ``extended`` is set as well, it only matches messages where
            ``<received_is_extended> == extended``. Else it matches every
            messages based only on the arbitration ID and mask.
        """
        self._filters = filters or None
        self._apply_filters(self._filters)

    def _apply_filters(self, filters):
        """
        Hook for applying the filters to the underlying kernel or
        hardware if supported/implemented by the interface.

        :param Iterator[dict] filters:
            See :meth:`~can.BusABC.set_filters` for details.
        """
        pass

    def _matches_filters(self, msg):
        """Checks whether the given message matches at least one of the
        current filters. See :meth:`~can.BusABC.set_filters` for details
        on how the filters work.

        This method should not be overridden.

        :param can.Message msg:
            the message to check if matching
        :rtype: bool
        :return: whether the given message matches at least one filter
        """

        # if no filters are set, all messages are matched
        if self._filters is None:
            return True

        for _filter in self._filters:
            # check if this filter even applies to the message
            if 'extended' in _filter and \
                    _filter['extended'] != msg.is_extended_id:
                continue

            # then check for the mask and id
            can_id = _filter['can_id']
            can_mask = _filter['can_mask']

            # basically, we compute
            # `msg.arbitration_id & can_mask == can_id & can_mask`
            # by using the shorter, but equivalent from below:
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
        in shutting down a bus.
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    @property
    def state(self):
        """
        Return the current state of the hardware
        :return: ACTIVE, PASSIVE or ERROR
        :rtype: NamedTuple
        """
        return BusState.ACTIVE

    @state.setter
    def state(self, new_state):
        """
        Set the new state of the hardware
        :param new_state: BusState.ACTIVE, BusState.PASSIVE or BusState.ERROR
        """
        raise NotImplementedError("Property is not implemented.")

    @staticmethod
    def _detect_available_configs():
        """Detect all configurations/channels that this interface could
        currently connect with.

        This might be quite time consuming.

        May not to be implemented by every interface on every platform.

        :rtype: Iterator[dict]
        :return: an iterable of dicts, each being a configuration suitable
                 for usage in the interface's bus constructor.
        """
        raise NotImplementedError()

    __metaclass__ = ABCMeta
