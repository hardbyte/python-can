# -*- coding: utf-8 -*-

"""
This module implements an OS and hardware independent
virtual CAN interface for testing purposes.

Any VirtualBus instances connecting to the same channel
will get the same messages. Sent messages will also be
echoed back to the same bus.
"""

import logging
import time
try:
    import queue
except ImportError:
    import Queue as queue
from can.bus import BusABC


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Channels are lists of queues, one for each connection
channels = {}


class VirtualBus(BusABC):
    """Virtual CAN bus using an internal message queue for testing."""

    def __init__(self, channel=None, **config):
        self.channel_info = 'Virtual bus channel %s' % channel

        # Create a new channel if one does not exist
        if channel not in channels:
            channels[channel] = []

        self.queue = queue.Queue()
        self.channel = channels[channel]
        self.channel.append(self.queue)

    def recv(self, timeout=None):
        try:
            msg = self.queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

        logger.log(9, 'Received message:\n%s', msg)
        return msg

    def send(self, msg, timeout=None):
        msg.timestamp = time.time()
        # Add message to all listening on this channel
        for bus_queue in self.channel:
            bus_queue.put(msg)
        logger.log(9, 'Transmitted message:\n%s', msg)

    def shutdown(self):
        self.channel.remove(self.queue)
