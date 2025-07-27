import logging
import queue
from threading import Thread

from .can_8dev_usb_utils import *

logger = logging.getLogger(__name__)

try:
    import usb.core
    import usb.util
except ImportError:
    logger.warning(
        "The PyUSB module is not installed. Install it using `python3 -m pip install pyusb`"
    )


class Can8DevUSBDevice:
    cmd_rx_ep: usb.core.Endpoint
    cmd_tx_ep: usb.core.Endpoint
    data_rx_ep: usb.core.Endpoint
    data_tx_ep: usb.core.Endpoint
    serial_number: str
    _close: bool
    _rx_queue: queue.Queue
    _recv_thread: Thread

    def __init__(self, serial_number=None):
        if serial_number is not None:
            dev = usb.core.find(
                idVendor=USB_8DEV_VENDOR_ID,
                idProduct=USB_8DEV_PRODUCT_ID,
                serial_number=serial_number,
            )
        else:
            dev = usb.core.find(
                idVendor=USB_8DEV_VENDOR_ID, idProduct=USB_8DEV_PRODUCT_ID
            )

        if dev is None:
            raise ValueError(
                "8Devices CAN interface not found! Serial number provided: %s"
                % serial_number
            )

        self.serial_number = dev.serial_number

        dev.reset()
        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        dev.set_configuration()

        # get an endpoint instance
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]

        self.cmd_rx_ep: usb.core.Endpoint = usb.util.find_descriptor(
            intf, bEndpointAddress=USB_8DEV_ENDP_CMD_RX
        )
        self.cmd_tx_ep: usb.core.Endpoint = usb.util.find_descriptor(
            intf, bEndpointAddress=USB_8DEV_ENDP_CMD_TX
        )
        self.data_rx_ep: usb.core.Endpoint = usb.util.find_descriptor(
            intf, bEndpointAddress=USB_8DEV_ENDP_DATA_RX
        )
        self.data_tx_ep: usb.core.Endpoint = usb.util.find_descriptor(
            intf, bEndpointAddress=USB_8DEV_ENDP_DATA_TX
        )

        if (
            self.cmd_rx_ep is None
            or self.cmd_tx_ep is None
            or self.data_rx_ep is None
            or self.data_tx_ep is None
        ):
            raise ValueError("Could not configure 8Devices CAN endpoints!")

        self._rx_queue = queue.Queue(MAX_8DEV_RECV_QUEUE)

    def _recv_thread_loop(self):
        while True:
            byte_buffer = bytes()
            try:
                # We must read the full possible buffer size each iteration or we risk a buffer overrun exception losing data.
                byte_buffer = self.data_rx_ep.read(512, 0).tobytes()
            except Exception:
                pass
            for i in range(0, len(byte_buffer), 21):
                # We could have read multiple frames in a single bulk xfer
                self._rx_queue.put(Can8DevRxFrame(byte_buffer[i : i + 21]))
            if self._close:
                return

    def _start_recv_thread(self):
        self._close = False
        self._recv_thread = Thread(target=self._recv_thread_loop, daemon=True)
        self._recv_thread.start()

    def _stop_recv_thread(self):
        self._close = True

    def send_command(self, cmd: Can8DevCommandFrame):
        self.cmd_tx_ep.write(cmd.to_bytes())
        return Can8DevCommandFrame.from_bytes(self.cmd_rx_ep.read(16))

    def open(
        self,
        phase_seg1: int,
        phase_seg2: int,
        sjw: int,
        brp: int,
        loopback: bool = False,
        listenonly: bool = False,
        oneshot: bool = False,
    ):
        self.send_command(Can8DevCommandFrame(Can8DevCommand.USB_8DEV_RESET))
        open_command = can_8dev_open_frame(
            phase_seg1, phase_seg2, sjw, brp, loopback, listenonly, oneshot
        )
        if self.send_command(open_command).opt1 == 0:
            self._start_recv_thread()
            return True
        else:
            return False

    def close(self):
        self._stop_recv_thread()
        close_command = Can8DevCommand.USB_8DEV_CLOSE
        self.send_command(Can8DevCommandFrame(close_command))

    def recv(self, timeout=None):
        try:
            return self._rx_queue.get(True, timeout=timeout / 1000)
        except queue.Empty:
            return None

    def send(self, tx_frame: Can8DevTxFrame, timeout=None):
        self.data_tx_ep.write(tx_frame.to_bytes(), timeout)

    def get_version(self):
        cmd_response = self.send_command(
            Can8DevCommandFrame(Can8DevCommand.USB_8DEV_GET_SOFTW_HARDW_VER)
        )
        version = int.from_bytes(cmd_response.data[0:4], byteorder="big")
        return version

    def get_firmware_version(self):
        version = self.get_version()
        return "%d.%d" % ((version >> 24) & 0xFF, (version >> 16) & 0xFF)

    def get_serial_number(self):
        return self.serial_number
