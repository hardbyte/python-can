from pycanlib import canlib, canstat, InputValidation

import cPickle
import ctypes
import datetime
import os
import platform
import Queue
import sys
import time
import types

try:
    import hgversionutils
    __version__ = hgversionutils.get_version_number(os.path.join(os.path.dirname(__file__), ".."))
except ImportError:
    with open(os.path.join(os.path.dirname(__file__), "version.txt"), "r") as _version_file:
        __version__ = _version_file.readline().replace("\n", "")

canlib.canInitializeLibrary()

ID_TYPE_EXTENDED = True
ID_TYPE_STANDARD = False

ID_TYPE_29_BIT = ID_TYPE_EXTENDED
ID_TYPE_11_BIT = ID_TYPE_STANDARD

REMOTE_FRAME = True
DATA_FRAME = False

WAKEUP_MSG = True

ERROR_FRAME = True

MAX_DEVICE_DESCR_LENGTH = 256
MAX_MANUFACTURER_NAME_LENGTH = 256
MAX_FW_VERSION_LENGTH = 8
FW_VERSION_ARRAY = ctypes.c_ubyte * MAX_FW_VERSION_LENGTH
MAX_HW_VERSION_LENGTH = 8
HW_VERSION_ARRAY = ctypes.c_ubyte * MAX_HW_VERSION_LENGTH
MAX_CARD_SN_LENGTH = 8
CARD_SN_ARRAY = ctypes.c_ubyte * MAX_CARD_SN_LENGTH
MAX_TRANS_SN_LENGTH = 8
TRANS_SN_ARRAY = ctypes.c_ubyte * MAX_TRANS_SN_LENGTH

LOG_FORMAT_DAT = 0
LOG_FORMAT_TDV = 1

class Message(object):

    def __init__(self, timestamp=0.0, is_remote_frame=False, id_type=ID_TYPE_11_BIT, is_wakeup=(not WAKEUP_MSG), is_error_frame=(not ERROR_FRAME), arbitration_id=0, data=[], dlc=0, info_strings=[]):
        self.timestamp = timestamp
        self.id_type = id_type
        self.is_remote_frame = is_remote_frame
        self.is_wakeup = is_wakeup
        self.is_error_frame = is_error_frame
        self.arbitration_id = arbitration_id
        self.data = data
        self.dlc = dlc
        self.info_strings = info_strings

    @property
    def timestamp(self):
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, value):
        InputValidation.verify_parameter_type("CAN.Message.timestamp.setter", "timestamp", value, types.FloatType)
        InputValidation.verify_parameter_min_value("CAN.Message.timestamp.setter", "timestamp", value, 0)
        self.__timestamp = value

    @property
    def is_remote_frame(self):
        if self.flags & canstat.canMSG_RTR:
            return REMOTE_FRAME
        else:
            return not REMOTE_FRAME

    @is_remote_frame.setter
    def is_remote_frame(self, value):
        InputValidation.verify_parameter_type("CAN.Message.is_remote_frame.setter", "is_remote_frame", value, types.BooleanType)
        self.flags &= (0xFFFF - canstat.canMSG_RTR)
        self.flags |= (value * canstat.canMSG_RTR)

    @property
    def id_type(self):
        if self.flags & canstat.canMSG_EXT:
            return ID_TYPE_EXTENDED
        elif self.flags & canstat.canMSG_STD:
            return ID_TYPE_STANDARD

    @id_type.setter
    def id_type(self, value):
        InputValidation.verify_parameter_type("CAN.Message.id_type.setter", "id_type", value, types.BooleanType)
        if (self.flags & (0xFFFF - (canstat.canMSG_STD | canstat.canMSG_EXT))) != 0:
            self.flags &= (0xFFFF - (canstat.canMSG_STD | canstat.canMSG_EXT))
        if value == ID_TYPE_EXTENDED:
            self.flags |= canstat.canMSG_EXT
        else:
            self.flags |= canstat.canMSG_STD

    @property
    def is_wakeup(self):
        if self.flags & canstat.canMSG_WAKEUP:
            return WAKEUP_MSG
        else:
            return not WAKEUP_MSG

    @is_wakeup.setter
    def is_wakeup(self, value):
        InputValidation.verify_parameter_type("CAN.Message.is_wakeup.setter", "is_wakeup", value, types.BooleanType)
        self.flags &= (0xFFFF - canstat.canMSG_WAKEUP)
        if value == WAKEUP_MSG:
            self.flags |= canstat.canMSG_WAKEUP

    @property
    def is_error_frame(self):
        if self.flags & canstat.canMSG_ERROR_FRAME:
            return ERROR_FRAME
        else:
            return not ERROR_FRAME

    @is_error_frame.setter
    def is_error_frame(self, value):
        InputValidation.verify_parameter_type("CAN.Message.is_error_frame.setter", "is_error_frame", value, types.BooleanType)
        self.flags &= (0xFFFF - canstat.canMSG_ERROR_FRAME)
        if value == ERROR_FRAME:
            self.flags |= canstat.canMSG_ERROR_FRAME

    @property
    def arbitration_id(self):
        return self.__arbitration_id

    @arbitration_id.setter
    def arbitration_id(self, value):
        InputValidation.verify_parameter_type("CAN.Message.arbitration_id.setter", "arbitration_id", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.Message.arbitration_id.setter", "arbitration_id", value, 0)
        if self.id_type == ID_TYPE_EXTENDED:
            InputValidation.verify_parameter_max_value("CAN.Message.arbitration_id.setter", "arbitration_id", value, ((2 ** 29) - 1))
        else:
            InputValidation.verify_parameter_max_value("CAN.Message.arbitration_id.setter", "arbitration_id", value, ((2 ** 11) - 1))
        self.__arbitration_id = value

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        InputValidation.verify_parameter_type("CAN.Message.data.setter", "data", value, types.ListType)
        for (_index, _item) in enumerate(value):
            InputValidation.verify_parameter_type("CAN.Message.data.setter", ("data[%d]" % _index), _item, types.IntType)
            InputValidation.verify_parameter_min_value("CAN.Message.data.setter", ("data[%d]" % _index), _item, 0)
            InputValidation.verify_parameter_max_value("CAN.Message.data.setter", ("data[%d]" % _index), _item, 255)
        self.__data = value

    @property
    def dlc(self):
        return self.__dlc

    @dlc.setter
    def dlc(self, value):
        InputValidation.verify_parameter_type("CAN.Message.dlc.setter", "dlc", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.Message.dlc.setter", "dlc", value, 0)
        InputValidation.verify_parameter_max_value("CAN.Message.dlc.setter", "dlc", value, 8)
        self.__dlc = value

    @property
    def flags(self):
        try:
            return self.__flags
        except AttributeError:
            return 0

    @flags.setter
    def flags(self, value):
        InputValidation.verify_parameter_type("CAN.Message.flags.setter", "flags", value, types.IntType)
#        InputValidation.verify_parameter_value_equal_to("CAN.Message.flags.setter", "(flags & (0xFFFF - canstat.canMSG_MASK))", (value & (0xFFFF - canstat.canMSG_MASK)), 0)
#        InputValidation.verify_parameter_value_in_set("CAN.Message.flags.setter", "(flags & (canstat.canMSG_EXT + canstat.canMSG_STD))", (value & (canstat.canMSG_EXT + canstat.canMSG_STD)), (canstat.canMSG_EXT, canstat.canMSG_STD))
        self.__flags = value

    @property
    def info_strings(self):
        return self.__info_strings

    @info_strings.setter
    def info_strings(self, value):
        InputValidation.verify_parameter_type("CAN.Message.info_strings.setter", "info_strings", value, types.ListType)
        for (_index, _string) in enumerate(value):
            InputValidation.verify_parameter_type("CAN.Message.info_strings.setter", "info_strings[%d]" % _index, _string, types.StringType)
        self.__info_strings = value

    def check_equality(self, other, fields):
        InputValidation.verify_parameter_type("CAN.Message.check_equality", "other", other, Message)
        InputValidation.verify_parameter_type("CAN.Message.check_equality", "fields", fields, types.ListType)
        for (_index, _field) in enumerate(fields):
            InputValidation.verify_parameter_type("CAN.Message.check_equality", ("fields[%d]" % _index), _field, types.StringType)
        retval = True
        for _field in fields:
            try:
                if eval("self.%s" % _field) != eval("other.%s" % _field):
                    retval = False
                    break
            except AttributeError:
                retval = False
                break
        return retval

    def __str__(self):
        _field_strings = []
        _field_strings.append("%15.6f" % self.timestamp)
        if self.flags & canstat.canMSG_EXT:
            _field_strings.append("%.8x" % self.arbitration_id)
        else:
            _field_strings.append("    %.4x" % self.arbitration_id)
        _field_strings.append("%.4x" % self.flags)
        _field_strings.append("%d" % self.dlc)
        _data_strings = []
        if self.data != None:
            for byte in self.data:
                _data_strings.append("%.2x" % byte)
        if len(_data_strings) > 0:
            _field_strings.append(" ".join(_data_strings).ljust(24, " "))
        _current_length = len("    ".join(_field_strings))
        _field_strings.append(("\n" + (" " * (_current_length + 4))).join(self.info_strings))
        return "    ".join(_field_strings)

class MessageList(object):

    def __init__(self, messages=[], filter_criteria="True", name="default"):
        self.messages = messages
        self.filter_criteria = filter_criteria
        self.name = name

    @property
    def messages(self):
        return self.__messages

    @messages.setter
    def messages(self, value):
        InputValidation.verify_parameter_type("CAN.MessageList.messages.setter", "messages", value, types.ListType)
        for (_index, _msg) in enumerate(value):
            InputValidation.verify_parameter_type("CAN.MessageList.messages.setter", "messages[%d]" % _index, _msg, Message)
        self.__messages = value
        if len(value) > 0:
            self.__start_timestamp = value[0].timestamp
            self.__end_timestamp = value[-1].timestamp
        else:
            self.__start_timestamp = 0
            self.__end_timestamp = 0

    @property
    def filter_criteria(self):
        return self.__filter_criteria

    @filter_criteria.setter
    def filter_criteria(self, value):
        InputValidation.verify_parameter_type("CAN.MessageList.filter_criteria.setter", "filter_criteria", value, types.StringType)
        self.__filter_criteria = value

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        InputValidation.verify_parameter_type("CAN.MessageList.name.setter", "name", value, types.StringType)
        self.__name = value

    @property
    def start_timestamp(self):
        return self.__start_timestamp

    @property
    def end_timestamp(self):
        return self.__end_timestamp

    @property
    def filtered_messages(self):
        retval = []
        for msg in self.messages:
            try:
                if eval(self.filter_criteria):
                    retval.append(msg)
            except AttributeError:
                pass

    def __str__(self):
        retval = "-"*len("\nMessage List '%s'\n" % self.name)
        retval += "\nMessage List '%s'\n" % self.name
        retval += "-"*len("\nMessage List '%s'\n" % self.name)
        retval += "\n"
        if self.filter_criteria == "True":
            retval += "Applied filters: None\n"
        else:
            retval += "Applied filters: %s\n" % self.filter_criteria
        retval += "Start timestamp = %f\n" % self.start_timestamp
        retval += "End timestamp = %f\n" % self.end_timestamp
        for _msg in self.messages:
            retval += "%s\n" % _msg
        return retval

class Bus(object):

    def __init__(self, channel, speed, tseg1, tseg2, sjw, no_samp, std_acceptance_filter=(0, 0), ext_acceptance_filter=(0, 0)):
        self.channel = channel
        self.speed = speed
        self.tseg1 = tseg1
        self.tseg2 = tseg2
        self.sjw = sjw
        self.no_samp = no_samp
        self.std_acceptance_filter = std_acceptance_filter
        self.ext_acceptance_filter = ext_acceptance_filter
        self.__listeners = []
        self.__old_stat_flags = 0
        self.__ctypes_callback = canlib.callback_dict[sys.platform](self.__callback)
        canlib.canBusOn(self.__read_handle)
        canlib.canBusOn(self.__write_handle)

    @property
    def channel(self):
        return self.__channel

    @channel.setter
    def channel(self, value):
        _num_channels = ctypes.c_int(0)
        canlib.canGetNumberOfChannels(ctypes.byref(_num_channels))
        InputValidation.verify_parameter_type("CAN.Bus.channel.setter", "channel", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.Bus.channel.setter", "channel", value, 0)
        InputValidation.verify_parameter_max_value("CAN.Bus.channel.setter", "channel", value, _num_channels.value)
        if "__read_handle" in self.__dict__:
            canlib.canBusOff(self.__read_handle)
            canlib.kvSetNotifyCallback(self.__read_handle, ctypes.c_void_p(0), ctypes.c_void_p(0), 0)
            canlib.canClose(self.__read_handle)
        if "__write_handle" in self.__dict__:
            canlib.canBusOff(self.__write_handle)
            canlib.kvSetNotifyCallback(self.__write_handle, ctypes.c_void_p(0), ctypes.c_void_p(0), 0)
            canlib.canClose(self.__write_handle)
        self.__channel = value
        self.__read_handle = canlib.canOpenChannel(value, canlib.canOPEN_ACCEPT_VIRTUAL)
        self.__write_handle = canlib.canOpenChannel(value, canlib.canOPEN_ACCEPT_VIRTUAL)
        canlib.canIoCtl(self.__read_handle, canlib.canIOCTL_SET_TIMER_SCALE, ctypes.byref(ctypes.c_long(1)), 4)
        canlib.canIoCtl(self.__write_handle, canlib.canIOCTL_SET_TIMER_SCALE, ctypes.byref(ctypes.c_long(1)), 4)
        self.__update_bus_parameters()
        canlib.canBusOn(self.__read_handle)
        canlib.canBusOn(self.__write_handle)

    @property
    def speed(self):
        return self.__speed

    @speed.setter
    def speed(self, value):
        InputValidation.verify_parameter_type("CAN.Bus.speed.setter", "speed", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.Bus.speed.setter", "speed", value, 0)
        InputValidation.verify_parameter_max_value("CAN.Bus.speed.setter", "speed", value, 1000000)
        self.__speed = value
        self.__update_bus_parameters()

    @property
    def tseg1(self):
        return self.__tseg1

    @tseg1.setter
    def tseg1(self, value):
        InputValidation.verify_parameter_type("CAN.Bus.tseg1.setter", "tseg1", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.Bus.tseg1.setter", "tseg1", value, 0)
        InputValidation.verify_parameter_max_value("CAN.Bus.tseg1.setter", "tseg1", value, 255)
        self.__tseg1 = value
        self.__update_bus_parameters()

    @property
    def tseg2(self):
        return self.__tseg2

    @tseg2.setter
    def tseg2(self, value):
        InputValidation.verify_parameter_type("CAN.Bus.tseg2.setter", "tseg2", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.Bus.tseg2.setter", "tseg2", value, 0)
        InputValidation.verify_parameter_max_value("CAN.Bus.tseg2.setter", "tseg2", value, 255)
        self.__tseg2 = value
        self.__update_bus_parameters()

    @property
    def sjw(self):
        return self.__sjw

    @sjw.setter
    def sjw(self, value):
        InputValidation.verify_parameter_type("CAN.Bus.sjw.setter", "sjw", value, types.IntType)
        InputValidation.verify_parameter_value_in_set("CAN.Bus.sjw.setter", "sjw", value, [1, 2, 3, 4])
        self.__sjw = value
        self.__update_bus_parameters()

    @property
    def no_samp(self):
        return self.__no_samp

    @no_samp.setter
    def no_samp(self, value):
        InputValidation.verify_parameter_type("CAN.Bus.no_samp.setter", "no_samp", value, types.IntType)
        InputValidation.verify_parameter_value_in_set("CAN.Bus.no_samp.setter", "no_samp", value, [1, 3])
        self.__no_samp = value
        self.__update_bus_parameters()

    @property
    def std_acceptance_filter(self):
        return (self.__std_acceptance_code, self.__std_acceptance_mask)

    @std_acceptance_filter.setter
    def std_acceptance_filter(self, value):
        InputValidation.verify_parameter_type("CAN.Bus.std_acceptance_filter.setter", "std_acceptance_filter", value, types.TupleType)
        InputValidation.verify_parameter_value_equal_to("CAN.Bus.std_acceptance_filter.setter", "len(std_acceptance_filter)", len(value), 2)
        InputValidation.verify_parameter_type("CAN.Bus.std_acceptance_filter.setter", "std_acceptance_code", value[0], types.IntType)
        InputValidation.verify_parameter_type("CAN.Bus.std_acceptance_filter.setter", "std_acceptance_mask", value[1], types.IntType)
        InputValidation.verify_parameter_min_value("CAN.Bus.std_acceptance_filter.setter", "std_acceptance_code", value[0], 0)
        InputValidation.verify_parameter_min_value("CAN.Bus.std_acceptance_filter.setter", "std_acceptance_mask", value[1], 0)
        InputValidation.verify_parameter_max_value("CAN.Bus.std_acceptance_filter.setter", "std_acceptance_code", value[0], ((2 ** 11) - 1))
        InputValidation.verify_parameter_max_value("CAN.Bus.std_acceptance_filter.setter", "std_acceptance_mask", value[1], ((2 ** 11) - 1))
        self.__set_acceptance_filter(value, canlib.ACCEPTANCE_FILTER_TYPE_STD)

    @property
    def ext_acceptance_filter(self):
        return (self.__ext_acceptance_code, self.__ext_acceptance_mask)

    @ext_acceptance_filter.setter
    def ext_acceptance_filter(self, value):
        InputValidation.verify_parameter_type("CAN.Bus.ext_acceptance_filter.setter", "ext_acceptance_filter", value, types.TupleType)
        InputValidation.verify_parameter_value_equal_to("CAN.Bus.ext_acceptance_filter.setter", "len(ext_acceptance_filter)", len(value), 2)
        InputValidation.verify_parameter_type("CAN.Bus.ext_acceptance_filter.setter", "ext_acceptance_code", value[0], types.IntType)
        InputValidation.verify_parameter_type("CAN.Bus.ext_acceptance_filter.setter", "ext_acceptance_mask", value[1], types.IntType)
        InputValidation.verify_parameter_min_value("CAN.Bus.ext_acceptance_filter.setter", "ext_acceptance_code", value[0], 0)
        InputValidation.verify_parameter_min_value("CAN.Bus.ext_acceptance_filter.setter", "ext_acceptance_mask", value[1], 0)
        InputValidation.verify_parameter_max_value("CAN.Bus.ext_acceptance_filter.setter", "ext_acceptance_code", value[0], ((2 ** 29) - 1))
        InputValidation.verify_parameter_max_value("CAN.Bus.ext_acceptance_filter.setter", "ext_acceptance_mask", value[1], ((2 ** 29) - 1))
        self.__set_acceptance_filter(value, canlib.ACCEPTANCE_FILTER_TYPE_EXT)

    @property
    def bus_time(self):
        return (canlib.canReadTimer(self.__read_handle) / 1000000.0)

    @property
    def bus_load(self):
        return (self.__get_bus_statistics().bus_load / 100.0)

    @property
    def frame_counts(self):
        _stats = self.__get_bus_statistics()
        retval = {}
        retval["std data"] = _stats.std_data
        retval["std remote"] = _stats.std_remote
        retval["ext data"] = _stats.ext_data
        retval["ext remote"] = _stats.ext_remote
        retval["error"] = _stats.error_frames
        return retval

    @property
    def buffer_overruns(self):
        return self.__get_bus_statistics().overruns

    @property
    def device_description(self):
        _buffer = ctypes.create_string_buffer(MAX_DEVICE_DESCR_LENGTH)
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_DEVDESCR_ASCII, ctypes.byref(_buffer), ctypes.c_size_t(MAX_DEVICE_DESCR_LENGTH))
        return _buffer.value

    @property
    def manufacturer_name(self):
        _buffer = ctypes.create_string_buffer(MAX_MANUFACTURER_NAME_LENGTH)
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_MFGNAME_ASCII, ctypes.byref(_buffer), ctypes.c_size_t(MAX_MANUFACTURER_NAME_LENGTH))
        return _buffer.value

    @property
    def firmware_version(self):
        _buffer = FW_VERSION_ARRAY()
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_CARD_FIRMWARE_REV, ctypes.byref(_buffer), ctypes.c_size_t(MAX_FW_VERSION_LENGTH))
        _version_number = []
        for i in [6, 4, 0, 2]:
            _version_number.append((_buffer[i + 1] << 8) + _buffer[i])
        return "%d.%d.%d.%d" % (_version_number[0], _version_number[1], _version_number[2], _version_number[3])

    @property
    def hardware_version(self):
        _buffer = HW_VERSION_ARRAY()
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_CARD_HARDWARE_REV, ctypes.byref(_buffer), ctypes.c_size_t(MAX_HW_VERSION_LENGTH))
        _version_number = []
        for i in [2, 0]:
            _version_number.append((_buffer[i + 1] << 8) + _buffer[i])
        return "%d.%d" % (_version_number[0], _version_number[1])

    @property
    def card_serial(self):
        _buffer = CARD_SN_ARRAY()
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_CARD_SERIAL_NO, ctypes.byref(_buffer), ctypes.c_size_t(MAX_CARD_SN_LENGTH))
        _serial_number = 0
        for i in xrange(len(_buffer)):
            _serial_number += (_buffer[i] << (8 * i))
        return _serial_number

    @property
    def transceiver_serial(self):
        _buffer = TRANS_SN_ARRAY()
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_TRANS_SERIAL_NO, ctypes.byref(_buffer), ctypes.c_size_t(MAX_TRANS_SN_LENGTH))
        serial_number = 0
        for i in xrange(len(_buffer)):
            serial_number += (_buffer[i] << (8 * i))
        return serial_number

    @property
    def card_number(self):
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_CARD_NUMBER, ctypes.byref(_buffer), ctypes.c_size_t(4))
        return _buffer.value

    @property
    def card_channel(self):
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_CHAN_NO_ON_CARD, ctypes.byref(_buffer), ctypes.c_size_t(4))
        return _buffer.value

    @property
    def transceiver_type(self):
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel, canlib.canCHANNELDATA_TRANS_TYPE, ctypes.byref(_buffer), ctypes.c_size_t(4))
        return _buffer.value

    @property
    def channel_info(self):
        return ChannelInfo(channel=self.channel, name=self.device_description, manufacturer=self.manufacturer_name, fw_version=self.firmware_version, hw_version=self.hardware_version, card_serial=self.card_serial, trans_serial=self.transceiver_serial, trans_type=self.transceiver_type, card_number=self.card_number, channel_on_card=self.card_channel)

    def write(self, msg):
        InputValidation.verify_parameter_type("CAN.Bus.write", "msg", msg, Message)
        canlib.canWrite(self.__write_handle, msg.arbitration_id, "".join([("%c" % byte) for byte in msg.data]), msg.dlc, msg.flags)

    def clear_queues(self):
        canlib.canFlushReceiveQueue(self.__read_handle)
        canlib.canFlushTransmitQueue(self.__write_handle)

    def add_listener(self, listener):
        InputValidation.verify_parameter_type("CAN.Bus.add_listener", "listener", listener, Listener)
        self.__listeners.append(listener)

    def remove_listener(self, listener):
        self.__listeners.remove(listener)

    def enable_callback(self):
        canlib.kvSetNotifyCallback(self.__read_handle, self.__ctypes_callback, None, canstat.canNOTIFY_RX + canstat.canNOTIFY_STATUS)

    def disable_callback(self):
        canlib.kvSetNotifyCallback(self.__read_handle, self.__ctypes_callback, None, canstat.canNOTIFY_NONE)

    def shutdown(self):
        self.disable_callback()
        canlib.canBusOff(self.__read_handle)
        canlib.canBusOff(self.__write_handle)
        time.sleep(0.05)
        canlib.canClose(self.__read_handle)
        canlib.canClose(self.__write_handle)

    def __get_bus_statistics(self):
        canlib.canRequestBusStatistics(self.__read_handle)
        _stats = canlib.c_canBusStatistics()
        canlib.canGetBusStatistics(self.__read_handle, ctypes.byref(_stats), ctypes.c_uint(28))
        return _stats

    def __set_acceptance_filter(self, value, msg_type):
        InputValidation.verify_parameter_value_in_set("CAN.Bus.__set_acceptance_filter", "msg_type", msg_type, [canlib.ACCEPTANCE_FILTER_TYPE_STD, canlib.ACCEPTANCE_FILTER_TYPE_EXT])
        if msg_type == canlib.ACCEPTANCE_FILTER_TYPE_STD:
            self.__std_acceptance_code = value[0]
            self.__std_acceptance_mask = value[1]
            canlib.canSetAcceptanceFilter(self.__read_handle, self.std_acceptance_filter[0], self.std_acceptance_filter[1], msg_type)
            canlib.canSetAcceptanceFilter(self.__write_handle, self.std_acceptance_filter[0], self.std_acceptance_filter[1], msg_type)
        else:
            self.__ext_acceptance_code = value[0]
            self.__ext_acceptance_mask = value[1]
            canlib.canSetAcceptanceFilter(self.__read_handle, self.ext_acceptance_filter[0], self.ext_acceptance_filter[1], msg_type)
            canlib.canSetAcceptanceFilter(self.__write_handle, self.ext_acceptance_filter[0], self.ext_acceptance_filter[1], msg_type)

    def __update_bus_parameters(self):
        try:
            canlib.canBusOff(self.__read_handle)
            canlib.canBusOff(self.__write_handle)
            canlib.canSetBusParams(self.__read_handle, self.speed, self.tseg1, self.tseg2, self.sjw, self.no_samp, 0)
            canlib.canSetBusParams(self.__write_handle, self.speed, self.tseg1, self.tseg2, self.sjw, self.no_samp, 0)
            canlib.canBusOn(self.__read_handle)
            canlib.canBusOn(self.__write_handle)
        except AttributeError:
            pass

    def __rx_callback(self):
        while True:
            _rx_msg = self.__get_message()
            if _rx_msg is None:
                break
            else:
                for _listener in self.__listeners:
                    _listener.on_message_received(_rx_msg)

    def __get_message(self):
        _arb_id = ctypes.c_long(0)
        _data = ctypes.create_string_buffer(8)
        _dlc = ctypes.c_uint(0)
        _flags = ctypes.c_uint(0)
        _timestamp = ctypes.c_long(0)
        _status = canlib.canRead(self.__read_handle, ctypes.byref(_arb_id), ctypes.byref(_data), ctypes.byref(_dlc), ctypes.byref(_flags), ctypes.byref(_timestamp))
        if _status.value == canstat.canOK:
            _data_array = map(ord, _data)
            if int(_flags.value) & canstat.canMSG_EXT:
                _id_type = ID_TYPE_EXTENDED
            else:
                _id_type = ID_TYPE_STANDARD
            _rx_msg = Message(arbitration_id=_arb_id.value, data=_data_array[:_dlc.value], dlc=int(_dlc.value), id_type=_id_type, timestamp = (float(_timestamp.value) / 1000000))
            _rx_msg.flags = int(_flags.value) & canstat.canMSG_MASK
            return _rx_msg
        else:
            return None

    def __status_callback(self, timestamp):
        canlib.canRequestChipStatus(self.__read_handle)
        _stat_flags = ctypes.c_long(0)
        canlib.canReadStatus(self.__read_handle, ctypes.byref(_stat_flags))
        if _stat_flags.value != self.__old_stat_flags:
            for _listener in self.__listeners:
                _listener.on_status_change(timestamp, _stat_flags.value, self.__old_stat_flags)
            self.__old_stat_flags = _stat_flags.value

    def __callback(self, hnd, context, event):
        if event == canstat.canNOTIFY_RX:
            self.__rx_callback()
        elif event == canstat.canNOTIFY_STATUS:
            _timestamp = canlib.canReadTimer(self.__read_handle)
            self.__status_callback(_timestamp)
        return 0

class Listener(object):

    def on_message_received(self, msg):
        raise NotImplementedError("%s has not implemented on_message_received" % self.__class__.__name__)

    def on_status_change(self, timestamp, new_status, old_status):
        raise NotImplementedError("%s has not implemented on_status_change" % self.__class__.__name__)

class BufferedReader(Listener):
    def __init__(self):
        self.__msg_queue = Queue.Queue(0)

    def on_message_received(self, msg):
        self.__msg_queue.put_nowait(msg)

    def on_status_change(self, timestamp, old_status, new_status):
        pass

    def get_message(self, timeout=1):
        try:
            return self.__msg_queue.get(timeout=timeout)
        except Queue.Empty:
            return None

class SoftwareAcceptanceFilter(Listener):
    def __init__(self, std_acceptance_code=0, std_acceptance_mask=0, ext_acceptance_code=0, ext_acceptance_mask=0):
        self.std_acceptance_code = std_acceptance_code
        self.std_acceptance_mask = std_acceptance_mask
        self.ext_acceptance_code = ext_acceptance_code
        self.ext_acceptance_mask = ext_acceptance_mask
        self.__listeners = []

    @property
    def std_acceptance_code(self):
        return self.__std_acceptance_code

    @std_acceptance_code.setter
    def std_acceptance_code(self, value):
        InputValidation.verify_parameter_type("CAN.SoftwareAcceptanceFilter.std_acceptance_code.setter", "std_acceptance_code", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.SoftwareAcceptanceFilter.std_acceptance_code.setter", "std_acceptance_code", value, 0)
        InputValidation.verify_parameter_max_value("CAN.SoftwareAcceptanceFilter.std_acceptance_code.setter", "std_acceptance_code", value, ((2 ** 11) - 1))
        self.__std_acceptance_code = value

    @property
    def std_acceptance_mask(self):
        return self.__std_acceptance_mask

    @std_acceptance_mask.setter
    def std_acceptance_mask(self, value):
        InputValidation.verify_parameter_type("CAN.SoftwareAcceptanceFilter.std_acceptance_mask.setter", "std_acceptance_mask", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.SoftwareAcceptanceFilter.std_acceptance_mask.setter", "std_acceptance_mask", value, 0)
        InputValidation.verify_parameter_max_value("CAN.SoftwareAcceptanceFilter.std_acceptance_mask.setter", "std_acceptance_mask", value, ((2 ** 11) - 1))
        self.__std_acceptance_mask = value

    @property
    def ext_acceptance_code(self):
        return self.__ext_acceptance_code

    @ext_acceptance_code.setter
    def ext_acceptance_code(self, value):
        InputValidation.verify_parameter_type("CAN.SoftwareAcceptanceFilter.ext_acceptance_code.setter", "ext_acceptance_code", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.SoftwareAcceptanceFilter.ext_acceptance_code.setter", "ext_acceptance_code", value, 0)
        InputValidation.verify_parameter_max_value("CAN.SoftwareAcceptanceFilter.ext_acceptance_code.setter", "ext_acceptance_code", value, ((2 ** 29) - 1))
        self.__ext_acceptance_code = value

    @property
    def ext_acceptance_mask(self):
        return self.__ext_acceptance_mask

    @ext_acceptance_mask.setter
    def ext_acceptance_mask(self, value):
        InputValidation.verify_parameter_type("CAN.SoftwareAcceptanceFilter.ext_acceptance_mask.setter", "ext_acceptance_mask", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.SoftwareAcceptanceFilter.ext_acceptance_mask.setter", "ext_acceptance_mask", value, 0)
        InputValidation.verify_parameter_max_value("CAN.SoftwareAcceptanceFilter.ext_acceptance_mask.setter", "ext_acceptance_mask", value, ((2 ** 29) - 1))
        self.__ext_acceptance_mask = value

    def on_message_received(self, msg):
        _msg = self.filter_message(msg)
        if _msg != None:
            for _listener in self.__listeners:
                _listener.on_message_received(msg)

    def add_listener(self, listener):
        InputValidation.verify_parameter_type("CAN.SoftwareAcceptanceFilter.add_listener", "listener", listener, Listener)
        self.__listeners.append(listener)

    def remove_listener(self, listener):
        self.__listeners.remove(listener)

    def filter_message(self, msg):
        if msg.id_type == ID_TYPE_EXTENDED:
            _mask = self.ext_acceptance_mask
            _code = self.ext_acceptance_code
        else:
            _mask = self.std_acceptance_mask
            _code = self.std_acceptance_code
        if not ((msg.arbitration_id & _mask) ^ _code):
            return msg
        else:
            return None

class ChannelInfo(object):

    def __init__(self, channel=0, name="", manufacturer="", fw_version="", hw_version="", card_serial=0, trans_serial=0, trans_type="", card_number=0, channel_on_card=0):
        self.channel = channel
        self.name = name
        self.manufacturer = manufacturer
        self.fw_version = fw_version
        self.hw_version = hw_version
        self.card_serial = card_serial
        self.trans_serial = trans_serial
        self.trans_type = trans_type
        self.card_number = card_number
        self.channel_on_card = channel_on_card

    @property
    def channel(self):
        return self.__channel

    @channel.setter
    def channel(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.channel.setter", "channel", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.ChannelInfo.channel.setter", "channel", value, 0)
        self.__channel = value

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.name.setter", "name", value, types.StringType)
        self.__name = value

    @property
    def manufacturer(self):
        return self.__manufacturer

    @manufacturer.setter
    def manufacturer(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.manufacturer.setter", "manufacturer", value, types.StringType)
        self.__manufacturer = value

    @property
    def fw_version(self):
        return self.__fw_version

    @fw_version.setter
    def fw_version(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.fw_version.setter", "fw_version", value, types.StringType)
        self.__fw_version = value

    @property
    def hw_version(self):
        return self.__hw_version

    @hw_version.setter
    def hw_version(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.hw_version.setter", "hw_version", value, types.StringType)
        self.__hw_version = value

    @property
    def card_serial(self):
        return self.__card_serial

    @card_serial.setter
    def card_serial(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.card_serial.setter", "card_serial", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.ChannelInfo.card_serial.setter", "card_serial", value, 0)
        self.__card_serial = value

    @property
    def trans_serial(self):
        return self.__trans_serial

    @trans_serial.setter
    def trans_serial(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.trans_serial.setter", "trans_serial", value, types.IntType)
        InputValidation.verify_parameter_min_value("CAN.ChannelInfo.trans_serial.setter", "trans_serial", value, 0)
        self.__trans_serial = value

    @property
    def trans_type(self):
        return canstat.canTransceiverTypeStrings[self.__trans_type]

    @trans_type.setter
    def trans_type(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.trans_type.setter", "trans_type", value, types.LongType)
        InputValidation.verify_parameter_value_in_set("CAN.ChannelInfo.trans_type.setter", "trans_type", value, canstat.canTransceiverTypeStrings.keys())
        self.__trans_type = value

    @property
    def card_number(self):
        return self.__card_number

    @card_number.setter
    def card_number(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.card_number.setter", "card_number", value, types.LongType)
        InputValidation.verify_parameter_min_value("CAN.ChannelInfo.card_number.setter", "card_number", value, 0)
        self.__card_number = value

    @property
    def channel_on_card(self):
        return self.__channel_on_card

    @channel_on_card.setter
    def channel_on_card(self, value):
        InputValidation.verify_parameter_type("CAN.ChannelInfo.channel_on_card.setter", "channel_on_card", value, types.LongType)
        InputValidation.verify_parameter_min_value("CAN.ChannelInfo.channel_on_card.setter", "channel_on_card", value, 0)
        self.__channel_on_card = value

    def __str__(self):
        retval = "-"*len("Channel Info")
        retval += "\nChannel Info\n"
        retval += "-"*len("Channel Info")
        retval += "\n"
        retval += "CANLIB channel: %s\n" % self.channel
        retval += "Name: %s\n" % self.name
        retval += "Manufacturer: %s\n" % self.manufacturer
        retval += "Firmware version: %s\n" % self.fw_version
        retval += "Hardware version: %s\n" % self.hw_version
        retval += "Card serial number: %s\n" % self.card_serial
        retval += "Transceiver type: %s\n" % self.trans_type
        retval += "Transceiver serial number: %s\n" % self.trans_serial
        retval += "Card number: %s\n" % self.card_number
        retval += "Channel on card: %s\n" % self.channel_on_card
        return retval

class LogInfo(object):

    def __init__(self, log_start_time=None, log_end_time=None, original_file_name="default.dat", test_location="default", tester_name="default"):
        self.log_start_time = log_start_time
        self.log_end_time = log_end_time
        self.original_file_name = original_file_name
        self.test_location = test_location
        self.tester_name = tester_name

    @property
    def log_start_time(self):
        return self.__log_start_time

    @log_start_time.setter
    def log_start_time(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.log_start_time.setter", "log_start_time", value, (datetime.datetime, types.NoneType))
        try:
            InputValidation.verify_parameter_max_value("CAN.LogInfo.log_start_time.setter", "log_start_time", value, self.log_end_time)
        except AttributeError:
            pass
        self.__log_start_time = value

    @property
    def log_end_time(self):
        return self.__log_end_time

    @log_end_time.setter
    def log_end_time(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.log_end_time.setter", "log_end_time", value, (datetime.datetime, types.NoneType))
        try:
            InputValidation.verify_parameter_min_value("CAN.LogInfo.log_end_time.setter", "log_end_time", value, self.log_start_time)
        except AttributeError:
            pass
        self.__log_end_time = value

    @property
    def original_file_name(self):
        return self.__original_file_name

    @original_file_name.setter
    def original_file_name(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.original_file_name.setter", "original_file_name", value, types.StringType)
        self.__original_file_name = value

    @property
    def test_location(self):
        return self.__test_location

    @test_location.setter
    def test_location(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.test_location.setter", "test_location", value, types.StringType)
        self.__test_location = value

    @property
    def tester_name(self):
        return self.__tester_name

    @tester_name.setter
    def tester_name(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.tester_name.setter", "tester_name", value, types.StringType)
        self.__tester_name = value

    def __str__(self):
        retval = "-"*len("Log Info")
        retval += "\nLog Info\n"
        retval += "-"*len("Log Info")
        retval += "\n"
        retval += "Start time: %s\n" % self.log_start_time
        retval += "End time: %s\n" % self.log_end_time
        retval += "Original DAT file name: %s\n" % self.original_file_name
        retval += "Test Location: %s\n" % self.test_location
        retval += "Tester name: %s\n" % self.tester_name
        return retval

class MachineInfo(object):

    def __init__(self, machine_name="", python_version="", platform_info=""):
        self.machine_name = machine_name
        self.python_version = python_version
        self.platform_info = platform_info
        self.canlib_version = get_canlib_info()
        self.module_versions = {}
        for (_modname, _mod) in sys.modules.items():
            if _mod != None:
                if "__version__" in _mod.__dict__.keys():
                    self.module_versions[_modname] = _mod.__version__

    @property
    def machine_name(self):
        return self.__machine_name

    @machine_name.setter
    def machine_name(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.machine_name.setter", "machine_name", value, types.StringType)
        self.__machine_name = value

    @property
    def python_version(self):
        return self.__python_version

    @python_version.setter
    def python_version(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.python_version.setter", "python_version", value, types.StringType)
        self.__python_version = value

    @property
    def platform_info(self):
        return self.__platform_info

    @platform_info.setter
    def platform_info(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.platform_info.setter", "platform_info", value, types.StringType)
        self.__platform_info = value

    @property
    def canlib_version(self):
        return self.__canlib_version

    @canlib_version.setter
    def canlib_version(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.canlib_version.setter", "canlib_version", value, types.StringType)
        self.__canlib_version = value

    @property
    def module_versions(self):
        return self.__module_versions

    @module_versions.setter
    def module_versions(self, value):
        InputValidation.verify_parameter_type("CAN.LogInfo.module_versions.setter", "module_versions", value, types.DictType)
        self.__module_versions = value

    def __str__(self):
        retval = "-" * len("Machine Info")
        retval += "\nMachine Info\n"
        retval += "-" * len("Machine Info")
        retval += "\n"
        retval += "Machine name: %s\n" % self.machine_name
        retval += "Python: %s\n" % self.python_version
        retval += "OS: %s\n" % self.platform_info
        retval += "CANLIB: %s\n" % self.canlib_version
        retval += "Loaded Python module versions:\n"
        for _mod in sorted(self.module_versions.keys()):
            retval += "\t%s: %s\n" % (_mod, self.module_versions[_mod])
        return retval

def get_host_machine_info():
    if sys.platform == "win32":
        _machine_name = os.getenv("COMPUTERNAME")
    else:
        _machine_name = os.getenv("HOSTNAME")
    _platform_info = platform.platform()
    _python_version = sys.version[:sys.version.index(" ")]
    return MachineInfo(machine_name=_machine_name, python_version=_python_version, platform_info=_platform_info)

def get_canlib_info():
    _canlib_prod_ver_32 = canlib.canGetVersionEx(canlib.canVERSION_CANLIB32_PRODVER32)
    _major_ver_no = (_canlib_prod_ver_32 & 0x00FF0000) >> 16
    _minor_ver_no = (_canlib_prod_ver_32 & 0x0000FF00) >> 8
    if (_canlib_prod_ver_32 & 0x000000FF) != 0:
        _minor_ver_letter = "%c" % (_canlib_prod_ver_32 & 0x000000FF)
    else:
        _minor_ver_letter = ""
    return "%d.%d%s" % (_major_ver_no, _minor_ver_no, _minor_ver_letter)

class Log(object):

    def __init__(self, log_info, channel_info, machine_info, message_lists=[]):
        self.log_info = log_info
        self.channel_info = channel_info
        self.machine_info = machine_info
        self.message_lists = message_lists

    @property
    def log_info(self):
        return self.__log_info

    @log_info.setter
    def log_info(self, value):
        InputValidation.verify_parameter_type("CAN.Log.log_info.setter", "log_info", value, LogInfo)
        self.__log_info = value

    @property
    def channel_info(self):
        return self.__channel_info

    @channel_info.setter
    def channel_info(self, value):
        InputValidation.verify_parameter_type("CAN.Log.channel_info.setter", "channel_info", value, (ChannelInfo, types.NoneType))
        self.__channel_info = value

    @property
    def machine_info(self):
        return self.__machine_info

    @machine_info.setter
    def machine_info(self, value):
        InputValidation.verify_parameter_type("CAN.Log.machine_info.setter", "machine_info", value, MachineInfo)
        self.__machine_info = value

    @property
    def message_lists(self):
        return self.__message_lists

    @message_lists.setter
    def message_lists(self, value):
        InputValidation.verify_parameter_type("CAN.Log.message_lists.setter", "message_lists", value, types.ListType)
        for (_index, _value) in enumerate(value):
            InputValidation.verify_parameter_type("CAN.Log.message_lists.setter", ("message_lists[%d]" % _index), _value, MessageList)
        self. __message_lists = value

    def __str__(self):
        retval = ""
        retval += "%s\n" % self.machine_info
        retval += "%s\n" % self.log_info
        if self.channel_info != None:
            retval += "%s\n" % self.channel_info
        for _list in self.message_lists:
            retval += "%s" % _list
        return retval

    def write_to_file(self, format=LOG_FORMAT_DAT, name=None, path=None):
        InputValidation.verify_parameter_value_in_set("CAN.Log.write_to_file", "format", format, (LOG_FORMAT_DAT, LOG_FORMAT_TDV))
        InputValidation.verify_parameter_type("CAN.Log.write_to_file", "name", name, (types.NoneType, types.StringType))
        InputValidation.verify_parameter_type("CAN.Log.write_to_file", "path", path, (types.NoneType, types.StringType))
        if name != None:
            InputValidation.verify_parameter_min_value("CAN.Log.write_to_file", "len(name)", len(name), 1)
        if path != None:
            InputValidation.verify_parameter_min_value("CAN.Log.write_to_file", "len(path)", len(path), 1)
        if name == None:
            _name = self.log_info.original_file_name
        else:
            _name = name
        if path == None:
            _path = os.path.expanduser("~/CAN_bus_logs/")
        else:
            _path = path
        _path = os.path.join(_path, _name)
        if not os.path.exists(os.path.dirname(_path)):
            os.makedirs(os.path.dirname(_path))
        if format == LOG_FORMAT_DAT:
            with open(_path, "wb") as _log_file:
                cPickle.dump(self, _log_file)
        else:
            with open(_path, "w") as _log_file:
                _log_file.write("%s\n" % self)
