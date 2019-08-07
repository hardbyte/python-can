#!/usr/bin/python
#
# ----------------------------------------------------------------------
# pylint: disable=invalid-name
# ----------------------------------------------------------------------
#
# **********************************************************************
# Copyright (C) 2019 DG Technologies/Dearborn Group, Inc. All rights
# reserved. The copyright here does not evidence any actual or intended
# publication.
#
# File Name: dg.py
# Author(s): mohtake <mohtake@dgtech.com>
# Target Project: python-can
# Description:
# Notes:
# ----------------------------------------------------------------------
# Release Revision: $Rev: 74 $
# Release Date: $Date: 2019/08/05 21:07:52 $
# Revision Control Tags: $Tags: tip $
# ----------------------------------------------------------------------
# **********************************************************************
#

"""DG BEACON python-can module"""

# ----------------------------------------------------------------------
import weakref
# import sys
from can import BusABC, Message
from can.interfaces.dg.dg_gryphon_protocol import server_commands
from can.broadcastmanager import LimitedDurationCyclicSendTaskABC, ModifiableCyclicTaskABC


class dgBus(BusABC):
    """ Beacon python-can backend API """

    # Init method
    def __init__(self, chan=1, mode="CAN", ip="localhost", bitrate=500000, termination=True,
                 databitr=2000000, **kwargs):
        self.beacon = server_commands.Gryphon(ip)
        self.beacon.CMD_SERVER_REG("root", "dgbeacon")
        self.beacon.CMD_BCAST_ON()
        self.channel = chan

        self.bitrate = dgBus._int2list(bitrate)
        self.bitrate.reverse()
        self.termination = [1] if termination else [0]
        if mode == "CAN":
            self.mode = [0]
        else:
            if mode == "CANFD":
                self.mode = [1]
            else:
                self.mode = [2]
            self.databitr = dgBus._int2list(databitr)
            self.databitr.reverse()
            self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_GSETFASTBITRATE,
                                       data_in=self.databitr)

        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_SETINTTERM,
                                   data_in=self.termination)
        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_GSETBITRATE,
                                   data_in=self.bitrate)
        self.beacon.CMD_CARD_IOCTL(self.channel, self.beacon.IOCTL_GCANSETMODE,
                                   data_in=self.mode)
        self.beacon.CMD_INIT(self.channel, value_in=self.beacon.ALWAYS_INIT)
        self.beacon.CMD_CARD_SET_FILTER_MODE(self.channel, self.beacon.FILTER_OFF_PASS_ALL)
        self.channel_info = ("dg channel '%s' on " + mode) % self.channel
        # is this necessary
        self.ip = ip
        super(dgBus, self).__init__(chan, None)

    # Next two methods use MSB to LSB
    # Internal method to take a decimal int and convert to lst of int bytes
    @staticmethod
    def _int2list(num):
        hdrTemp = hex(num).rstrip('L')[2:]
        if len(hdrTemp) % 2 != 0:
            hdrTemp = '0' + hdrTemp
        return [int(hdrTemp[i:i + 2], 16) for i in range(0, len(hdrTemp), 2)]

    # Internal method to take a list of int bytes and convert to a decimal int
    @staticmethod
    def _list2int(datab):
        header = "0x"
        for item in datab:
            if item < 16:
                header = header + '0' + hex(item)[2:]
            else:
                header = header + hex(item)[2:]
        return int(header, 16)

    # Method to decode Message type to gryph dict
    @classmethod
    def decode_msg(cls, msg):
        """Conversion table

        float   msg.timestamp               ->  msgForm["timestamp"] (N/A)
        bool    msg.is_remote_frame         ->  N/A
        bool    msg.is_extended_id          ->  msgForm["hdrlen"]
        bool    msg.is_error_frame          ->  N/A
        Int     msg.arbitration_id          ->  msgForm["hdr"], msgForm["hdrlen"]
        int     msg.dlc                     ->  N/A
        byteArr msg.data                    ->  msgForm["data"]
        bool    msg.is_fd                   ->  N/A
        bool    msg.bitrate_switch          ->  N/A
        bool    msg.error_state_indicator   ->  N/A
        int?    msg.channel                 ->  N/A

        """
        msgForm = {}
        msgForm["hdr"] = cls._int2list(msg.arbitration_id)
        msgForm["hdrlen"] = len(msgForm["hdr"])
        msgForm["data"] = msg.data
        return msgForm

    # Method to encode gryph dict to Message
    @classmethod
    def _encode_msg(cls, msgForm):
        timestamp = msgForm["GCprotocol"]["body"]["data"]["timestamp"] / 1000000.0
        headerForm = cls._list2int(msgForm["GCprotocol"]["body"]["data"]["hdr"])
        data = msgForm["GCprotocol"]["body"]["data"]["data"]
        extId = (msgForm["GCprotocol"]["body"]["data"]["hdrlen"] == 8)
        isFD = msgForm["GCprotocol"]["body"]["data"]["status"] == 48
        return Message(timestamp=timestamp, arbitration_id=headerForm,
                       data=data, is_extended_id=extId, is_fd=isFD)

    # Send method
    def send(self, msg, timeout=None):
        msgForm = self.decode_msg(msg)
        self.beacon.FT_DATA_TX(self.channel, msgForm)

    # Scheduled transmit
    def _send_periodic_internal(self, msg, period, duration=None):
        msgForm = {}
        msgForm["message_list"] = [self.decode_msg(msg[0])]
        msgForm["message_list"][0]["tx_period"] = int(period * 1000000)
        msgForm["message_list"][0]["period_in_microsec"] = True
        if duration is None:
            cycles = 4294967295
        else:
            cycles = int(duration / period)
        reply = self.beacon.CMD_SCHED_TX(self.channel, msgForm, iterations=cycles)
        return Scheduling(msg, period, duration, reply["schedule_id"],
                          weakref.ref(self.beacon), self.channel)

    # Receive method
    def _recv_internal(self, timeout=None):
        if timeout is None:
            reply = self.beacon.FT_DATA_WAIT_FOR_RX(timeout=.5)
            while reply is None:
                reply = self.beacon.FT_DATA_WAIT_FOR_RX(timeout=.5)
            return self._encode_msg(reply), True

        reply = self.beacon.FT_DATA_WAIT_FOR_RX(timeout=timeout)
        if reply is not None:
            return self._encode_msg(reply), True
        return None, True

    # Filtering method
    def _apply_filters(self, filters):
        if filters is None:
            reply = self.beacon.CMD_CARD_GET_FILTER_HANDLES(self.channel)
            for item in reply["GCprotocol"]["body"]["data"]["filter_handles"]:
                self.beacon.CMD_CARD_MODIFY_FILTER(self.channel,
                                                   self.beacon.DELETE_FILTER, filter_handle=item)
            self.beacon.CMD_CARD_SET_DEFAULT_FILTER(self.channel, self.beacon.DEFAULT_FILTER_PASS)
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
            dataFil["filter_blocks"][counter]["data_type"] = self.beacon.FILTER_DATA_TYPE_HEADER
            dataFil["filter_blocks"][counter]["operator"] = self.beacon.BIT_FIELD_CHECK
            dataFil["filter_blocks"][counter]["mask"] = self._int2list(item["can_mask"])
            dataFil["filter_blocks"][counter]["pattern"] = self._int2list(item["can_id"])
            counter += 1
        self.beacon.CMD_CARD_ADD_FILTER(self.channel, dataFil)
        self.beacon.CMD_CARD_SET_FILTER_MODE(self.channel, self.beacon.FILTER_ON)
        self.beacon.CMD_CARD_SET_DEFAULT_FILTER(self.channel, self.beacon.DEFAULT_FILTER_BLOCK)

    # Shutdown Method
    def shutdown(self):
        # print sys.getrefcount(self.beacon)
        # reply = self.beacon.CMD_SCHED_GET_IDS()
        # if reply is None:
        #     print "[]"
        # else:
        #     print reply["GCprotocol"]["body"]["data"]["schedules"]
        del self.beacon

    # "Flushing" the TX buffer (just re-inits the channel)
    def flush_tx_buffer(self):
        self.beacon.CMD_INIT(self.channel, value_in=self.beacon.ALWAYS_INIT)

    # Returns list of dicts that contains available configs for the beacon
    def _detect_available_configs(self):
        reply = []
        for i in range(1, 9):
            temp = {}
            modeInt = self.beacon.CMD_CARD_IOCTL(i, self.beacon.IOCTL_GCANGETMODE, data_in=[0])
            modeInt = modeInt["GCprotocol"]["body"]["data"]["ioctl_data"][0]
            if modeInt == 0:
                mode = "CAN"
            elif modeInt == 1:
                mode = "CANFD"
            else:
                mode = "CANPREISO"

            bitrArr = self.beacon.CMD_CARD_IOCTL(i, self.beacon.IOCTL_GGETBITRATE,
                                                 data_in=[0, 0, 0, 0])
            bitrArr = bitrArr["GCprotocol"]["body"]["data"]["ioctl_data"]
            bitrArr.reverse()
            bitr = dgBus._list2int(bitrArr)

            termInt = self.beacon.CMD_CARD_IOCTL(i, self.beacon.IOCTL_GETINTTERM, data_in=[0])
            termInt = termInt["GCprotocol"]["body"]["data"]["ioctl_data"][0]
            term = termInt == 1

            if mode != "CAN":
                dataArr = self.beacon.CMD_CARD_IOCTL(i, self.beacon.IOCTL_GGETFASTBITRATE,
                                                     data_in=[0, 0, 0, 0])
                dataArr = dataArr["GCprotocol"]["body"]["data"]["ioctl_data"]
                dataArr.reverse()
                data = dgBus._list2int(dataArr)
                temp["databitr"] = data

            temp["chan"] = i
            temp["mode"] = mode
            temp["ip"] = self.ip
            temp["bitrate"] = bitr
            temp["termination"] = term
            reply.append(temp)
        return reply


class Scheduling(LimitedDurationCyclicSendTaskABC, ModifiableCyclicTaskABC):
    """ Class that handles task interface between Beacon scheduler and python-can """

    def __init__(self, message, period, duration, idIn, _beacon, channel):
        super(Scheduling, self).__init__(message, period, duration)
        self.idIn = idIn
        self.beaconref = _beacon
        self.channel = channel

    def modify_data(self, message):
        self.beaconref().CMD_SCHED_MSG_REPLACE(self.idIn, dgBus.decode_msg(message), index=0)

    def stop(self):
        self.beaconref().CMD_SCHED_KILL_TX(self.channel, self.idIn)
