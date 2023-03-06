import struct
import time
import logging
from typing import Any, List

from can import BusABC, Message
from can.typechecking import AutoDetectedConfig

logger = logging.getLogger("usb_can_analyzer")

try:
    import serial
except ImportError:
    logger.warning(
        "You won't be able to use the serial can backend without "
        "the serial module installed!"
    )
    serial = None

try:
    from serial.tools.list_ports import comports as list_comports
except ImportError:
    # If unavailable on some platform, just return nothing
    def list_comports() -> List[Any]:
        return []


def wait(t):
    w = time.perf_counter()
    while time.perf_counter() - w < t:
        continue


class UsbCanAnalyzer(BusABC):

    BITRATE = {
        1000000: 0x01,
        800000: 0x02,
        500000: 0x03,
        400000: 0x04,
        250000: 0x05,
        200000: 0x06,
        125000: 0x07,
        100000: 0x08,
        50000: 0x09,
        20000: 0x0A,
        10000: 0x0B,
        5000: 0x0C,
    }

    FRAMETYPE = {"STD": 0x01, "EXT": 0x02}

    OPERATIONMODE = {
        "normal": 0x00,
        "loopback": 0x01,
        "silent": 0x02,
        "loopback_and_silent": 0x03,
    }

    def __init__(
        self,
        channel,
        baudrate=2000000,
        timeout=0.1,
        frame_type="STD",
        operation_mode="normal",
        bitrate=500000,
        *args,
        **kwargs
    ):

        self.channel_info = "USB-CAN Analyzer: " + channel
        self.bit_rate = bitrate
        self.frame_type = frame_type
        self.op_mode = operation_mode
        self.filter_id = bytearray([0x00, 0x00, 0x00, 0x00])
        self.mask_id = bytearray([0x00, 0x00, 0x00, 0x00])
        self.ser = serial.serial_for_url(
            channel,
            baudrate=baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=timeout,
            rtscts=False,
        )

        super().__init__(channel=channel, *args, **kwargs)
        self.init()

    def init(self):
        byte_msg = bytearray()
        byte_msg.append(0xAA)  # Frame Start Byte 1
        byte_msg.append(0x55)  # Frame Start Byte 2
        byte_msg.append(0x12)  # Initialization Message ID
        byte_msg.append(UsbCanAnalyzer.BITRATE[self.bit_rate])  # CAN Baud Rate
        byte_msg.append(UsbCanAnalyzer.FRAMETYPE[self.frame_type])
        byte_msg.extend(self.filter_id)
        byte_msg.extend(self.mask_id)
        byte_msg.append(UsbCanAnalyzer.OPERATIONMODE[self.op_mode])
        byte_msg.append(0x01)  # Follows 'Send once' in windows app.
        byte_msg.extend([0x00] * 4)  # Manual bitrate config, details unknown.
        crc = sum(byte_msg[2:]) & 0xFF
        byte_msg.append(crc)

        self.ser.write(byte_msg)
        self.ser.flush()

    def shutdown(self):
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()
        self.ser.close()

    def flush_tx_buffer(self):
        self.ser.reset_output_buffer()

    def send(self, msg, timeout=None):
        try:
            byte_msg = bytearray()
            byte_msg.append(0xAA)
            byte_msg.append(
                0xC0 | (msg.is_extended_id << 5) | (msg.is_remote_frame << 4) | msg.dlc
            )
            byte_msg += struct.pack(
                "<I" if msg.is_extended_id else "<H", msg.arbitration_id
            )
            byte_msg += msg.data
            byte_msg.append(0x55)
            self.ser.write(byte_msg)
            self.ser.flush()
            wait(0.0002)
        except serial.SerialException:
            pass

    def _recv_internal(self, timeout):
        try:
            rx_byte = self.ser.read()
            if rx_byte and ord(rx_byte) == 0xAA:
                tyep = ord(self.ser.read(1))
                is_extended_id = tyep & 0x20
                is_remote_frame = tyep & 0x10
                dlc = (tyep << 4 & 0xFF) >> 4
                arb_id = (
                    struct.unpack(
                        "<I" if is_extended_id else "<H",
                        bytearray(self.ser.read(4 if is_extended_id else 2)),
                    )
                )[0]
                data = self.ser.read(dlc)
                rxd_byte = ord(self.ser.read(1))
                if rxd_byte == 0x55:
                    msg = Message(
                        arbitration_id=arb_id,
                        timestamp=time.perf_counter(),
                        dlc=dlc,
                        data=data,
                        is_extended_id=is_extended_id,
                        is_remote_frame=is_remote_frame,
                    )
                    return msg, False
        except serial.SerialException:
            pass
        return None, False

    def fileno(self):
        try:
            return self.ser.fileno()
        except io.UnsupportedOperation as excption:
            logger.warning(
                "fileno is not implemented using current CAN bus: %s", str(excption)
            )
            return -1

    @staticmethod
    def _detect_available_configs() -> List[AutoDetectedConfig]:
        configs = []
        for port in list_comports():
            if port.vid == 0x1A86:
                configs.append(
                    {"interface": "usb_can_analyzer", "channel": port.device}
                )
        return configs
