# coding: utf-8

"""
Exposes several methods for transmitting cyclic messages.

The main entry point to these classes should be through
:meth:`can.BusABC.send_periodic`.
"""

from typing import Optional, Sequence, Tuple, Union

import can.typechecking

import abc
import logging
import threading
import time

import can

# try to import win32event for event-based cyclic send task(needs pywin32 package)
try:
    import win32event

    HAS_EVENTS = True
except ImportError:
    HAS_EVENTS = False

log = logging.getLogger("can.bcm")


class CyclicTask:
    """
    Abstract Base for all cyclic tasks.
    """

    @abc.abstractmethod
    def stop(self):
        """Cancel this periodic task.

        :raises can.CanError:
            If stop is called on an already stopped task.
        """


class CyclicSendTaskABC(CyclicTask):
    """
    Message send task with defined period
    """

    def __init__(
        self, messages: Union[Sequence[can.Message], can.Message], period: float
    ):
        """
        :param messages:
            The messages to be sent periodically.
        :param period: The rate in seconds at which to send the messages.
        """
        messages = self._check_and_convert_messages(messages)

        # Take the Arbitration ID of the first element
        self.arbitration_id = messages[0].arbitration_id
        self.period = period
        self.messages = messages

    @staticmethod
    def _check_and_convert_messages(
        messages: Union[Sequence[can.Message], can.Message]
    ) -> Tuple[can.Message, ...]:
        """Helper function to convert a Message or Sequence of messages into a
        tuple, and raises an error when the given value is invalid.

        Performs error checking to ensure that all Messages have the same
        arbitration ID and channel.

        Should be called when the cyclic task is initialized
        """
        if not isinstance(messages, (list, tuple)):
            if isinstance(messages, can.Message):
                messages = [messages]
            else:
                raise ValueError("Must be either a list, tuple, or a Message")
        if not messages:
            raise ValueError("Must be at least a list or tuple of length 1")
        messages = tuple(messages)

        all_same_id = all(
            message.arbitration_id == messages[0].arbitration_id for message in messages
        )
        if not all_same_id:
            raise ValueError("All Arbitration IDs should be the same")

        all_same_channel = all(
            message.channel == messages[0].channel for message in messages
        )
        if not all_same_channel:
            raise ValueError("All Channel IDs should be the same")

        return messages


class LimitedDurationCyclicSendTaskABC(CyclicSendTaskABC):
    def __init__(
        self,
        messages: Union[Sequence[can.Message], can.Message],
        period: float,
        duration: Optional[float],
    ):
        """Message send task with a defined duration and period.

        :param messages:
            The messages to be sent periodically.
        :param period: The rate in seconds at which to send the messages.
        :param duration:
            Approximate duration in seconds to continue sending messages. If
            no duration is provided, the task will continue indefinitely.
        """
        super().__init__(messages, period)
        self.duration = duration


class RestartableCyclicTaskABC(CyclicSendTaskABC):
    """Adds support for restarting a stopped cyclic task"""

    @abc.abstractmethod
    def start(self):
        """Restart a stopped periodic task.
        """


class ModifiableCyclicTaskABC(CyclicSendTaskABC):
    """Adds support for modifying a periodic message"""

    def _check_modified_messages(self, messages: Tuple[can.Message, ...]):
        """Helper function to perform error checking when modifying the data in
        the cyclic task.

        Performs error checking to ensure the arbitration ID and the number of
        cyclic messages hasn't changed.

        Should be called when modify_data is called in the cyclic task.
        """
        if len(self.messages) != len(messages):
            raise ValueError(
                "The number of new cyclic messages to be sent must be equal to "
                "the number of messages originally specified for this task"
            )
        if self.arbitration_id != messages[0].arbitration_id:
            raise ValueError(
                "The arbitration ID of new cyclic messages cannot be changed "
                "from when the task was created"
            )

    def modify_data(self, messages: Union[Sequence[can.Message], can.Message]):
        """Update the contents of the periodically sent messages, without
        altering the timing.

        :param messages:
            The messages with the new :attr:`can.Message.data`.

            Note: The arbitration ID cannot be changed.

            Note: The number of new cyclic messages to be sent must be equal
            to the original number of messages originally specified for this
            task.
        """
        messages = self._check_and_convert_messages(messages)
        self._check_modified_messages(messages)

        self.messages = messages


class MultiRateCyclicSendTaskABC(CyclicSendTaskABC):
    """A Cyclic send task that supports switches send frequency after a set time.
    """

    def __init__(
        self,
        channel: can.typechecking.Channel,
        messages: Union[Sequence[can.Message], can.Message],
        count: int,
        initial_period: float,
        subsequent_period: float,
    ):
        """
        Transmits a message `count` times at `initial_period` then continues to
        transmit messages at `subsequent_period`.

        :param channel: See interface specific documentation.
        :param messages:
        :param count:
        :param initial_period:
        :param subsequent_period:
        """
        super().__init__(messages, subsequent_period)
        self._channel = channel


class ThreadBasedCyclicSendTask(
    ModifiableCyclicTaskABC, LimitedDurationCyclicSendTaskABC, RestartableCyclicTaskABC
):
    """Fallback cyclic send task using thread."""

    def __init__(
        self,
        bus: "can.bus.BusABC",
        lock: threading.Lock,
        messages: Union[Sequence[can.Message], can.Message],
        period: float,
        duration: Optional[float] = None,
    ):
        super().__init__(messages, period, duration)
        self.bus = bus
        self.send_lock = lock
        self.stopped = True
        self.thread = None
        self.end_time = time.perf_counter() + duration if duration else None

        if HAS_EVENTS:
            self.period_ms: int = int(round(period * 1000, 0))
            self.event = win32event.CreateWaitableTimer(None, False, None)

        self.start()

    def stop(self):
        if HAS_EVENTS:
            win32event.CancelWaitableTimer(self.event.handle)
        self.stopped = True

    def start(self):
        self.stopped = False
        if self.thread is None or not self.thread.is_alive():
            name = "Cyclic send task for 0x%X" % (self.messages[0].arbitration_id)
            self.thread = threading.Thread(target=self._run, name=name)
            self.thread.daemon = True

            if HAS_EVENTS:
                win32event.SetWaitableTimer(
                    self.event.handle, 0, self.period_ms, None, None, False
                )

            self.thread.start()

    def _run(self):
        msg_index = 0
        while not self.stopped:
            # Prevent calling bus.send from multiple threads
            with self.send_lock:
                started = time.perf_counter()
                try:
                    self.bus.send(self.messages[msg_index])
                except Exception as exc:
                    log.exception(exc)
                    break
            if self.end_time is not None and time.perf_counter() >= self.end_time:
                break
            msg_index = (msg_index + 1) % len(self.messages)

            if HAS_EVENTS:
                win32event.WaitForSingleObject(self.event.handle, self.period_ms)
            else:
                # Compensate for the time it takes to send the message
                delay = self.period - (time.perf_counter() - started)
                time.sleep(max(0.0, delay))
