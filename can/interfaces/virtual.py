#!/usr/bin/env python
# coding: utf-8

"""
This module implements an OS and hardware independent
virtual CAN interface for testing purposes.

Any VirtualBus instances connecting to the same channel
and reside in the same process will receive the same messages.
"""

import logging
import time
try:
    import queue
except ImportError:
    import Queue as queue

from can.bus import BusABC
from can import CanError

logger = logging.getLogger(__name__)


# Channels are lists of queues, one for each connection
channels = {}


class VirtualBus(BusABC):
    """Virtual CAN bus using an internal message queue for testing."""

    def __init__(self, channel=None, receive_own_messages=False, **config):
        self.channel_info = 'Virtual bus channel %s' % channel
        self.receive_own_messages = receive_own_messages

        # Create a new channel if one does not exist
        if channel not in channels:
            channels[channel] = []

        self.queue = queue.Queue()
        self.channel = channels[channel]
        self.channel.append(self.queue)
        self._open = True

        super(VirtualBus, self).__init__()

    def _check_if_open(self):
        """Raises CanError if the bus is not open.

        Has to be called in every method that accesses the bus.
        """
        if not self._open:
            raise CanError('Operation on closed bus')

    def recv(self, timeout=None):
        self._check_if_open()
        try:
            msg = self.queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

        #logger.log(9, 'Received message:\n%s', msg)
        return msg

    def send(self, msg, timeout=None):
        self._check_if_open()
        msg.timestamp = time.time()
        # Add message to all listening on this channel
        for bus_queue in self.channel:
            if bus_queue is not self.queue or self.receive_own_messages:
                bus_queue.put(msg)
        #logger.log(9, 'Transmitted message:\n%s', msg)

    def shutdown(self):
        self._check_if_open()
        self.channel.remove(self.queue)
        self._open = False
        super(VirtualBus, self).shutdown()
