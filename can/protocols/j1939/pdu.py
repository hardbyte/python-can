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
        if arbitration_id is None:
            arbitration_id = ArbitrationID()
        assert isinstance(arbitration_id, ArbitrationID)
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

    def _check_data(self, value):
        assert len(value) <= 1785, 'Too much data to fit in a j1939 CAN message. Got {0} bytes'.format(len(value))
        if len(value) > 0:
            assert min(value) >= 0, 'Data values must be between 0 and 255'
            assert max(value) <= 255, 'Data values must be between 0 and 255'
        return value

    def data_segments(self, segment_length=8):
        retval = []
        for i in range(0, len(self.data), segment_length):
            retval.append(self.data[i:i+min(segment_length, (len(self.data) - i))])
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
        field_strings = ["%15.6f" % self.timestamp,
                         "%s" % self.arbitration_id]
        data_segments = []
        return "TODO FIX DISPLAY STR of j1939.pdu " + str(list(map(hex, self.data)))

        for (segment, info_string) in zip(self.data_segments(segment_length=8), 
                                          self.breakdown)[:min(len(self.data_segments(segment_length=8)),
                                                               len(self.breakdown))]:
            data_segments.append("%s%s" % ((" ".join("%.2x" % _byte for _byte in segment)).ljust(24), info_string))
        
        if len(self.data_segments(segment_length=8)) >= len(self.breakdown):
            for segment in self.data_segments(segment_length=8)[len(self.breakdown):]:
                data_segments.append("%s" % (" ".join("%.2x" % _byte for _byte in segment)).ljust(24))
        else:
            for info_string in self.breakdown[len(self.data_segments(segment_length=8)):]:
                data_segments.append((" " * 24 + info_string))
        retval = "    ".join(field_strings) + "    "
        retval += ("\n" + " "*len(retval)).join(data_segments)
        if len(self.info_strings) > 0:
            retval += ("\n" + " " * 19)
            retval += (("\n" + " " * 19).join(self.info_strings))
        return retval


