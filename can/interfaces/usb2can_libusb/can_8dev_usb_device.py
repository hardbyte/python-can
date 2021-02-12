from enum import Enum
import queue
from threading import Thread

import usb.core
import usb.util

MAX_8DEV_RECV_QUEUE = 128  # Maximum number of slots in the recv queue

USB_8DEV_VENDOR_ID = (
    0x0483
)  # Unfortunately this is actually the ST Microelectronics Vendor ID
USB_8DEV_PRODUCT_ID = 0x1234  # Unfortunately this is pretty bogus
USB_8DEV_PRODUCT_STRING = "USB2CAN converter"  # So we use this instead. Not great.

USB_8DEV_ABP_CLOCK = 32000000

# USB Bulk Endpoint identifiers

USB_8DEV_ENDP_DATA_RX = 0x81
USB_8DEV_ENDP_DATA_TX = 0x2
USB_8DEV_ENDP_CMD_RX = 0x83
USB_8DEV_ENDP_CMD_TX = 0x4

# Open Device Options

USB_8DEV_SILENT = 0x01
USB_8DEV_LOOPBACK = 0x02
USB_8DEV_DISABLE_AUTO_RESTRANS = 0x04
USB_8DEV_STATUS_FRAME = 0x08

# Command options
USB_8DEV_BAUD_MANUAL = 0x09
USB_8DEV_CMD_START = 0x11
USB_8DEV_CMD_END = 0x22

USB_8DEV_CMD_SUCCESS = 0
USB_8DEV_CMD_ERROR = 255

USB_8DEV_CMD_TIMEOUT = 1000

# Framing definitions
USB_8DEV_DATA_START = 0x55
USB_8DEV_DATA_END = 0xAA

USB_8DEV_TYPE_CAN_FRAME = 0
USB_8DEV_TYPE_ERROR_FRAME = 3

USB_8DEV_EXTID = 0x01
USB_8DEV_RTR = 0x02
USB_8DEV_ERR_FLAG = 0x04

# Status messages
USB_8DEV_STATUSMSG_OK = 0x00
USB_8DEV_STATUSMSG_OVERRUN = 0x01  # Overrun occured when sending */
USB_8DEV_STATUSMSG_BUSLIGHT = 0x02  # Error counter has reached 96 */
USB_8DEV_STATUSMSG_BUSHEAVY = 0x03  # Error count. has reached 128 */
USB_8DEV_STATUSMSG_BUSOFF = 0x04  # Device is in BUSOFF */
USB_8DEV_STATUSMSG_STUFF = 0x20  # Stuff Error */
USB_8DEV_STATUSMSG_FORM = 0x21  # Form Error */
USB_8DEV_STATUSMSG_ACK = 0x23  # Ack Error */
USB_8DEV_STATUSMSG_BIT0 = 0x24  # Bit1 Error */
USB_8DEV_STATUSMSG_BIT1 = 0x25  # Bit0 Error */
USB_8DEV_STATUSMSG_CRC = 0x27  # CRC Error */

USB_8DEV_RP_MASK = 0x7F  # Mask for Receive Error Bit */

# Available Commands


class Can8DevCommand(Enum):
    USB_8DEV_RESET = 1  # Reset Device
    USB_8DEV_OPEN = 2  # Open Port
    USB_8DEV_CLOSE = 3  # Close Port
    USB_8DEV_SET_SPEED = 4
    USB_8DEV_SET_MASK_FILTER = (
        5
    )  # Unfortunately unknown parameters and supposedly un-implemented on early firmwares
    USB_8DEV_GET_STATUS = 6
    USB_8DEV_GET_STATISTICS = 7
    USB_8DEV_GET_SERIAL = 8
    USB_8DEV_GET_SOFTW_VER = 9
    USB_8DEV_GET_HARDW_VER = 0xA
    USB_8DEV_RESET_TIMESTAMP = 0xB
    USB_8DEV_GET_SOFTW_HARDW_VER = 0xC


class Can8DevTxFrame:
    flags: int
    id: int
    dlc: int
    data: bytes

    def __init__(
        self, can_id: int, dlc: int, data: bytes, is_ext: bool, is_remote: bool
    ):
        self.can_id = can_id
        self.dlc = dlc
        self.data = data
        self.flags = 0
        if is_ext:
            self.flags |= USB_8DEV_EXTID
        if is_remote:
            self.flags |= USB_8DEV_RTR

    def _pad_data(self, data: bytes):
        data_bytes = bytearray(8)
        for i in range(0, 7):
            if i < len(data):
                data_bytes[i] = data[i]
        return bytes(data_bytes)

    def to_bytes(self):
        cmd_buf = bytearray()
        cmd_buf.append(USB_8DEV_DATA_START)
        cmd_buf.append(self.flags)
        id_bytes = self.can_id.to_bytes(4, byteorder="big")
        cmd_buf.extend(id_bytes)
        cmd_buf.append(self.dlc)
        cmd_buf.extend(self._pad_data(self.data))
        cmd_buf.append(USB_8DEV_DATA_END)
        return bytes(cmd_buf)


class Can8DevRxFrame:
    data: bytes
    id: int
    dlc: int
    timestamp: int
    ext_id: bool
    is_error: bool
    is_remote: bool

    def __init__(self, bytes_in: bytes):
        if len(bytes_in) != 21:
            raise ValueError("Did not receive 21 bytes for 8Dev Data Frame")
        if bytes_in[0] != USB_8DEV_DATA_START:
            raise ValueError("Did not receive a valid 8Dev Data Frame")
        if bytes_in[1] == USB_8DEV_TYPE_CAN_FRAME:
            self.data = bytes_in[8:16]
            self.dlc = bytes_in[7]
            self.ext_id = bytes_in[2] & USB_8DEV_EXTID
            self.is_remote = bytes_in[2] & USB_8DEV_RTR
            self.id = int.from_bytes(bytes_in[3:7], byteorder="big")
            self.timestamp = int.from_bytes(bytes_in[16:20], byteorder="big")
            self.is_error = False
        elif bytes_in[1] == USB_8DEV_TYPE_ERROR_FRAME:
            self.is_error = True
            self.data = bytes_in[7:15]
            self.timestamp = int.from_bytes(bytes_in[16:20], byteorder="big")
        else:
            raise ValueError("8Dev Data Frame with Unknown Type")


class Can8DevCommandFrame:
    command: Can8DevCommand
    opt1: int
    opt2: int
    data: bytes

    def __init__(self, command, data=bytes(), opt1=0, opt2=0):
        self.command = command
        self.data = data
        self.opt1 = opt1
        self.opt2 = opt2

    def _pad_data(self, data: bytes):
        data_bytes = bytearray(10)
        for i in range(0, 9):
            if i < len(data):
                data_bytes[i] = data[i]
        return bytes(data_bytes)

    def to_bytes(self):
        cmd_buf = bytearray()
        cmd_buf.append(USB_8DEV_CMD_START)
        cmd_buf.append(0)  # Supposedly could be a channel value, but unknown
        cmd_buf.append(self.command.value)
        cmd_buf.append(self.opt1)
        cmd_buf.append(self.opt2)
        cmd_buf.extend(self._pad_data(self.data))
        cmd_buf.append(USB_8DEV_CMD_END)
        return bytes(cmd_buf)

    def from_bytes(byte_input: bytes):
        if len(byte_input) != 16:
            raise ValueError("Did not receive 16 bytes for 8Dev Command Frame")
        return Can8DevCommandFrame(
            Can8DevCommand(byte_input[2]),
            byte_input[5:15],
            byte_input[3],
            byte_input[4],
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

    def send_command(self, cmd: Can8DevCommand, data: bytes = bytes(), opt1=0, opt2=0):
        frame = Can8DevCommandFrame(cmd, data, opt1, opt2)
        self.cmd_tx_ep.write(frame.to_bytes())
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
        self.send_command(Can8DevCommand.USB_8DEV_RESET)
        open_command = Can8DevCommand.USB_8DEV_OPEN
        opt1 = USB_8DEV_BAUD_MANUAL
        flags = 0
        if loopback:
            flags |= USB_8DEV_LOOPBACK
        if listenonly:
            flags |= USB_8DEV_SILENT
        if oneshot:
            flags |= USB_8DEV_DISABLE_AUTO_RESTRANS
        flags_bytes = flags.to_bytes(4, "big")
        brp_bytes = brp.to_bytes(2, "big")
        data = bytearray(10)
        data[0] = phase_seg1
        data[1] = phase_seg2
        data[2] = sjw
        data[3] = brp_bytes[0]
        data[4] = brp_bytes[1]
        data[5] = flags_bytes[0]
        data[6] = flags_bytes[1]
        data[7] = flags_bytes[2]
        data[8] = flags_bytes[3]
        if self.send_command(open_command, data, opt1).opt1 == 0:
            self._start_recv_thread()
            return True
        else:
            return False

    def close(self):
        self._stop_recv_thread()
        close_command = Can8DevCommand.USB_8DEV_CLOSE
        self.send_command(close_command)

    def recv(self, timeout=None):
        try:
            return self._rx_queue.get(True, timeout=timeout / 1000)
        except queue.Empty:
            return None

    def send(self, tx_frame: Can8DevTxFrame, timeout=None):
        self.data_tx_ep.write(tx_frame.to_bytes(), timeout)

    def get_version(self):
        cmd_response = self.send_command(Can8DevCommand.USB_8DEV_GET_SOFTW_HARDW_VER)
        version = int.from_bytes(cmd_response.data[0:4], byteorder="big")
        return version

    def get_firmware_version(self):
        version = self.get_version()
        return "%d.%d" % ((version >> 24) & 0xFF, (version >> 16) & 0xFF)

    def get_serial_number(self):
        return self.serial_number
