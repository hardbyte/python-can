#!/usr/bin/env python3
"""
Exposes several methods for transmitting cyclic messages.
20/09/13
"""

import can
import abc
import logging
import sched
import threading
import time

log = logging.getLogger('can.bcm')
log.debug("Loading base broadcast manager functionality")


class CyclicTask(object):
    """
    Abstract Base for all Cyclic Tasks
    """

    @abc.abstractmethod
    def stop(self):
        """Cancel this periodic task.
        """


class CyclicSendTaskABC(CyclicTask):
    """
    Message send task with defined period
    """

    def __init__(self, message, period):
        """
        :param message: The :class:`can.Message` to be sent periodically.
        :param float period: The rate in seconds at which to send the message.
        """
        self.message = message
        self.can_id = message.arbitration_id
        self.period = period
        super(CyclicSendTaskABC, self).__init__()


class LimitedDurationCyclicSendTaskABC(CyclicSendTaskABC):

    def __init__(self, message, period, duration):
        """Message send task with a defined duration and period.

        :param message: The :class:`can.Message` to be sent periodically.
        :param float period: The rate in seconds at which to send the message.
        :param float duration:
            The duration to keep sending this message at given rate.
        """
        super(LimitedDurationCyclicSendTaskABC, self).__init__(message, period)
        self.duration = duration


class RestartableCyclicTaskABC(CyclicSendTaskABC):
    """Adds support for restarting a stopped cyclic task"""

    @abc.abstractmethod
    def start(self):
        """Restart a stopped periodic task.
        """


class ModifiableCyclicTaskABC(CyclicSendTaskABC):
    """Adds support for modifying a periodic message"""

    def modify_data(self, message):
        """Update the contents of this periodically sent message without altering
        the timing.

        :param message: The :class:`~can.Message` with new :attr:`Message.data`.
        """
        self.message = message


class MultiRateCyclicSendTaskABC(CyclicSendTaskABC):
    """Exposes more of the full power of the TX_SETUP opcode.

    Transmits a message `count` times at `initial_period` then
    continues to transmit message at `subsequent_period`.
    """

    def __init__(self, channel, message, count, initial_period, subsequent_period):
        super(MultiRateCyclicSendTaskABC, self).__init__(channel, message, subsequent_period)


class ThreadBasedCyclicSendTask(ModifiableCyclicTaskABC,
                                LimitedDurationCyclicSendTaskABC,
                                RestartableCyclicTaskABC):
    """Fallback cyclic send task using thread."""

    def __init__(self, bus, lock, message, period, duration=None):
        super(ThreadBasedCyclicSendTask, self).__init__(message, period, duration)
        self.bus = bus
        self.lock = lock
        self.stopped = True
        self.thread = None
        self.end_time = time.time() + duration if duration else None
        self.start()

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        if self.thread is None or not self.thread.is_alive():
            name = "Cyclic send task for 0x%X" % (self.message.arbitration_id)
            self.thread = threading.Thread(target=self._run, name=name)
            self.thread.daemon = True
            self.thread.start()

    def _run(self):
        while not self.stopped:
            # Prevent calling bus.send from multiple threads
            with self.lock:
                started = time.time()
                try:
                    self.bus.send(self.message)
                except Exception as exc:
                    log.exception(exc)
                    break
            if self.end_time is not None and time.time() >= self.end_time:
                break
            # Compensate for the time it takes to send the message
            delay = self.period - (time.time() - started)
            time.sleep(max(0.0, delay))


def send_periodic(bus, message, period):
    """
    Send a message every `period` seconds on the given channel.

    """
    return can.interface.CyclicSendTask(bus, message, period)
