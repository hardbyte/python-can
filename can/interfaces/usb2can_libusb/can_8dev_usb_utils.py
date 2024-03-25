from enum import Enum

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


def can_8dev_open_frame(
    phase_seg1: int,
    phase_seg2: int,
    sjw: int,
    brp: int,
    loopback: bool = False,
    listenonly: bool = False,
    oneshot: bool = False,
) -> Can8DevCommandFrame:
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
    return Can8DevCommandFrame(open_command, data, opt1)
