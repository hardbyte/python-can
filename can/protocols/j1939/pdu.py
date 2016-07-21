import logging
from can import Message

from .arbitrationid import ArbitrationID
from .constants import pgn_strings, PGN_AC_ADDRESS_CLAIMED
from .nodename import NodeName

logger = logging.getLogger(__name__)


class PDU(object):

    """
    A PDU is a higher level abstraction of a CAN message.
    J1939 ensures that long messages are taken care of.
    """

    def __init__(self, timestamp=0.0, arbitration_id=None, data=None, info_strings=None):
        """
        :param float timestamp:
            Bus time in seconds.
        :param :class:`can.protocols.j1939.ArbitrationID` arbitration_id:

        :param bytes/bytearray/list data:
            With length up to 1785.
        """
        if data is None:
            data = []
        if info_strings is None:
            info_strings = []
        self.timestamp = timestamp
        self.arbitration_id = arbitration_id
        self.data = self._check_data(data)
        self.info_strings = info_strings

    def __eq__(self, other):
        """Returns True if the pgn, data, source and destination are the same"""
        if other is None:
            return False
        if self.pgn != other.pgn:
            return False
        if self.data != other.data:
            return False
        if self.source != other.source:
            return False
        if self.destination != other.destination:
            return False
        return True

    @property
    def pgn(self):
        if self.arbitration_id.pgn.is_destination_specific:
            return self.arbitration_id.pgn.value & 0xFF00
        else:
            return self.arbitration_id.pgn.value

    @property
    def destination(self):
        """Destination address of the message"""
        return self.arbitration_id.destination_address

    @property
    def source(self):
        """Source address of the message"""
        return self.arbitration_id.source_address

    @property
    def is_address_claim(self):
        return self.pgn == PGN_AC_ADDRESS_CLAIMED

    @property
    def arbitration_id(self):
        return self._arbitration_id

    @arbitration_id.setter
    def arbitration_id(self, other):
        if other is None:
            self._arbitration_id = ArbitrationID()
        elif not isinstance(other, ArbitrationID):
            self._arbitration_id = ArbitrationID(other)
        else:
            self._arbitration_id = other

    def _check_data(self, value):
        assert len(value) <= 1785, 'Too much data to fit in a j1939 CAN message. Got {0} bytes'.format(len(value))
        if len(value) > 0:
            assert min(value) >= 0, 'Data values must be between 0 and 255'
            assert max(value) <= 255, 'Data values must be between 0 and 255'
        return value

    def data_segments(self, segment_length=8):
        retval = []
        for i in range(0, len(self.data), segment_length):
            retval.append(self.data[i:i + min(segment_length, (len(self.data) - i))])
        return retval

    def check_equality(self, other, fields, debug=False):
        """
        :param :class:`~can.protocols.j1939.PDU` other:
        :param list[str] fields:
        """

        logger.debug("check_equality starting")

        retval = True
        for field in fields:
            try:
                own_value = getattr(self, field)
            except AttributeError:
                logger.warning("'%s' not found in 'self'" % field)
                return False

            try:
                other_value = getattr(other, field)
            except AttributeError:
                logger.debug("'%s' not found in 'other'" % field)
                return False

            if debug:
                self.info_strings.append("%s: %s, %s" % (field, own_value, other_value))
            if own_value != other_value:
                return False

        logger.debug("Messages match")
        return retval

    def __str__(self):
        """

        :return: A string representation of this message.

        """
        # TODO group this into 8 bytes per line and line them up...
        data_string = " ".join("{:02d}".format(byte) for byte in self.data)
        return "{s.timestamp:15.6f}    {s.arbitration_id}    {data}".format(s=self, data=data_string)
