#!/usr/bin/python
#
# ----------------------------------------------------------------------
# pylint: disable=invalid-name
# ----------------------------------------------------------------------
#
# **********************************************************************
#
# File Name: dg.py
# Author(s): mohtake <mohtake@dgtech.com>
# Target Project: python-can
# Description:
# Notes:
# **********************************************************************
#

"""DG BEACON python-can module"""

# ----------------------------------------------------------------------
import weakref
from can import BusABC, Message
from can.interfaces.dg.dg_gryphon_protocol import server_commands
from can.broadcastmanager import (
    LimitedDurationCyclicSendTaskABC,
    ModifiableCyclicTaskABC,
)


class DGBus(BusABC):
    """ Beacon python-can backend API """

    def __init__(self, channel=1, **kwargs):
        """
        :param int channel:
            Channel which the bus will be initialized on.

        :param bool is_fd:
            Specifies if bus is CANFD or not.

        :param str ip:
            IP at which the DG device is connected.

        :param int bitrate:
            Bitrate for the bus.

        :param bool termination:
            Termination for the bus (on or off).

        :param int data_bitrate:
            The data phase bitrate for the bus (Optional, only if is_fd is
            True).

        :param bool pre_iso:
            Specifies if bus should be CANFD PREISO (Optional, only if is_fd is
            True).

        :return: None
        """
        self.ip = kwargs["ip"] if "ip" in kwargs else "localhost"
        self.is_fd = kwargs["is_fd"] if "is_fd" in kwargs else False
        self.bitrate = kwargs["bitrate"] if "bitrate" in kwargs else 500000
        self.termination = kwargs["termination"] if "termination" in kwargs \
            else True
        self.pre_iso = kwargs["pre_iso"] if "pre_iso" in kwargs else False
        self.data_bitrate = kwargs["data_bitrate"] if "data_bitrate" in \
            kwargs else 2000000
        self.channel = channel

        self.beacon = server_commands.Gryphon(self.ip)
        self.beacon.CMD_SERVER_REG("root", "dgbeacon")
        self.beacon.CMD_BCAST_ON()
        if not self.is_fd:
            self.mode = "CAN"
            temp_mode = [0]
        elif self.pre_iso:
            self.mode = "CANPREISO"
            temp_mode = [2]
        else:
            self.mode = "CANFD"
            temp_mode = [1]
        temp_databitr = DGBus._int_to_list(self.data_bitrate)
        temp_databitr.reverse()
        self.beacon.CMD_CARD_IOCTL(self.channel,
                                   self.beacon.IOCTL_GSETFASTBITRATE,
                                   data_in=temp_databitr)

        temp_bitr = DGBus._int_to_list(self.bitrate)
        temp_bitr.reverse()
        temp_term = [1] if self.termination else [0]

        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_SETINTTERM,
                                   data_in=temp_term)
        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_GSETBITRATE,
                                   data_in=temp_bitr)
        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_GCANSETMODE,
                                   data_in=temp_mode)
        self.beacon.CMD_INIT(self.channel, value_in=self.beacon.ALWAYS_INIT)
        self.beacon.CMD_CARD_SET_FILTER_MODE(self.channel,
                                             self.beacon.FILTER_OFF_PASS_ALL)
        self.channel_info = ("dg channel '%s' on " + self.mode) % self.channel
        super(DGBus, self).__init__(self.channel, None)

    @staticmethod
    def _int_to_list(num):
        """
        Internal method to take a decimal int and convert to lst of int bytes

        :param int num:
            Number (decimal) to be converted
        :return:
            list of bytes (MSB to LSB)
        :rtype:
            list
        """
        hdrTemp = hex(num).rstrip('L')[2:]
        if len(hdrTemp) % 2 != 0:
            hdrTemp = '0' + hdrTemp
        return [int(hdrTemp[i:i + 2], 16) for i in range(0, len(hdrTemp), 2)]

    @staticmethod
    def _list_to_int(datab):
        """
        Internal method to take a list of int bytes and convert to a decimal
        int

        :param list datab:
            List of bytes to be converted (MSB to LSB)
        :return:
            Decimal int corresponding to list
        :rtype:
            int
        """
        header = "0x"
        for item in datab:
            if item < 16:
                header = header + '0' + hex(item)[2:]
            else:
                header = header + hex(item)[2:]
        return int(header, 16)

    @classmethod
    def msg_to_dict(cls, msg):
        """
        Method to convert Message type to gryph dict

        :param can.Message msg:
            Message object to be converted
        :return:
            Gryphon compatible dictionary
        :rtype:
            dict

        Conversion table::

            float       msg.timestamp            ->  msgForm["timestamp"] (N/A)
            bool        msg.is_remote_frame      ->  N/A
            bool        msg.is_extended_id       ->  msgForm["hdrlen"]
            bool        msg.is_error_frame       ->  N/A
            int         msg.arbitration_id       ->  msgForm["hdr"],
                msgForm["hdrlen"]
            int         msg.dlc                  ->  N/A
            bytearray   msg.data                 ->  msgForm["data"]
            bool        msg.is_fd                ->  N/A
            bool        msg.bitrate_switch       ->  N/A
            bool        msg.error_state_indicator->  N/A
            int         msg.channel              ->  N/A
        """
        msgForm = {}
        msgForm["hdr"] = cls._int_to_list(msg.arbitration_id)
        msgForm["hdrlen"] = len(msgForm["hdr"])
        msgForm["data"] = msg.data
        return msgForm

    @classmethod
    def _dict_to_msg(cls, msgForm):
        """
        Method to encode gryph dict to Message

        :param dict msgForm:
            Dictionary to be converted
        :return:
            Message object
        :rtype:
            can.Message
        """
        timestamp = \
            msgForm["GCprotocol"]["body"]["data"]["timestamp"] / 1000000.0
        headerForm = cls._list_to_int(
            msgForm["GCprotocol"]["body"]["data"]["hdr"])
        data = msgForm["GCprotocol"]["body"]["data"]["data"]
        extId = (msgForm["GCprotocol"]["body"]["data"]["hdrlen"] == 8)
        isFD = msgForm["GCprotocol"]["body"]["data"]["status"] == 48
        return Message(timestamp=timestamp, arbitration_id=headerForm,
                       data=data, is_extended_id=extId, is_fd=isFD)

    def send(self, msg, timeout=None):
        """send a can message
        """
        msgForm = self.msg_to_dict(msg)
        self.beacon.FT_DATA_TX(self.channel, msgForm)

    def _send_periodic_internal(self, msg, period, duration=None):
        """send a periodic can message
        """
        msgForm = {}
        msgForm["message_list"] = [self.msg_to_dict(msg[0])]
        msgForm["message_list"][0]["tx_period"] = int(period * 1000000)
        msgForm["message_list"][0]["period_in_microsec"] = True
        if duration is None:
            cycles = 4294967295
        else:
            cycles = int(duration / period)
        reply = self.beacon.CMD_SCHED_TX(self.channel, msgForm,
                                         iterations=cycles)
        return Scheduling(msg, period, duration, reply["schedule_id"],
                          weakref.ref(self.beacon), self.channel)

    def _recv_internal(self, timeout=None):
        """wait for a received can message from BEACON,
           or timeout
        """
        if timeout is None:
            reply = self.beacon.FT_DATA_WAIT_FOR_RX(timeout=.5)
            while reply is None:
                reply = self.beacon.FT_DATA_WAIT_FOR_RX(timeout=.5)
            return self._dict_to_msg(reply), True

        reply = self.beacon.FT_DATA_WAIT_FOR_RX(timeout=timeout)
        if reply is not None:
            return self._dict_to_msg(reply), True
        return None, True

    def _apply_filters(self, filters):
        """set the filters on the BEACON
        """
        if filters is None:
            reply = self.beacon.CMD_CARD_GET_FILTER_HANDLES(self.channel)
            for item in reply["GCprotocol"]["body"]["data"]["filter_handles"]:
                self.beacon.CMD_CARD_MODIFY_FILTER(self.channel,
                                                   self.beacon.DELETE_FILTER,
                                                   filter_handle=item)
            self.beacon.CMD_CARD_SET_DEFAULT_FILTER(
                self.channel,
                self.beacon.DEFAULT_FILTER_PASS)
            return
        dataFil = {}
        counter = 0
        dataFil["flags"] = (self.beacon.FILTER_FLAG_PASS
                            | self.beacon.FILTER_FLAG_ACTIVE
                            | self.beacon.FILTER_FLAG_OR_BLOCKS
                            | self.beacon.FILTER_FLAG_SAMPLING_INACTIVE)
        dataFil["filter_blocks"] = []
        for item in filters:
            dataFil["filter_blocks"].append({})
            dataFil["filter_blocks"][counter]["byte_offset"] = 0
            dataFil["filter_blocks"][counter]["data_type"] = \
                self.beacon.FILTER_DATA_TYPE_HEADER
            dataFil["filter_blocks"][counter]["operator"] = \
                self.beacon.BIT_FIELD_CHECK
            dataFil["filter_blocks"][counter]["mask"] = \
                self._int_to_list(item["can_mask"])
            dataFil["filter_blocks"][counter]["pattern"] = \
                self._int_to_list(item["can_id"])
            counter += 1
        self.beacon.CMD_CARD_ADD_FILTER(self.channel, dataFil)
        self.beacon.CMD_CARD_SET_FILTER_MODE(self.channel,
                                             self.beacon.FILTER_ON)
        self.beacon.CMD_CARD_SET_DEFAULT_FILTER(
            self.channel,
            self.beacon.DEFAULT_FILTER_BLOCK)

    def shutdown(self):
        """stop the BEACON
        """
        del self.beacon

    def flush_tx_buffer(self):
        """re-initialize the can channel
        """
        self.beacon.CMD_INIT(self.channel, value_in=self.beacon.ALWAYS_INIT)

    def detect_channel_config(self, channel):
        """
        Detect the current configuration of a specified channel

        :param int channel:
            The channel to detect the config of
        :return:
            A dict describing the config of the channel
        :rtype:
            dict
        """
        temp = {}
        modeInt = self.beacon.CMD_CARD_IOCTL(channel,
                                             self.beacon.IOCTL_GCANGETMODE,
                                             data_in=[0])
        modeInt = modeInt["GCprotocol"]["body"]["data"]["ioctl_data"][0]
        if modeInt == 0:
            is_fd = False
        elif modeInt == 1:
            is_fd = True
            pre_iso = False
        else:
            is_fd = True
            pre_iso = True

        bitrArr = self.beacon.CMD_CARD_IOCTL(channel,
                                             self.beacon.IOCTL_GGETBITRATE,
                                             data_in=[0, 0, 0, 0])
        bitrArr = bitrArr["GCprotocol"]["body"]["data"]["ioctl_data"]
        bitrArr.reverse()
        bitr = DGBus._list_to_int(bitrArr)

        termInt = self.beacon.CMD_CARD_IOCTL(channel,
                                             self.beacon.IOCTL_GETINTTERM,
                                             data_in=[0])
        termInt = termInt["GCprotocol"]["body"]["data"]["ioctl_data"][0]
        term = termInt == 1

        if is_fd:
            dataArr = self.beacon.CMD_CARD_IOCTL(
                channel,
                self.beacon.IOCTL_GGETFASTBITRATE,
                data_in=[0, 0, 0, 0])
            dataArr = dataArr["GCprotocol"]["body"]["data"]["ioctl_data"]
            dataArr.reverse()
            data = DGBus._list_to_int(dataArr)
            temp["data_bitrate"] = data
            temp["pre_iso"] = pre_iso

        temp["channel"] = channel
        temp["is_fd"] = is_fd
        temp["ip"] = self.ip
        temp["bitrate"] = bitr
        temp["termination"] = term
        return temp

    def _detect_available_configs(self):
        """ Returns list of dicts that contains available configs for the
            beacon
        """
        reply = []
        for i in range(1, 9):
            temp = self.detect_channel_config(i)
            reply.append(temp)
        return reply

    #
    # METHODS SPECIFIC TO DG INTERFACE
    #
    def set_mode(self, new_mode):
        """
        When going from CAN to CANFD or CANPREISO, this method will default
        to the previously set bitrate. Call :meth:`set_databitr` to set bitrate
        before switching modes.

        :param str new_mode:
            The new mode for the bus, either "CAN", "CANFD", or "CANPREISO
        """
        self.mode = new_mode
        if new_mode == "CAN":
            temp_mode = [0]
            self.is_fd = False
            self.pre_iso = False
        elif new_mode == "CANFD":
            temp_mode = [1]
            self.is_fd = True
            self.pre_iso = False
        else:
            temp_mode = [2]
            self.is_fd = True
            self.pre_iso = False

        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_GCANSETMODE,
                                   data_in=temp_mode)
        self.beacon.CMD_INIT(self.channel, value_in=self.beacon.ALWAYS_INIT)

    def set_bitrate(self, new_bitr):
        """
        :param int new_bitr:
            The new bitrate
        """
        self.bitrate = new_bitr
        temp_bitrate = DGBus._int_to_list(new_bitr)
        temp_bitrate.reverse()
        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_GSETBITRATE,
                                   data_in=temp_bitrate)
        self.beacon.CMD_INIT(self.channel, value_in=self.beacon.ALWAYS_INIT)

    def set_termination(self, new_term):
        """
        :param bool new_term:
            Set termination to on (True) or off (False)
        """
        self.termination = new_term
        temp_term = [1] if new_term else [0]
        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_SETINTTERM,
                                   data_in=temp_term)
        self.beacon.CMD_INIT(self.channel, value_in=self.beacon.ALWAYS_INIT)

    def set_databitr(self, new_databitr):
        """
        :param int new_databitr:
            The new data phase bitrate
        """
        self.data_bitrate = new_databitr
        temp_databitr = DGBus._int_to_list(new_databitr)
        temp_databitr.reverse()
        self.beacon.CMD_CARD_IOCTL(self.channel,
                                   self.beacon.IOCTL_GSETFASTBITRATE,
                                   data_in=temp_databitr)
        self.beacon.CMD_INIT(self.channel, value_in=self.beacon.ALWAYS_INIT)

    def set_event_rx(self, state):
        """
        :param bool state:
            Set event enabling to on (True) or off (False)
        """
        if state:
            self.beacon.CMD_EVENT_ENABLE(self.channel)
        else:
            self.beacon.CMD_EVENT_DISABLE(self.channel, 0)


class Scheduling(LimitedDurationCyclicSendTaskABC, ModifiableCyclicTaskABC):
    """ Class that handles task interface between Beacon scheduler and
        python-can
    """

    def __init__(self, message, period, duration, idIn, _beacon, channel):
        super(Scheduling, self).__init__(message, period, duration)
        self.idIn = idIn
        self.beaconref = _beacon
        self.channel = channel

    def modify_data(self, message):
        self.beaconref().CMD_SCHED_MSG_REPLACE(self.idIn,
                                               DGBus.msg_to_dict(message),
                                               index=0)

    def stop(self):
        self.beaconref().CMD_SCHED_KILL_TX(self.channel, self.idIn)
