"""
pyneovi interface module.

pyneovi is a Python wrapper around the API provided by Intrepid Control Systems
for communicating with their NeoVI range of devices.

Implementation references:
* http://pyneovi.readthedocs.io/en/latest/
* https://bitbucket.org/Kemp_J/pyneovi
"""

import logging

logger = logging.getLogger(__name__)

try:
    import queue
except ImportError:
    import Queue as queue

try:
    from neovi import neodevice
    from neovi import neovi
    from neovi.structures import icsSpyMessage
except ImportError as e:
    logger.warning("Cannot load pyneovi: %s", e)

from can import Message
from can.bus import BusABC


SPY_STATUS_XTD_FRAME = 0x04
SPY_STATUS_REMOTE_FRAME = 0x08


def neo_device_name(device_type):
    names = {
        neovi.NEODEVICE_BLUE: 'neoVI BLUE',
        neovi.NEODEVICE_DW_VCAN: 'ValueCAN',
        neovi.NEODEVICE_FIRE: 'neoVI FIRE',
        neovi.NEODEVICE_VCAN3: 'ValueCAN3',
        neovi.NEODEVICE_YELLOW: 'neoVI YELLOW',
        neovi.NEODEVICE_RED: 'neoVI RED',
        neovi.NEODEVICE_ECU: 'neoECU',
        # neovi.NEODEVICE_IEVB: ''
    }
    return names.get(device_type, 'Unknown neoVI')


class NeoVIBus(BusABC):
    """
    The CAN Bus implemented for the pyneovi interface.
    """

    def __init__(self, channel=None, can_filters=None, **config):
        """

        :param int channel:
            The Channel id to create this bus with.
        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

                >>> [{"can_id": 0x11, "can_mask": 0x21}]

        """
        type_filter = config.get('type_filter', neovi.NEODEVICE_ALL)
        neodevice.init_api()
        self.device = neodevice.find_devices(type_filter)[0]
        self.device.open()
        self.channel_info = '%s %s on channel %s' % (
            neo_device_name(self.device.get_type()),
            self.device.device.SerialNumber,
            channel
        )

        self.sw_filters = None
        self.set_filters(can_filters)
        self.rx_buffer = queue.Queue()

        self.network = int(channel) if channel is not None else None
        self.device.subscribe_to(self._rx_buffer, network=self.network)

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        self.device.pump_messages = False
        if self.device.msg_queue_thread is not None:
            self.device.msg_queue_thread.join()

    def _rx_buffer(self, msg, user_data):
        self.rx_buffer.put_nowait(msg)

    def _is_filter_match(self, arb_id):
        """
        If SW filtering is used, checks if the `arb_id` matches any of
        the filters setup.

        :param int arb_id:
            CAN ID to check against.

        :return:
            True if `arb_id` matches any filters
            (or if SW filtering is not used).
        """
        if not self.sw_filters:
            # Filtering done on HW or driver level or no filtering
            return True
        for can_filter in self.sw_filters:
            if not (arb_id ^ can_filter['can_id']) & can_filter['can_mask']:
                return True

        logging.info("%s not matching" % arb_id)
        return False

    def _ics_msg_to_message(self, ics_msg):
        return Message(
            timestamp=neovi.GetTimeStampForMsg(self.device.handle, ics_msg)[1],
            arbitration_id=ics_msg.ArbIDOrHeader,
            data=ics_msg.Data,
            dlc=ics_msg.NumberBytesData,
            extended_id=bool(ics_msg.StatusBitField &
                             SPY_STATUS_XTD_FRAME),
            is_remote_frame=bool(ics_msg.StatusBitField &
                                 SPY_STATUS_REMOTE_FRAME),
        )

    def recv(self, timeout=None):
        try:
            ics_msg = self.rx_buffer.get(block=True, timeout=timeout)
        except queue.Empty:
            pass
        else:
            if ics_msg.NetworkID == self.network and \
                    self._is_filter_match(ics_msg.ArbIDOrHeader):
                return self._ics_msg_to_message(ics_msg)

    def send(self, msg):
        data = tuple(msg.data)
        flags = SPY_STATUS_XTD_FRAME if msg.is_extended_id else 0
        if msg.is_remote_frame:
            flags |= SPY_STATUS_REMOTE_FRAME

        ics_msg = icsSpyMessage()
        ics_msg.ArbIDOrHeader = msg.arbitration_id
        ics_msg.NumberBytesData = len(data)
        ics_msg.Data = data
        ics_msg.StatusBitField = flags
        ics_msg.StatusBitField2 = 0
        ics_msg.DescriptionID = self.device.tx_id
        self.device.tx_id += 1
        self.device.tx_raw_message(ics_msg, self.network)

    def set_filters(self, can_filters=None):
        """Apply filtering to all messages received by this Bus.

        Calling without passing any filters will reset the applied filters.

        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

            >>> [{"can_id": 0x11, "can_mask": 0x21}]

            A filter matches, when
            ``<received_can_id> & can_mask == can_id & can_mask``

        """
        self.sw_filters = can_filters

        if self.sw_filters is None:
            logger.info("Filtering has been disabled")
        else:
            for can_filter in can_filters:
                can_id = can_filter["can_id"]
                can_mask = can_filter["can_mask"]
                logger.info("Filtering on ID 0x%X, mask 0x%X", can_id, can_mask)
