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
from threading import RLock
from random import randint

from can.bus import BusABC

logger = logging.getLogger(__name__)


# Channels are lists of queues, one for each connection
channels = {}
channels_lock = RLock()


class VirtualBus(BusABC):
    """
    A virtual CAN bus using an internal message queue. It can be
    used for example for testing.

    In this interface, a channel is an arbitrary object used as
    an identifier for connected buses.

    Implements :meth:`can.BusABC._detect_available_configs`; see
    :meth:`can.VirtualBus._detect_available_configs` for how it
    behaves here.
    """

    def __init__(self, channel=None, receive_own_messages=False, **config):
        config.update({'receive_own_messages': receive_own_messages})
        super(VirtualBus, self).__init__(channel=channel, **config)

        # the channel identifier may be an arbitrary object
        self.channel_id = channel
        self.channel_info = 'Virtual bus channel %s' % self.channel_id
        self.receive_own_messages = receive_own_messages

        with channels_lock:

            # Create a new channel if one does not exist
            if self.channel_id not in channels:
                channels[self.channel_id] = []
            self.channel = channels[self.channel_id]

            self.queue = queue.Queue()
            self.channel.append(self.queue)

    def _recv_internal(self, timeout=None):
        try:
            msg = self.queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None, False
        else:
            #logger.log(9, 'Received message:\n%s', msg)
            return msg, False

    def send(self, msg, timeout=None):
        msg.timestamp = time.time()
        # Add message to all listening on this channel
        for bus_queue in self.channel:
            if bus_queue is not self.queue or self.receive_own_messages:
                bus_queue.put(msg)
        #logger.log(9, 'Transmitted message:\n%s', msg)

    def shutdown(self):
        with channels_lock:
            self.channel.remove(self.queue)

            # remove if empty
            if not self.channel:
                del channels[self.channel_id]

    @staticmethod
    def _detect_available_configs():
        """
        Returns all currently used channels as well as
        one other currently unused channel.

        .. note::

            This method will run into problems if thousands of
            autodetected busses are used at once.

        """
        with channels_lock:
            available_channels = list(channels.keys())

        # find a currently unused channel
        get_extra = lambda: "channel-{}".format(randint(0, 9999))
        extra = get_extra()
        while extra in available_channels:
            extra = get_extra()

        available_channels += [extra]

        return [
            {'interface': 'virtual', 'channel': channel}
            for channel in available_channels
        ]
