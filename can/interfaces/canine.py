"""
Interface for CANine over USB (win32/macos/linux).

"""

# USB Packet format
# {remaining packets in sequence}{partial frame data}
# or
# 0{command}{CAN frame}

from typing import Any, Optional, Tuple
from can import typechecking

import struct
import time
import logging

import usb.core
import usb.util

from can import BusABC, Message

logger = logging.getLogger(__name__)


class CANineBus(BusABC):
    """
    CANine bus class
    """

    # the supported bitrates and their commands
    _BITRATES = {
        10000: b'S\x00',
        20000: b'S\x01',
        50000: b'S\x02',
        100000: b'S\x03',
        125000: b'S\x04',
        250000: b'S\x05',
        500000: b'S\x06',
        750000: b'S\x07',
        1000000: b'S\x08'
    }

    def __init__(
        self,
        channel: typechecking.ChannelStr,
        bitrate: Optional[int] = None,
        btr: Optional[str] = None,
        usb_dev=None,
        **kwargs: Any
    ) -> None:
        """
        :raise ValueError: if both *bitrate* and *btr* are set

        :param bitrate:
            Bitrate in bit/s
        :param btr:
            BTR register value to set custom can speed
        :param poll_interval:
            Poll interval in seconds when reading messages
        :param sleep_after_open:
            Time to wait in seconds after opening connection
        """

        self._buffer = bytearray()

        if usb_dev:
            dev = usb_dev
        else:
            dev = usb.core.find(idProduct=0xc1b0)
        assert(dev is not None)
        dev.set_configuration()
        self.dev = dev

        if bitrate is not None and btr is not None:
            raise ValueError("Bitrate and btr mutually exclusive.")
        if bitrate is not None:
            self.set_bitrate(bitrate)
        if btr is not None:
            self.set_bitrate_reg(btr)

        self.open()

        super().__init__(channel, bitrate=None, **kwargs)

    def set_bitrate(self, bitrate: int) -> None:
        """
        :raise ValueError: if both *bitrate* is not among the possible values

        :param bitrate:
            Bitrate in bit/s
        """
        if bitrate in self._BITRATES:
            self.set_bitrate_reg(self._BITRATES[bitrate])
        else:
            raise ValueError(
                "Invalid bitrate, choose one of "
                + (", ".join(str(k) for k in self._BITRATES.keys()))
                + "."
            )

    def set_bitrate_reg(self, btr: bytes) -> None:
        """
        :param btr:
            BTR register value to set custom can speed
        """
        self.close()
        self._write(btr)
        self.open()

    def _write(self, payload: bytes, timeout: int=0) -> None:
        # can only send single packet frames for now
        # TODO: update for CAN-FD
        payload = b'\000' + payload
        self.dev.write(0x1,  payload)

    def _read(self, timeout: Optional[float]) -> Optional[str]:
        # TODO: Reception should be asynchronous and use timeout
        packet = self.dev.read(0x81, 64)
        remaining_packets = packet[0]
        payload = packet[1:]
        assert(remaining_packets == 0)

        # for i in reversed(range(remaining_packets)):
        #     packet = self.dev.read(0x81, 64)
        #     if i != packet[0]:
        #         return None
        #     payload = payload + packet[1:]

        return payload

    def flush(self) -> None:
        del self._buffer[:]

    def open(self) -> None:
        self._write(b'O')

    def close(self) -> None:
        self._write(b'C')

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:

        canId = None
        remote = False
        extended = False
        frame = []

        payload = self._read(timeout)

        if payload[0] == b'T':
            # extended frame
            canId, dlc = struct.unpack('<LB', payload[1:6])
            extended = True
            frame = payload[6:dlc+6]
        elif payload[0] == b't':
            # normal frame
            canId, dlc = struct.unpack('<HB', payload[1:4])
            frame = payload[4:dlc+4]
        elif payload[0] == b'r':
            # remote frame
            canId, dlc = struct.unpack('<HB', payload[1:4])
            remote = True
        elif payload[0] == b'R':
            # remote extended frame
            canId, dlc = struct.unpack('<LB', payload[1:6])
            extended = True
            remote = True

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
                header = ord('R')
                encoding = '<BLB'
            else:
                header = ord('r')
                encoding = '<BHB'
            payload = struct.pack(encoding, header, msg.arbitration_id, msg.dlc)
        else:
            if msg.is_extended_id:
                header = ord('T')
                encoding = '<BLB'
            else:
                header = ord('t')
                encoding = '<BHB'
            payload = struct.pack(encoding, header, msg.arbitration_id, msg.dlc) + \
                bytes(msg.data)
        print(msg.arbitration_id)
        print(payload)
        self._write(payload, timeout)

    def shutdown(self) -> None:
        self.close()
        usb.util.dispose_resources(self.dev)

    def fileno(self) -> int:
        raise NotImplementedError(
            "fileno is not implemented using current CAN bus on this platform"
        )

    def get_version(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[int], Optional[int]]:
        """Get HW and SW version of the adapter fw.

        :param timeout:
            seconds to wait for version or None to wait indefinitely

        :returns: tuple (hw_version, sw_version)
            WHERE
            int hw_version is the hardware version or None on timeout
            int sw_version is the software version or None on timeout
        """
        cmd = b'V'
        self._write(cmd)

        payload = self._read(timeout)
        assert(payload[0] == ord(b'V'))
        return struct.unpack('>HH', payload[1:5])
