import logging

log = logging.getLogger('py1939.node')
log.info('Loading J1939 node')

from can import Listener, CanError
from can.protocols.j1939.constants import *
from can.protocols.j1939.pdu import PDU
from can.protocols.j1939.nodename import NodeName


class J1939Error(CanError):
    pass


class DuplicateTransmissionError(J1939Error):
    pass


class InaccessibleDestinationError(J1939Error):
    pass


class Node(Listener):

    """
    A j1939.Node will claim an address when it sees a j1939 address claim
    and after address claim send any messages with its source address.

    :param :class:`can.Bus` bus:
    :param :class:`can.protocols.j1939.NodeName` name:
    :param list(int) address_list:
        A list of potential addresses that this Node will use when claiming
        an address.
    :param pdu_type:
        The pdu class to use when returning messages.
    """

    def __init__(self, bus, name, address_list, pdu_type=PDU):
        self.bus = bus
        self.node_name = name
        self.address_list = address_list
        self._pdu_type = pdu_type
        self._current_address_index = 0
        self.known_node_addresses = {self.node_name.value: ADDRESS_UNCLAIMED}

    @property
    def address(self):
        return self.known_node_addresses[self.node_name.value]

    def start_address_claim(self):
        self.claim_address(self.address_list[self._current_address_index])

    def claim_address(self, address):
        claimed_address_pdu = self._pdu_type()
        claimed_address_pdu.arbitration_id.pgn.value = PGN_AC_ADDRESS_CLAIMED
        claimed_address_pdu.arbitration_id.priority = 4
        claimed_address_pdu.arbitration_id.pgn.pdu_specific = 0xff
        claimed_address_pdu.arbitration_id.source_address = address
        claimed_address_pdu.data = self.node_name.bytes
        self.known_node_addresses[self.node_name.value] = address
        self.bus.send(claimed_address_pdu)

    def on_message_received(self, pdu):
        if pdu.pgn == PGN_AC_ADDRESS_CLAIMED:
            log.info('got address claimed pdu')
            if pdu.source != DESTINATION_ADDRESS_NULL:
                if pdu.data != self.node_name.bytes:
                    if pdu.source != self.address:
                        node_name = NodeName()
                        node_name.bytes = pdu.data
                        self.known_node_addresses[node_name.value] = pdu.source
                    else:
                        competing_node_name = NodeName()
                        competing_node_name.bytes = pdu.data
                        if self.node_name.value > competing_node_name.value:
                            self._current_address_index += 1
                            if self._current_address_index >= len(self.address_list):
                                self.claim_address(DESTINATION_ADDRESS_NULL)
                            else:
                                self.claim_address(self.address_list[self._current_address_index])
                        else:
                            self.claim_address(self.address)
            else:
                node_name = NodeName()
                node_name.bytes = pdu.data
                self.known_node_addresses[node_name.value] = pdu.source
        elif pdu.pgn == PGN_AC_COMMANDED_ADDRESS:
            node_name = NodeName()
            node_name.bytes = pdu.data[:8]
            new_address = pdu.data[8]
            if node_name.value == self.node_name.value:
                # if we are the commanded node change our address
                self.claim_address(new_address)
        elif pdu.pgn == PGN_REQUEST_FOR_PGN:
            pgn = int("%.2X%.2X%.2X" % (pdu.data[2], pdu.data[1], pdu.data[0]), 16)
            if pdu.destination in (self.address, DESTINATION_ADDRESS_GLOBAL):
                if pgn == PGN_AC_ADDRESS_CLAIMED:
                    self.claim_address(self.known_node_addresses[self.node_name.value])

    def send_parameter_group(self, pgn, data, destination_device_name=None):
        """
        :param int pgn:
            should be between [0, (2 ** 18) - 1]
        :param list data:
            should have less than 1785 elements
            Each element should be a int between 0 and 255
        :param destination_device_name:
            Should be None, or an int between 0 and (2 ** 64) - 1
        """
        # if we are *allowed* to send data
        if self.known_node_addresses[self.node_name.value] not in (ADDRESS_UNCLAIMED, DESTINATION_ADDRESS_NULL):
            pdu = self._pdu_type()
            pdu.arbitration_id.pgn.value = pgn
            pdu.arbitration_id.source_address = self.known_node_addresses[self.node_name.value]
            if pdu.arbitration_id.pgn.is_destination_specific:
                if destination_device_name is not None:
                    pdu.arbitration_id.pgn.pdu_specific = self.known_node_addresses[destination_device_name]
                    if pdu.arbitration_id.pgn.pdu_specific == DESTINATION_ADDRESS_NULL:
                        raise InaccessibleDestinationError
                else:
                    pdu.arbitration_id.pgn.pdu_specific = DESTINATION_ADDRESS_GLOBAL
            pdu.data = data
            self.bus.write(pdu)
