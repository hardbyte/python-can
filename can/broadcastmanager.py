#!/usr/bin/env python3
"""
Exposes several methods for transmitting cyclic messages.
20/09/13
"""

import can
import abc
import logging

log = logging.getLogger('can.bcm')
log.debug("Loading base broadcast manager functionality")


class CyclicSendTaskABC(object):

    def __init__(self, message, period):
        """
        :param message: The :class:`can.Message` to be sent periodically.
        :param float period: The rate in seconds at which to send the message.
        """
        self.can_id = message.arbitration_id
        self.period = period

    @abc.abstractmethod
    def stop(self):
        """Cancel this periodic task.
        """

    @abc.abstractmethod
    def start(self):
        """Restart a stopped periodic task.
        """


class ModifiableCyclicTaskABC(CyclicSendTaskABC):
    """Adds support for modifying a periodic message"""

    @abc.abstractmethod
    def modify_data(self, message):
        """Update the contents of this periodically sent message without altering
        the timing.

        :param message: The :class:`~can.Message` with new :attr:`Message.data`.
        """


class MultiRateCyclicSendTaskABC(CyclicSendTaskABC):
    """Exposes more of the full power of the TX_SETUP opcode.

    Transmits a message `count` times at `initial_period` then
    continues to transmit message at `subsequent_period`.
    """

    def __init__(self, channel, message, count, initial_period, subsequent_period):
        super(MultiRateCyclicSendTaskABC, self).__init__(channel, message, subsequent_period)


def send_periodic(bus, message, period):
    """
    Send a message every `period` seconds on the given channel.

    """
    return can.interface.CyclicSendTask(bus, message, period)
