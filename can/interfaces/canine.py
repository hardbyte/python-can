"""
Interface for CANine over USB (win32/macos/linux).

"""

# USB Packet format
# {remaining packets in sequence}{partial frame data}
# or
# 0{command}{CAN frame}

from typing import Any, Optional, Tuple
from can import typechecking

from ..exceptions import error_check

import struct
import time
import logging

from usb import USBError
import usb.core
import usb.util

from can import BusABC, Message

logger = logging.getLogger(__name__)


class CANineBus(BusABC):
    """
    CANine bus class
    CANine is a USB to CAN adapter evolved from canable.
    https://github.com/tinymovr/CANine
    """

    # the supported bitrates and their commands
    _BITRATES = {
        10000: b"S\x00",
        20000: b"S\x01",
        50000: b"S\x02",
        100000: b"S\x03",
        125000: b"S\x04",
        250000: b"S\x05",
        500000: b"S\x06",
        750000: b"S\x07",
        1000000: b"S\x08",
    }

    def __init__(
        self,
        channel: Optional[int],
        bitrate: Optional[int] = None,
        usb_dev=None,
        **kwargs: Any
    ) -> None:
        """
        :param channel:
            Optional channel, corresponds to USB product ID
        :param bitrate:
            Bitrate in bit/s
        :param usb_dev:
            A pyusb device to use
        """

        self._buffer = bytearray()

        if usb_dev:
            dev = usb_dev
        elif channel:
            dev = usb.core.find(idProduct=channel)
        else:
            dev = usb.core.find(idProduct=0xC1B0)
        dev.set_configuration()
        self.dev = dev

        if bitrate is not None:
            self.set_bitrate(bitrate)

        self.open()

        super().__init__(channel, bitrate=None, **kwargs)

    def set_bitrate(self, bitrate: int) -> None:
        """
        :raise ValueError: if both *bitrate* is not among the possible values

        :param bitrate:
            Bitrate in bit/s
        """
        if bitrate in self._BITRATES:
            self.close()
            self._write(self._BITRATES[bitrate])
            self.open()
        else:
            raise ValueError(
                "Invalid bitrate, choose one of "
                + (", ".join(str(k) for k in self._BITRATES.keys()))
                + "."
            )

    def _write(self, payload: bytes) -> None:
        """
        Write to the interface

        :param payload:
            The payload to write as an array of bytes
        """
        # can only send single packet frames for now
        # TODO: update for CAN-FD
        payload = b"\x00" + payload
        self.dev.write(0x1, payload)

    def _read(self, timeout: Optional[float]) -> Optional[str]:
        """
        Read from the interface

        :param timeout:
            Optional read timeout in seconds
        """
        # TODO: handle multiple packets sequence
        # NOTE: pyusb specifies timeout in milliseconds. 
        # in case you dont want to spend a full 
        # hour finding this, here it is: 
        # https://github.com/pyusb/pyusb/blob/777dea9d718e70d7323c821d4497c706b35742da/usb/core.py#L1014 .
        if timeout == 0:
            timeout_int = 1
        else:
            timeout_int = int(timeout*1000)
        with error_check("Could not read from USB device"):
            try:
                packet = self.dev.read(0x81, 64, timeout_int)
                remaining_packets = packet[0]
                assert remaining_packets == 0  # avoid multi-packet sequence for now
                payload = packet[1:]

                return payload
            except USBError as e:
                # do we really need to check for token in string??
                if "time" in str(e):
                    return None
                raise e

    def flush(self) -> None:
        """
        Flush buffer and attempt to read all waiting messages from interface
        """
        del self._buffer[:]
        try:
            p = self.dev.read()
            if p:
                p = self.dev.read()
        except TimeoutError:
            pass

    def open(self) -> None:
        """
        Write the token to open the interface
        """
        self._write(b"O")

    def close(self) -> None:
        """
        Write the token to close the interface
        """
        self._write(b"C")

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:

        canId = None
        remote = False
        extended = False
        frame = []

        payload = self._read(timeout)

        if not payload:
            return None, False
        elif payload[0] == ord(b"T"):
            # extended frame
            canId, dlc = struct.unpack("<LB", payload[1:6])
            extended = True
            frame = payload[6 : dlc + 6]
        elif payload[0] == ord(b"t"):
            # normal frame
            canId, dlc = struct.unpack("<HB", payload[1:4])
            frame = payload[4 : dlc + 4]
        elif payload[0] == ord(b"r"):
            # remote frame
            canId, dlc = struct.unpack("<HB", payload[1:4])
            remote = True
        elif payload[0] == ord(b"R"):
            # remote extended frame
            canId, dlc = struct.unpack("<LB", payload[1:6])
            extended = True
            remote = True
        else:
            raise ConnectionError("Unknown frame type identifier")

        msg = Message(
            arbitration_id=canId,
            is_extended_id=extended,
            timestamp=time.time(),  # Better than nothing...
            is_remote_frame=remote,
            dlc=dlc,
            data=frame,
        )
        return msg, False

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:

        if msg.is_remote_frame:
            if msg.is_extended_id:
                header = ord("R")
                encoding = "<BLB"
            else:
                header = ord("r")
                encoding = "<BHB"
            payload = struct.pack(encoding, header, msg.arbitration_id, msg.dlc)
        else:
            if msg.is_extended_id:
                header = ord("T")
                encoding = "<BLB"
            else:
                header = ord("t")
                encoding = "<BHB"
            payload = struct.pack(
                encoding, header, msg.arbitration_id, msg.dlc
            ) + bytes(msg.data)
        self._write(payload)

    def shutdown(self) -> None:
        """
        Shutdown by closing the interface and freeing resources
        """
        self.close()
        usb.util.dispose_resources(self.dev)

    def fileno(self) -> int:
        raise NotImplementedError(
            "fileno is not implemented using current CAN bus on this platform"
        )

    def get_version(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[int], Optional[int]]:
        """Get HW and SW version of the adapter.

        :param timeout:
            seconds to wait for version or None to wait indefinitely

        :returns: tuple (hw_version, sw_version)
            WHERE
            int hw_version is the hardware version or None on timeout
            int sw_version is the software version or None on timeout
        """
        cmd = b"V"
        self._write(cmd)

        payload = self._read(timeout)
        assert payload[0] == ord(b"V")
        return struct.unpack("<HH", payload[1:5])

    @staticmethod
    def _detect_available_configs():
        """
        Identify CANine devices
        """
        devs = usb.core.find(idProduct=0xC1B0, find_all=True)
        return [
            {
                "interface": "canine",
                "channel": usb.util.get_string(dev, dev.iSerialNumber),
            }
            for dev in devs
        ]
