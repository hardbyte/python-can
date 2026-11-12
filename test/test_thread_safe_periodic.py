"""Behavioral regressions for default periodic sends on ThreadSafeBus."""

import threading
import unittest
from unittest.mock import patch

import can


class ThreadSafePeriodicTest(unittest.TestCase):
    def check_serialized_sends(self, first_is_periodic):
        first_entered = threading.Event()
        release_first = threading.Event()
        contender_reached = threading.Event()
        second_entered = threading.Event()
        counter_lock = threading.Lock()
        contender_id = None
        active = 0
        maximum_active = 0
        errors = []

        class ObservedRLock:
            """Keep real RLock semantics while exposing an attempted acquisition."""

            def __init__(self):
                self.lock = threading.RLock()

            def __enter__(self):
                if threading.get_ident() == contender_id:
                    contender_reached.set()
                self.lock.acquire()
                return self

            def __exit__(self, *args):
                self.lock.release()

        def mark_contender(message):
            nonlocal contender_id
            contender_id = threading.get_ident()

        first = can.Message(arbitration_id=0x100, data=[1], is_extended_id=False)
        second = can.Message(arbitration_id=0x200, data=[2], is_extended_id=False)
        tasks = []
        manual_thread = None

        with patch("can.thread_safe_bus.RLock", ObservedRLock):
            bus = can.ThreadSafeBus(
                interface="virtual", channel=self.id(), receive_own_messages=True
            )
        backend = bus.__wrapped__
        original_send = backend.send

        def observed_send(msg, timeout=None):
            nonlocal active, maximum_active
            with counter_lock:
                active += 1
                maximum_active = max(maximum_active, active)
            try:
                if msg.arbitration_id == first.arbitration_id:
                    first_entered.set()
                    if not release_first.wait(5):
                        raise TimeoutError("test did not release the first send")
                else:
                    # Unlocked implementations reach the backend; locked ones
                    # signal at attempted acquisition before entering here.
                    contender_reached.set()
                    second_entered.set()
                return original_send(msg, timeout=timeout)
            except BaseException as exc:
                errors.append(exc)
                raise
            finally:
                with counter_lock:
                    active -= 1

        def manual_send():
            try:
                bus.send(first)
            except BaseException as exc:
                errors.append(exc)

        try:
            with patch.object(backend, "send", side_effect=observed_send):
                try:
                    if first_is_periodic:
                        tasks.append(bus.send_periodic(first, 0.01))
                    else:
                        manual_thread = threading.Thread(target=manual_send)
                        manual_thread.start()
                    self.assertTrue(first_entered.wait(5))
                    tasks.append(
                        bus.send_periodic(
                            second, 0.01, modifier_callback=mark_contender
                        )
                    )
                    # A positive barrier works whether the contender reaches
                    # the shared lock or incorrectly enters the backend.
                    self.assertTrue(contender_reached.wait(5))
                    release_first.set()
                    self.assertTrue(second_entered.wait(5))
                finally:
                    release_first.set()
                    for task in tasks:
                        task.stop()
                    if manual_thread is not None:
                        manual_thread.join(5)
                        self.assertFalse(manual_thread.is_alive())
                    for task in tasks:
                        task.thread.join(5)
                        self.assertFalse(task.thread.is_alive())

            self.assertEqual(errors, [])
            self.assertEqual(maximum_active, 1)
            received = []
            while (message := bus.recv(0)) is not None:
                received.append((message.arbitration_id, bytes(message.data)))
            self.assertEqual(set(received), {(0x100, b"\x01"), (0x200, b"\x02")})
        finally:
            bus.shutdown()

    def test_manual_and_periodic_send_do_not_overlap(self):
        self.check_serialized_sends(first_is_periodic=False)

    def test_multiple_periodic_sends_do_not_overlap(self):
        self.check_serialized_sends(first_is_periodic=True)
