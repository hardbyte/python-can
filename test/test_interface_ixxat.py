"""
Unittest for ixxat VCI4 interface.

Run only this test:
python setup.py test --addopts "--verbose -s test/test_interface_ixxat.py"
"""

from copy import copy
import logging
import time
import unittest

import can
import can.interfaces.ixxat.canlib as ixxat_canlib_module
from can.interfaces.ixxat import get_ixxat_hwids
from can.interfaces.ixxat.canlib import _format_can_status


logger = logging.getLogger("can.ixxat")
default_test_bitrate = 250_000
default_test_msg = can.Message(
    arbitration_id=0xC0FFEE, dlc=6, data=[0x70, 0x79, 0x74, 0x68, 0x6F, 0x6E]
)


TESTING_DEBUG_LEVEL = logging.INFO


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
    Test cases that test the python-can software only
    """

    def setUp(self):
        self.log_capture = LogCaptureHandler()
        # ensure we test as if there is no driver even if it is installed
        self._canlib = ixxat_canlib_module._canlib
        ixxat_canlib_module._canlib = None
        log = logging.getLogger("can.ixxat")
        log.addHandler(self.log_capture)
        log.setLevel(TESTING_DEBUG_LEVEL)

    def tearDown(self):
        # replace the driver reference for the other tests
        ixxat_canlib_module._canlib = self._canlib
        logging.getLogger("can.ixxat").removeHandler(self.log_capture)

    def test_interface_detection(self):  # driver missing test
        if_list = can.detect_available_configs("ixxat")
        self.assertIsInstance(if_list, list)

    def test_get_ixxat_hwids(self):  # driver missing test
        hwid_list = get_ixxat_hwids()
        self.assertIsInstance(hwid_list, list)

    def test_format_can_status(self):
        self.assertIsInstance(_format_can_status(0x01), str)
        self.assertIsInstance(_format_can_status(0x02), str)
        self.assertIsInstance(_format_can_status(0x04), str)
        self.assertIsInstance(_format_can_status(0x08), str)
        self.assertIsInstance(_format_can_status(0x10), str)
        self.assertIsInstance(_format_can_status(0x20), str)


class TestDriverCase(unittest.TestCase):
    """
    Test cases that do not rely on an existing/connected hardware, but test the software and driver communication.
    The VCI 4 driver must be installed for these tests
    """

    def setUp(self):
        self.log_capture = LogCaptureHandler()
        log = logging.getLogger("can.ixxat")
        log.addHandler(self.log_capture)
        log.setLevel(TESTING_DEBUG_LEVEL)
        try:
            # if the driver
            bus = can.Bus(interface="ixxat", channel=0, bitrate=default_test_bitrate)
            bus.shutdown()
        except can.CanInterfaceNotImplementedError as exc:
            raise unittest.SkipTest("not available on this platform") from exc

    def tearDown(self):
        logging.getLogger("can.ixxat").removeHandler(self.log_capture)

    def test_interface_detection(self):  # driver present test
        if_list = can.detect_available_configs("ixxat")
        self.assertIsInstance(if_list, list)

    def test_get_ixxat_hwids(self):  # driver present test
        hwid_list = get_ixxat_hwids()
        self.assertIsInstance(hwid_list, list)

    def test_bus_creation_std(self):
        # channel must be >= 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=-1, bitrate=default_test_bitrate)

        # rx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(
                interface="ixxat",
                channel=0,
                rx_fifo_size=0,
                bitrate=default_test_bitrate,
            )

        # tx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(
                interface="ixxat",
                channel=0,
                tx_fifo_size=0,
                bitrate=default_test_bitrate,
            )

    def test_bus_creation_fd(self):
        # channel must be >= 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", fd=True, channel=-1)

        # rx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(
                interface="ixxat",
                fd=True,
                channel=0,
                rx_fifo_size=0,
                bitrate=default_test_bitrate,
            )

        # tx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(
                interface="ixxat",
                fd=True,
                channel=0,
                tx_fifo_size=0,
                bitrate=default_test_bitrate,
            )


class TestHardwareCaseStd(unittest.TestCase):
    """
    Test cases that rely on an existing/connected hardware.
    """

    def setUp(self):
        self.log_capture = LogCaptureHandler()
        log = logging.getLogger("can.ixxat")
        log.addHandler(self.log_capture)
        log.setLevel(TESTING_DEBUG_LEVEL)
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
            bus_timing = can.BitTiming(
                self.clock_frequency,
                timing.dwBPS,
                timing.wTS1,
                timing.wTS2,
                timing.wSJW,
            )
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
        bus = can.Bus(
            interface="ixxat",
            channel=0,
            bitrate=default_test_bitrate,
            sjw_abr=1,
            tseg1_abr=13,
            tseg2_abr=2,
        )
        bus.shutdown()
        # except can.CanInterfaceNotImplementedError:
        #     raise unittest.SkipTest("not available on this platform")

    def test_send_single(self):
        with can.Bus(
            interface="ixxat",
            channel=0,
            bitrate=default_test_bitrate,
            receive_own_messages=True,
        ) as bus:
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
                    "properly terminated bus configured at %s bps"
                    % default_test_bitrate
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
        with can.Bus(
            interface="ixxat",
            channel=0,
            bitrate=default_test_bitrate,
            receive_own_messages=True,
        ) as bus:
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
            self.assertGreaterEqual(
                len(messages), 9
            )  # should be 10 messages - give ±1 margin for timing issues
            self.assertLessEqual(
                len(messages), 11
            )  # should be 10 messages - give ±1 margin for timing issues
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
            raise can.exceptions.CanOperationError("No messages have been received")

    def test_send_periodic_busabc_fallback(self):
        with can.Bus(
            interface="ixxat",
            channel=0,
            bitrate=default_test_bitrate,
            receive_own_messages=True,
        ) as bus:
            # setup Notifier and BufferedReader instances to receive messages
            bus._interface_scheduler_capable = False

            # setup periodic send task
            task = bus.send_periodic(default_test_msg, 0.2)
            assert isinstance(task, can.CyclicSendTaskABC)
            time.sleep(2)
            task.stop()

    def test_multiple_bus_instances(self):
        """This tests the access of multiple bus instances to the same adapter using the VCI 4 driver"""

        with can.Bus(
            interface="ixxat",
            channel=0,
            bitrate=default_test_bitrate,
            receive_own_messages=True,
        ) as bus1:
            with can.Bus(
                interface="ixxat",
                channel=0,
                bitrate=default_test_bitrate,
                receive_own_messages=True,
            ) as bus2:
                with can.Bus(
                    interface="ixxat",
                    channel=0,
                    bitrate=default_test_bitrate,
                    receive_own_messages=True,
                ) as bus3:
                    bus1_msg = copy(default_test_msg)
                    bus1_msg.arbitration_id = bus1_msg.arbitration_id | 0x1000000
                    bus2_msg = copy(default_test_msg)
                    bus2_msg.arbitration_id = bus2_msg.arbitration_id | 0x2000000
                    bus3_msg = copy(default_test_msg)
                    bus3_msg.arbitration_id = bus3_msg.arbitration_id | 0x3000000
                    # send a message on bus 1, and try to receive it on bus 2 and bus 3
                    bus1.send(bus1_msg)
                    bus1.recv(0.25)  # discard own message
                    response2from1 = bus2.recv(0.25)
                    response3from1 = bus3.recv(0.25)
                    # send the same message on bus 2, and try to receive it on bus 1 and bus 3
                    bus2.send(bus2_msg)
                    bus2.recv(0.25)  # discard own message
                    response1from2 = bus1.recv(0.25)
                    response3from2 = bus3.recv(0.25)
                    # send the same message on bus 3, and try to receive it on bus 1 and bus 2
                    bus3.send(bus3_msg)
                    bus3.recv(0.25)  # discard own message
                    response1from3 = bus1.recv(0.25)
                    response2from3 = bus2.recv(0.25)

        if response2from1 and response3from1 and response1from2 and response3from2 and response1from3 and response2from3:
            bus_checks = {
                "sent from bus instance 1, received on bus instance 2": (response2from1, bus1_msg),
                "sent from bus instance 1, received on bus instance 3": (response3from1, bus1_msg),
                "sent from bus instance 2, received on bus instance 1": (response1from2, bus2_msg),
                "sent from bus instance 2, received on bus instance 3": (response3from2, bus2_msg),
                "sent from bus instance 3, received on bus instance 1": (response1from3, bus3_msg),
                "sent from bus instance 3, received on bus instance 3": (response2from3, bus3_msg),
             }
            for case, msg_objects in bus_checks.items():
                self.assertEqual(
                    msg_objects[0].arbitration_id,
                    msg_objects[1].arbitration_id,
                    f"The Arbitration ID of the messages {case} do not match",
                )
                self.assertEqual(
                    msg_objects[0].data,
                    msg_objects[1].data,
                    f"The Data fields of the messages {case} do not match.",
                )
        else:
            captured_logs = self.log_capture.get_records()
            if captured_logs[-1] == "CAN bit error":
                raise can.exceptions.CanOperationError(
                    "CAN bit error - Ensure you are connected to a properly "
                    "terminated bus configured at {default_test_bitrate} bps"
                )

            elif captured_logs[-1] == "CAN ack error":
                raise can.exceptions.CanOperationError(
                    "CAN ack error - Ensure there is at least one other (silent) node to provide ack signals",
                )
            else:
                raise ValueError(
                    "\n".join(
                        (
                            "At least one response does not match the sent message:",
                            f"Sent on bus instance 1: {bus1_msg}",
                            f" - Received on bus instance 2: {response2from1}",
                            f" - Received on bus instance 3: {response3from1}",
                            f"Sent on bus instance 2: {bus2_msg}",
                            f" - Received on bus instance 1: {response1from2}",
                            f" - Received on bus instance 3: {response3from2}",
                            f"Sent on interface 3: {bus3_msg}",
                            f" - Received on interface 1: {response1from3}",
                            f" - Received on interface 2: {response2from3}",
                            f"Last Caputred Log: {captured_logs[-1]}",
                            "Ensure hardware tests are run on a bus with no other traffic.",
                        )
                    )
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


class HardwareTestCaseFd(unittest.TestCase):
    """
    Test cases that rely on an existing/connected hardware with CAN FD capability
    """

    def setUp(self):
        try:
            bus = can.Bus(interface="ixxat", fd=True, channel=0)
            bus.shutdown()
        except can.CanInterfaceNotImplementedError as exc:
            raise unittest.SkipTest("not available on this platform") from exc
        except can.CanInitializationError as exc:
            raise unittest.SkipTest("connected hardware is not FD capable") from exc

    def test_bus_creation(self):
        # non-existent channel -> use arbitrary high value
        with self.assertRaises(can.CanInitializationError):
            can.Bus(
                interface="ixxat", fd=True, channel=0xFFFF, bitrate=default_test_bitrate
            )

    def test_send_after_shutdown(self):
        with can.Bus(
            interface="ixxat", fd=True, channel=0, bitrate=default_test_bitrate
        ) as bus:
            with self.assertRaises(can.CanOperationError):
                bus.send(can.Message(arbitration_id=0x3FF, dlc=0))


if __name__ == "__main__":
    unittest.main()
