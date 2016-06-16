class PGN(object):

    def __init__(self, reserved_flag=False, data_page_flag=False, pdu_format=0, pdu_specific=0):
        self.reserved_flag = reserved_flag
        self.data_page_flag = data_page_flag
        self.pdu_format = pdu_format
        self.pdu_specific = pdu_specific

    @property
    def is_pdu1(self):
        return ((self.pdu_format < 240) or self.reserved_flag or self.data_page_flag)

    @property
    def is_pdu2(self):
        return not self.is_pdu1

    @property
    def is_destination_specific(self):
        return self.is_pdu1

    @property
    def value(self):
        _pgn_flags_byte = ((self.reserved_flag << 1) + self.data_page_flag)
        return int("%.2x%.2x%.2x" % (_pgn_flags_byte, self.pdu_format, self.pdu_specific), 16)

    @value.setter
    def value(self, value):
        self.reserved_flag = (value & 0x020000) >> 17
        self.data_page_flag = (value & 0x010000) >> 16
        self.pdu_format = (value & 0x00FF00) >> 8
        self.pdu_specific = value & 0x0000FF

    @staticmethod
    def from_value(value):
        pgn = PGN()
        pgn.value = value
        return pgn

    def __str__(self):
        retval = ""
        _temp = self.value
        if self.is_destination_specific:
            _temp -= self.pdu_specific
        retval += ("0x%.4x " % (_temp & 0xFFFF))
        if self.reserved_flag:
            retval += "R "
        else:
            retval += "  "
        if self.data_page_flag:
            retval += "P "
        else:
            retval += "  "
        return retval
