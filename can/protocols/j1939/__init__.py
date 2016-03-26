"""
SAE J1939 vehicle bus standard.

http://en.wikipedia.org/wiki/J1939
"""

import threading
import logging

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty
import time
import copy

# By this stage the can.rc should have been set up
from can import Message
from can.interfaces.interface import Bus as RawCanBus

from can.notifier import Notifier

# Import our new message type
from can.protocols.j1939.pdu import PDU
from can.protocols.j1939.pgn import PGN
from can.bus import BusABC
from can.protocols.j1939 import constants
from can.protocols.j1939.node import Node
from can.protocols.j1939.nodename import NodeName
from can.protocols.j1939.arbitrationid import ArbitrationID


logger = logging.getLogger(__name__)


class Bus(BusABC):

    """
    A CAN Bus that implements the J1939 Protocol.

    :param list j1939_filters:
        a list of dictionaries that specify filters that messages must
        match to be received by this Bus. Messages can match any of the
        filters.

        Options are:

        * :pgn: An integer PGN to show
    """

    channel_info = "j1939 bus"

    def __init__(self, pdu_type=PDU, *args, **kwargs):
        logger.debug("Creating a new j1939 bus")

        self.rx_can_message_queue = Queue()

        super(Bus, self).__init__()
        self._pdu_type = pdu_type
        self._long_message_throttler = threading.Thread(target=self._throttler_function)
        #self._long_message_throttler.daemon = True

        self._incomplete_received_pdus = {}
        self._incomplete_received_pdu_lengths = {}
        self._incomplete_transmitted_pdus = {}
        self._long_message_segment_queue = Queue(0)

        # Convert J1939 filters into Raw Can filters

        if 'j1939_filters' in kwargs and kwargs['j1939_filters'] is not None:
            filters = kwargs.pop('j1939_filters')
            logger.debug("Got filters: {}".format(filters))
            can_filters = []
            for filt in filters:
                can_id, can_mask = 0, 0
                if 'pgn' in filt:
                    can_id = filt['pgn'] << 8
                    # The pgn needs to be left shifted by 8 to ignore the CAN_ID's source address
                    # Look at most significant 4 bits to determine destination specific
                    if can_id & 0xF00000 == 0xF00000:
                        logging.info("PDU2 (broadcast message)")
                        can_mask = 0xFFFF00
                    else:
                        logging.info("PDU1 (p2p)")
                        can_mask = 0xFF0000
                if 'source' in filt:
                    # filter by source
                    can_mask |= 0xFF
                    can_id |= filt['source']
                    logger.info("added source", filt)

                logger.info("Adding CAN ID filter: {:0x}:{:0x}".format(can_id, can_mask))
                can_filters.append({"can_id": can_id, "can_mask": can_mask})
            kwargs['can_filters'] = can_filters

        logger.debug("Creating a new can bus")
        self.can_bus = RawCanBus(*args, **kwargs)
        self.can_notifier = Notifier(self.can_bus, [self.rx_can_message_queue.put])
        self.j1939_notifier = Notifier(self, [])

        self._long_message_throttler.start()

    def recv(self, timeout=None):
        logger.debug("Waiting for new message")
        logger.debug("Timeout is {}".format(timeout))
        try:
            m = self.rx_can_message_queue.get(timeout=timeout)
        except Empty:
            return

        rx_pdu = None

        if isinstance(m, Message):
            logger.debug('Got a Message: %s' % m)
            if m.id_type:
                # Extended ID
                # Only J1939 messages (i.e. 29-bit IDs) should go further than this point.
                # Non-J1939 systems can co-exist with J1939 systems, but J1939 doesn't care
                # about the content of their messages.
                logger.info('Message is j1939 msg')
                rx_pdu = self._process_incoming_message(m)
            else:
                logger.info("Received non J1939 message (ignoring)")

            # TODO: Decide what to do with CAN errors
            if m.is_error_frame:
                logger.warning("Appears we got an error frame!")

                #rx_error = CANError(timestamp=m.timestamp)
                # if rx_error is not None:
                #     logger.info('Sending error "%s" to registered listeners.' % rx_error)
                #     for listener in self.listeners:
                #         if hasattr(listener, 'on_error_received'):
                #             listener.on_error_received(rx_error)

        # Return to BusABC where it will get fed to any listeners
        return rx_pdu

    def send(self, msg):
        messages = []
        if len(msg.data) > 8:
            # Making a copy of the PDU so that the original
            # is not altered by the data padding.
            pdu = copy.deepcopy(msg)
            pdu.data = bytearray(pdu.data)

            pdu_length_lsb, pdu_length_msb = divmod(len(pdu.data), 256)

            while len(pdu.data) % 7 != 0:
                pdu.data += b'\xFF'

            for i, segment in enumerate(pdu.data_segments(segment_length=7)):
                arbitration_id = copy.deepcopy(pdu.arbitration_id)
                arbitration_id.pgn.value = constants.PGN_TP_DATA_TRANSFER
                if pdu.arbitration_id.pgn.is_destination_specific and \
                   pdu.arbitration_id.destination_address != constants.DESTINATION_ADDRESS_GLOBAL:
                    arbitration_id.pgn.pdu_specific = pdu.arbitration_id.pgn.pdu_specific
                else:
                    arbitration_id.pgn.pdu_specific = constants.DESTINATION_ADDRESS_GLOBAL

                message = Message(arbitration_id=arbitration_id.can_id,
                                  extended_id=True,
                                  dlc=(len(segment) + 1),
                                  data=(bytearray([i + 1]) + segment))
                messages.append(message)

            if pdu.arbitration_id.pgn.is_destination_specific and \
               pdu.arbitration_id.destination_address != constants.DESTINATION_ADDRESS_GLOBAL:
                destination_address = pdu.arbitration_id.pgn.pdu_specific
                if pdu.arbitration_id.source_address in self._incomplete_transmitted_pdus:
                    if destination_address in self._incomplete_transmitted_pdus[pdu.arbitration_id.source_address]:
                        logger.warning("Duplicate transmission of PDU:\n{}".format(pdu))
                else:
                    self._incomplete_transmitted_pdus[pdu.arbitration_id.source_address] = {}
                self._incomplete_transmitted_pdus[pdu.arbitration_id.source_address][destination_address] = messages
            else:
                destination_address = constants.DESTINATION_ADDRESS_GLOBAL

            rts_arbitration_id = ArbitrationID(source_address=pdu.source)
            rts_arbitration_id.pgn.value = constants.PGN_TP_CONNECTION_MANAGEMENT
            rts_arbitration_id.pgn.pdu_specific = pdu.arbitration_id.pgn.pdu_specific

            temp_pgn = copy.deepcopy(pdu.arbitration_id.pgn)
            if temp_pgn.is_destination_specific:
                temp_pgn.value -= temp_pgn.pdu_specific

            pgn_msb = ((temp_pgn.value & 0xFF0000) >> 16)
            pgn_middle = ((temp_pgn.value & 0x00FF00) >> 8)
            pgn_lsb = (temp_pgn.value & 0x0000FF)

            if pdu.arbitration_id.pgn.is_destination_specific and \
               pdu.arbitration_id.destination_address != constants.DESTINATION_ADDRESS_GLOBAL:
                # send request to send
                rts_msg = Message(extended_id=True,
                                  arbitration_id=rts_arbitration_id.can_id,
                                  data=[constants.CM_MSG_TYPE_RTS,
                                        pdu_length_msb,
                                        pdu_length_lsb,
                                        len(messages),
                                        0xFF,
                                        pgn_lsb,
                                        pgn_middle,
                                        pgn_msb],
                                  dlc=8)
                self.can_bus.send(rts_msg)
            else:
                rts_arbitration_id.pgn.pdu_specific = constants.DESTINATION_ADDRESS_GLOBAL
                bam_msg = Message(extended_id=True,
                                  arbitration_id=rts_arbitration_id.can_id,
                                  data=[constants.CM_MSG_TYPE_BAM,
                                        pdu_length_msb,
                                        pdu_length_lsb, len(messages),
                                        0xFF,
                                        pgn_lsb,
                                        pgn_middle,
                                        pgn_msb],
                                  dlc=8)
                # send BAM
                self.can_bus.send(bam_msg)

                for message in messages:
                    # send data messages - no flow control, so no need to wait
                    # for receiving devices to acknowledge
                    self._long_message_segment_queue.put_nowait(message)
        else:
            can_message = Message(arbitration_id=msg.arbitration_id.can_id,
                                  extended_id=True,
                                  dlc=len(msg.data),
                                  data=msg.data)

            self.can_bus.send(can_message)

    def shutdown(self):
        self.can_notifier.running.clear()
        self.can_bus.shutdown()
        self.j1939_notifier.running.clear()
        super(Bus, self).shutdown()

    def _process_incoming_message(self, msg):
        logger.debug("Processing incoming message")
        logging.debug(msg)
        arbitration_id = ArbitrationID()
        arbitration_id.can_id = msg.arbitration_id
        if arbitration_id.pgn.is_destination_specific:
            arbitration_id.pgn.value -= arbitration_id.pgn.pdu_specific
        pdu = self._pdu_type(timestamp=msg.timestamp, data=msg.data, info_strings=[])
        pdu.arbitration_id.can_id = msg.arbitration_id
        pdu.info_strings = []

        if arbitration_id.pgn.value == constants.PGN_TP_CONNECTION_MANAGEMENT:
            retval = self._connection_management_handler(pdu)
        elif arbitration_id.pgn.value == constants.PGN_TP_DATA_TRANSFER:
            retval = self._data_transfer_handler(pdu)
        else:
            retval = pdu

        return retval

    def _connection_management_handler(self, msg):
        if len(msg.data) == 0:
            msg.info_strings.append("Invalid connection management message - no data bytes")
            return msg
        cmd = msg.data[0]
        retval = None
        if cmd == constants.CM_MSG_TYPE_RTS:
            retval = self._process_rts(msg)
        elif cmd == constants.CM_MSG_TYPE_CTS:
            retval = self._process_cts(msg)
        elif cmd == constants.CM_MSG_TYPE_EOM_ACK:
            retval = self._process_eom_ack(msg)
        elif cmd == constants.CM_MSG_TYPE_BAM:
            retval = self._process_bam(msg)
        elif cmd == constants.CM_MSG_TYPE_ABORT:
            retval = self._process_abort(msg)

        return retval

    def _data_transfer_handler(self, msg):
        msg_source = msg.arbitration_id.source_address
        pdu_specific = msg.arbitration_id.pgn.pdu_specific

        if msg_source in self._incomplete_received_pdus:

            if pdu_specific in self._incomplete_received_pdus[msg_source]:
                self._incomplete_received_pdus[msg_source][pdu_specific].data.extend(msg.data[1:])
                total = self._incomplete_received_pdu_lengths[msg_source][pdu_specific]["total"]
                if len(self._incomplete_received_pdus[msg_source][pdu_specific].data) >= total:
                    if pdu_specific == constants.DESTINATION_ADDRESS_GLOBAL:
                        # Looks strange but makes sense - in the absence of explicit flow control,
                        # the last CAN packet in a long message *is* the end of message acknowledgement
                        return self._process_eom_ack(msg)

                    # Find a Node object so we can search its list of known node addresses for this node
                    # so we can find if we are responsible for sending the EOM ACK message
                    send_ack = any(True for l in self.j1939_notifier.listeners
                                   if isinstance(l, Node) and (l.address == pdu_specific or
                                                               pdu_specific in l.address_list))
                    if send_ack:
                        arbitration_id = ArbitrationID()
                        arbitration_id.pgn.value = constants.PGN_TP_CONNECTION_MANAGEMENT
                        arbitration_id.pgn.pdu_specific = msg_source
                        arbitration_id.source_address = pdu_specific
                        total_length = self._incomplete_received_pdu_lengths[msg_source][pdu_specific]["total"]
                        _num_packages = self._incomplete_received_pdu_lengths[msg_source][pdu_specific]["num_packages"]
                        pgn = self._incomplete_received_pdus[msg_source][pdu_specific].arbitration_id.pgn
                        pgn_msb = ((pgn.value & 0xFF0000) >> 16)
                        _pgn_middle = ((pgn.value & 0x00FF00) >> 8)
                        _pgn_lsb = 0

                        div, mod = divmod(total_length, 256)
                        can_message = Message(arbitration_id=arbitration_id.can_id,
                                              extended_id=True,
                                              dlc=8,
                                              data=[constants.CM_MSG_TYPE_EOM_ACK,
                                                    mod,  # total_length % 256,
                                                    div,  # total_length / 256,
                                                    _num_packages,
                                                    0xFF,
                                                    _pgn_lsb,
                                                    _pgn_middle,
                                                    pgn_msb])
                        self.can_bus.send(can_message)

                    return self._process_eom_ack(msg)

    def _process_rts(self, msg):
        if msg.arbitration_id.source_address not in self._incomplete_received_pdus:
            self._incomplete_received_pdus[msg.arbitration_id.source_address] = {}
            self._incomplete_received_pdu_lengths[msg.arbitration_id.source_address] = {}

        # Delete any previous messages that were not finished correctly
        if msg.arbitration_id.pgn.pdu_specific in self._incomplete_received_pdus[msg.arbitration_id.source_address]:
            del self._incomplete_received_pdus[msg.arbitration_id.source_address][msg.arbitration_id.pgn.pdu_specific]
            del self._incomplete_received_pdu_lengths[msg.arbitration_id.source_address][
                msg.arbitration_id.pgn.pdu_specific]

        if msg.data[0] == constants.CM_MSG_TYPE_BAM:
            self._incomplete_received_pdus[msg.arbitration_id.source_address][0xFF] = self._pdu_type()
            self._incomplete_received_pdus[msg.arbitration_id.source_address][0xFF].arbitration_id.pgn.value = int(
                ("%.2X%.2X%.2X" % (msg.data[7], msg.data[6], msg.data[5])), 16)
            if self._incomplete_received_pdus[msg.arbitration_id.source_address][
                    0xFF].arbitration_id.pgn.is_destination_specific:
                self._incomplete_received_pdus[msg.arbitration_id.source_address][
                    0xFF].arbitration_id.pgn.pdu_specific = msg.arbitration_id.pgn.pdu_specific
            self._incomplete_received_pdus[msg.arbitration_id.source_address][
                0xFF].arbitration_id.source_address = msg.arbitration_id.source_address
            self._incomplete_received_pdus[msg.arbitration_id.source_address][0xFF].data = []
            _message_size = int("%.2X%.2X" % (msg.data[2], msg.data[1]), 16)
            self._incomplete_received_pdu_lengths[msg.arbitration_id.source_address][0xFF] = {"total": _message_size,
                                                                                              "chunk": 255,
                                                                                              "num_packages": msg.data[
                                                                                                  3], }
        else:
            self._incomplete_received_pdus[msg.arbitration_id.source_address][
                msg.arbitration_id.pgn.pdu_specific] = self._pdu_type()
            self._incomplete_received_pdus[msg.arbitration_id.source_address][
                msg.arbitration_id.pgn.pdu_specific].arbitration_id.pgn.value = int(
                ("%.2X%.2X%.2X" % (msg.data[7], msg.data[6], msg.data[5])), 16)
            if self._incomplete_received_pdus[msg.arbitration_id.source_address][
                    msg.arbitration_id.pgn.pdu_specific].arbitration_id.pgn.is_destination_specific:
                self._incomplete_received_pdus[msg.arbitration_id.source_address][
                    msg.arbitration_id.pgn.pdu_specific].arbitration_id.pgn.pdu_specific = msg.arbitration_id.pgn.pdu_specific
            self._incomplete_received_pdus[msg.arbitration_id.source_address][
                msg.arbitration_id.pgn.pdu_specific].arbitration_id.source_address = msg.arbitration_id.source_address
            self._incomplete_received_pdus[msg.arbitration_id.source_address][
                msg.arbitration_id.pgn.pdu_specific].data = []
        _message_size = int("%.2X%.2X" % (msg.data[2], msg.data[1]), 16)
        self._incomplete_received_pdu_lengths[msg.arbitration_id.source_address][
            msg.arbitration_id.pgn.pdu_specific] = {"total": _message_size, "chunk": 255, "num_packages": msg.data[3], }

        if msg.data[0] != constants.CM_MSG_TYPE_BAM:
            for _listener in self.j1939_notifier.listeners:
                if isinstance(_listener, Node):
                    # find a Node object so we can search its list of known node addresses
                    # for this node - if we find it we are responsible for sending the CTS message
                    if _listener.address == msg.arbitration_id.pgn.pdu_specific or msg.arbitration_id.pgn.pdu_specific in _listener.address_list:
                        _cts_arbitration_id = ArbitrationID(source_address=msg.arbitration_id.pgn.pdu_specific)
                        _cts_arbitration_id.pgn.value = constants.PGN_TP_CONNECTION_MANAGEMENT
                        _cts_arbitration_id.pgn.pdu_specific = msg.arbitration_id.source_address
                        _data = [0x11, msg.data[4], 0x01, 0xFF, 0xFF]
                        _data.extend(msg.data[5:])
                        cts_msg = Message(extended_id=True, arbitration_id=_cts_arbitration_id.can_id, data=_data,
                                          dlc=8)

                        # send clear to send
                        self.can_bus.send(cts_msg)
                        return

    def _process_cts(self, msg):
        if msg.arbitration_id.pgn.pdu_specific in self._incomplete_transmitted_pdus:
            if msg.arbitration_id.source_address in self._incomplete_transmitted_pdus[
                    msg.arbitration_id.pgn.pdu_specific]:
                # Next packet number in CTS message (Packet numbers start at 1 not 0)
                start_index = msg.data[2] - 1
                # Using total number of packets in CTS message
                end_index = start_index + msg.data[1]
                for _msg in self._incomplete_transmitted_pdus[msg.arbitration_id.pgn.pdu_specific][
                        msg.arbitration_id.source_address][start_index:end_index]:
                    self.can_bus.send(_msg)

    def _process_eom_ack(self, msg):
        if (msg.arbitration_id.pgn.value - msg.arbitration_id.pgn.pdu_specific) == constants.PGN_TP_DATA_TRANSFER:
            self._incomplete_received_pdus[msg.arbitration_id.source_address][
                msg.arbitration_id.pgn.pdu_specific].timestamp = msg.timestamp
            retval = copy.deepcopy(
                self._incomplete_received_pdus[msg.arbitration_id.source_address][msg.arbitration_id.pgn.pdu_specific])
            retval.data = retval.data[:self._incomplete_received_pdu_lengths[msg.arbitration_id.source_address][
                msg.arbitration_id.pgn.pdu_specific]["total"]]
            del self._incomplete_received_pdus[msg.arbitration_id.source_address][msg.arbitration_id.pgn.pdu_specific]
            del self._incomplete_received_pdu_lengths[msg.arbitration_id.source_address][
                msg.arbitration_id.pgn.pdu_specific]
        else:
            if msg.arbitration_id.pgn.pdu_specific in self._incomplete_received_pdus:
                if msg.arbitration_id.source_address in self._incomplete_received_pdus[
                        msg.arbitration_id.pgn.pdu_specific]:
                    self._incomplete_received_pdus[msg.arbitration_id.pgn.pdu_specific][
                        msg.arbitration_id.source_address].timestamp = msg.timestamp
                    retval = copy.deepcopy(self._incomplete_received_pdus[msg.arbitration_id.pgn.pdu_specific][
                        msg.arbitration_id.source_address])
                    retval.data = retval.data[:
                                              self._incomplete_received_pdu_lengths[msg.arbitration_id.pgn.pdu_specific][
                                                  msg.arbitration_id.source_address]["total"]]
                    del self._incomplete_received_pdus[msg.arbitration_id.pgn.pdu_specific][
                        msg.arbitration_id.source_address]
                    del self._incomplete_received_pdu_lengths[msg.arbitration_id.pgn.pdu_specific][
                        msg.arbitration_id.source_address]
                else:
                    retval = None
            else:
                retval = None
            if msg.arbitration_id.pgn.pdu_specific in self._incomplete_transmitted_pdus:
                if msg.arbitration_id.source_address in self._incomplete_transmitted_pdus[
                        msg.arbitration_id.pgn.pdu_specific]:
                    del self._incomplete_transmitted_pdus[msg.arbitration_id.pgn.pdu_specific][
                        msg.arbitration_id.source_address]

        return retval

    def _process_bam(self, msg):
        self._process_rts(msg)

    def _process_abort(self, msg):
        if msg.arbitration_id.pgn.pdu_specific in self._incomplete_received_pdus:
            if msg.source in self._incomplete_received_pdus[msg.arbitration_id.pgn.pdu_specific]:
                del self._incomplete_received_pdus[msg.arbitration_id.pgn.pdu_specific][
                    msg.arbitration_id.source_address]

    def _throttler_function(self):
        while self.can_notifier.running.is_set():
            _msg = None
            try:
                _msg = self._long_message_segment_queue.get(timeout=0.1)
            except Empty:
                pass
            if _msg is not None:
                self.can_bus.send(_msg)

    @property
    def transmissions_in_progress(self):
        retval = 0
        for _tx_address in self._incomplete_transmitted_pdus:
            retval += len(self._incomplete_transmitted_pdus[_tx_address])
        for _rx_address in self._incomplete_received_pdus:
            retval += len(self._incomplete_received_pdus[_rx_address])
        return retval
