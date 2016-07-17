from can.protocols.j1939.pgn import PGN


class ArbitrationID(object):

    def __init__(self, priority=7, pgn=None, source_address=0):
        """
        :param int priority:
            Between 0 and 7, where 0 is highest priority.

        :param :class:`can.protocols.j1939.PGN`/int pgn:
            The parameter group number.

        :param int source_address:
            Between 0 and 255.
        """
        self.priority = priority
        self.pgn = pgn
        self.source_address = source_address

    @property
    def can_id(self):
        return (self.source_address + (self.pgn.value << 8) + (self.priority << 26))

    @can_id.setter
    def can_id(self, value):
        """
        Int between 0 and (2**29) - 1
        """
        self.priority = (value & 0x1C000000) >> 26
        self.pgn.value = (value & 0x03FFFF00) >> 8
        self.source_address = value & 0x000000FF

    @property
    def destination_address(self):
        if self.pgn.is_destination_specific:
            return self.pgn.pdu_specific
        else:
            return None

    @property
    def pgn(self):
        return self._pgn

    @pgn.setter
    def pgn(self, other):
        if other is None:
            self._pgn = PGN()
        elif not isinstance(other, PGN):
            self._pgn = PGN.from_value(other)
        else:
            self._pgn = other

    def __str__(self):
        if self.destination_address is not None:
            retval = "PRI=%d PGN=%6s DST=0x%.2x SRC=0x%.2x" % (
                self.priority, self.pgn, self.destination_address, self.source_address)
        else:
            retval = "PRI=%d PGN=%6s          SRC=0x%.2x" % (self.priority, self.pgn, self.source_address)
        return retval
