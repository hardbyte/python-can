#!/usr/bin/env python

"""
Unittest for ixxat interface.

Run only this test:
python setup.py test --addopts "--verbose -s test/test_interface_ixxat.py"
"""

import logging
import time
import unittest

import can

logger = logging.getLogger("can.ixxat")
default_test_bitrate = 250_000
default_test_msg = can.Message(arbitration_id=0xC0FFEE, dlc=6, data=[0x70, 0x79, 0x74, 0x68, 0x6F, 0x6E])


class LogCaptureHandler(logging.Handler):
    """
    Allows a test case to get access to the logs raised in another module
    """

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())

    def get_records(self):
        return self.records


class TestSoftwareCase(unittest.TestCase):
    """
    Test cases that test the software only and do not rely on an existing/connected hardware.
    """

    def setUp(self):
        self.log_capture = LogCaptureHandler()
        log = logging.getLogger("can.ixxat")
        log.addHandler(self.log_capture)
        log.setLevel(logging.INFO)
        try:
            bus = can.Bus(interface="ixxat", channel=0, bitrate=default_test_bitrate)
            bus.shutdown()
        except can.CanInterfaceNotImplementedError as exc:
            raise unittest.SkipTest("not available on this platform") from exc

    def tearDown(self):
        logging.getLogger("can.ixxat").removeHandler(self.log_capture)

    def test_bus_creation(self):
        # channel must be >= 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=-1, bitrate=default_test_bitrate)

        # rx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=0, rx_fifo_size=0, bitrate=default_test_bitrate)

        # tx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=0, tx_fifo_size=0, bitrate=default_test_bitrate)


class TestHardwareCase(unittest.TestCase):
    """
    Test cases that rely on an existing/connected hardware.
    """

    def setUp(self):
        self.log_capture = LogCaptureHandler()
        logging.getLogger("can.ixxat").addHandler(self.log_capture)
        try:
            bus = can.Bus(interface="ixxat", channel=0)
            self.clock_frequency = bus.clock_frequency
            bus.shutdown()
        except can.CanInterfaceNotImplementedError as exc:
            raise unittest.SkipTest("not available on this platform") from exc

    def tearDown(self):
        logging.getLogger("can.ixxat").removeHandler(self.log_capture)

    def test_bus_creation_standard_bitrate(self):
        bus = can.Bus(interface="ixxat", channel=0, bitrate=default_test_bitrate)
        bus.shutdown()

    def test_bus_creation_arbitrary_bitrate(self):
        target_bitrate = 444_444
        with can.Bus(interface="ixxat", channel=0, bitrate=target_bitrate) as bus:
            timing = bus._status().sBtpSdr
            bus_timing = can.BitTiming(self.clock_frequency, timing.dwBPS, timing.wTS1, timing.wTS2, timing.wSJW)
            self.assertEqual(
                target_bitrate,
                bus_timing.bitrate,
                "\n".join(
                    (
                        "The Hardware Configured bitrate does not match the desired bitrate",
                        "Desired: %s" % target_bitrate,
                        "Hardware Setting: %s" % bus_timing.bitrate,
                    )
                ),
            )

    def test_bus_creation_invalid_bitrate(self):
        with self.assertRaises(ValueError):
            bus = can.Bus(interface="ixxat", channel=0, bitrate=2_000_000)
            bus.shutdown()

    def test_bus_creation_timing_arg(self):
        # try:
        timing_obj = can.BitTiming.from_bitrate_and_segments(
            self.clock_frequency, default_test_bitrate, tseg1=13, tseg2=2, sjw=1
        )
        bus = can.Bus(interface="ixxat", channel=0, timing=timing_obj)
        bus.shutdown()
        # except can.CanInterfaceNotImplementedError:
        #     raise unittest.SkipTest("not available on this platform")

    def test_bus_creation_deprecated_timing_args(self):
        # try:
        bus = can.Bus(interface="ixxat", channel=0, bitrate=default_test_bitrate, sjw_abr=1, tseg1_abr=13, tseg2_abr=2)
        bus.shutdown()
        # except can.CanInterfaceNotImplementedError:
        #     raise unittest.SkipTest("not available on this platform")

    def test_send_single(self):
        with can.Bus(interface="ixxat", channel=0, bitrate=default_test_bitrate, receive_own_messages=True) as bus:
            bus.send(default_test_msg)
            response = bus.recv(0.1)

        if response:
            self.assertEqual(
                response.arbitration_id,
                default_test_msg.arbitration_id,
                "The Arbitration ID of the sent message and the received message do not match",
            )
            self.assertEqual(
                response.data,
                default_test_msg.data,
                "The Data fields of the sent message and the received message do not match",
            )
        else:
            captured_logs = self.log_capture.get_records()
            if captured_logs[-1] == "CAN bit error":
                raise can.exceptions.CanOperationError(
                    "CAN bit error - Ensure you are connected to a "
                    "properly terminated bus configured at %s bps" % default_test_bitrate
                )

            elif captured_logs[-1] == "CAN ack error":
                raise can.exceptions.CanOperationError(
                    "CAN ack error - Ensure there is at least one other (silent) node to provide ack signals",
                )
            else:
                raise ValueError(
                    "\n".join(
                        (
                            "Response does not match the sent message",
                            "Sent: %s" % default_test_msg,
                            "Received: %s" % response,
                            "Last Caputred Log: %s" % captured_logs[-1],
                            "Ensure hardware tests are run on a bus with no other traffic.",
                        )
                    )
                )

    def test_send_periodic(self):
        with can.Bus(interface="ixxat", channel=0, bitrate=default_test_bitrate, receive_own_messages=True) as bus:
            # setup Notifier and BufferedReader instances to receive messages
            msg_rx_buffer = can.BufferedReader()
            msg_notifier = can.Notifier(bus, [msg_rx_buffer])

            # setup periodic send task
            task = bus.send_periodic(default_test_msg, 0.2)
            assert isinstance(task, can.CyclicSendTaskABC)
            time.sleep(2)
            task.stop()

            # clean up the Notifier and BufferedReader instances
            msg_notifier.stop()
            msg_rx_buffer.stop()

        messages = []
        while msg := msg_rx_buffer.get_message(timeout=0.1):
            messages.append(msg)

        if messages:
            self.assertGreaterEqual(len(messages), 9)  # should be 10 messages - give ±1 margin for timing issues
            self.assertLessEqual(len(messages), 11)  # should be 10 messages - give ±1 margin for timing issues
            self.assertEqual(
                messages[-1].arbitration_id,
                default_test_msg.arbitration_id,
                "The Arbitration ID of the sent message and the received message do not match",
            )
            self.assertEqual(
                messages[-1].data,
                default_test_msg.data,
                "The Data fields of the sent message and the received message do not match",
            )
        else:
            raise can.exceptions.CanOperationError(
                "No messages have been received"
            )

    def test_bus_creation_invalid_channel(self):
        # non-existent channel -> use arbitrary high value
        with self.assertRaises(can.CanInitializationError):
            can.Bus(interface="ixxat", channel=0xFFFF, bitrate=default_test_bitrate)

    def test_send_after_shutdown(self):
        bus = can.Bus(interface="ixxat", channel=0, bitrate=default_test_bitrate)
        bus.shutdown()
        with self.assertRaises(can.CanOperationError):
            bus.send(default_test_msg)


if __name__ == "__main__":
    unittest.main()
