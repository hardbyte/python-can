from pycanlib import canlib, canstat

import ctypes
import datetime
import os
import Queue
import sys
import time
import types

try:
    VERSION_NUMBER_FILE = open(os.path.join(os.path.dirname(__file__),
                              "version.txt"), "r")
    __version__ = VERSION_NUMBER_FILE.readline()
    VERSION_NUMBER_FILE.close()
except IOError:
    __version__ = "UNKNOWN"

canlib.canInitializeLibrary()

ID_TYPE_EXT = True
ID_TYPE_STD = False

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

class Message(object):

    def __init__(self, timestamp=0.0, is_remote_frame=False, id_type=ID_TYPE_STD,
      is_wakeup=False, is_err_frame=False, arb_id=0, data=[], dlc=0):
        self.timestamp = timestamp
        self.is_remote_frame = is_remote_frame
        self.id_type = id_type
        self.is_wakeup = is_wakeup
        self.is_err_frame = is_err_frame
        self.arbitration_id = arb_id
        self.data = data
        self.dlc = dlc

    @property
    def timestamp(self):
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, value):
        if not isinstance(value, types.FloatType):
            raise TypeError("timestamp (type %s) is not of type 'float'" %
              type(value))
        elif value < 0:
            raise ValueError("timestamp (%s) < 0")
        else:
            self.__timestamp = value

    @property
    def is_remote_frame(self):
        try:
            return self.flags & canstat.canMSG_RTR
        except AttributeError:
            return DATA_FRAME

    @is_remote_frame.setter
    def is_remote_frame(self, value):
        if value not in (REMOTE_FRAME, DATA_FRAME):
            raise ValueError("is_remote_frame not in %s" % ((REMOTE_FRAME, DATA_FRAME),))
        self.flags &= (0xFFFF - canstat.canMSG_RTR)
        self.flags |= (value * canstat.canMSG_RTR)
        
    @property
    def id_type(self):
        try:
            if self.flags & canstat.canMSG_EXT:
                return ID_TYPE_EXT
            elif self.flags & canstat.canMSG_STD:
                return ID_TYPE_STD
        except AttributeError:
            return ID_TYPE_STD

    @id_type.setter
    def id_type(self, value):
        if value not in (ID_TYPE_EXT, ID_TYPE_STD):
            raise ValueError("id_type not in %s" % ((ID_TYPE_EXT, ID_TYPE_STD),))
        self.flags &= (0xFFFF - (canstat.canMSG_STD | canstat.canMSG_EXT))
        if value == ID_TYPE_EXT:
            self.flags |= canstat.canMSG_EXT
        else:
            self.flags |= canstat.canMSG_STD

    @property
    def is_wakeup(self):
        try:
            if self.flags & canstat.canMSG_WAKEUP:
                return WAKEUP_MSG
            else:
                return not WAKEUP_MSG
        except AttributeError:
            return not WAKEUP_MSG

    @is_wakeup.setter
    def is_wakeup(self, value):
        if value not in (WAKEUP_MSG, not WAKEUP_MSG):
            raise ValueError("is_wakeup not in %s" % ((WAKEUP_MSG, not WAKEUP_MSG),))
        self.flags &= (0xFFFF - canstat.canMSG_WAKEUP)
        if value == WAKEUP_MSG:
            self.flags |= canstat.canMSG_WAKEUP

    @property
    def is_error_frame(self):
        try:
            if self.flags & canstat.canMSG_ERROR_FRAME:
                return ERROR_FRAME
            else:
                return not ERROR_FRAME
        except AttributeError:
            return not ERROR_FRAME

    @is_error_frame.setter
    def is_error_frame(self, value):
        if value not in (ERROR_FRAME, not ERROR_FRAME):
            raise ValueError("is_wakeup not in %s" % ((ERROR_FRAME, not ERROR_FRAME),))
        self.flags &= (0xFFFF - canstat.canMSG_ERROR_FRAME)
        if value == ERROR_FRAME:
            self.flags |= canstat.canMSG_ERROR_FRAME

    @property
    def arbitration_id(self):
        return self.__arbitration_id

    @arbitration_id.setter
    def arbitration_id(self, value):
        if self.flags & canstat.canMSG_EXT:
            _max_id_value = ((2 ** 29) - 1)
        else:
            _max_id_value = ((2 ** 11) - 1)
        if not isinstance(value, (types.LongType, types.IntType)):
            _err_str = "arbitration_id (type %s) is not of type 'long'"
            _err_str += " or type 'int'"
            raise TypeError(_err_str % type(value))
        if value < 0:
            raise ValueError("arbitration_id (%s) < 0" % value)
        elif value > _max_id_value:
            _err_str = "arbitration_id (%s) > %d"
            raise ValueError(_err_str % (value, _max_id_value))
        else:
            self.__arbitration_id = value

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        if not isinstance(value, types.ListType):
            raise TypeError("data (%s) is not of type 'list'" % type(value))
        else:
            for (_index, _item) in enumerate(value):
                if not isinstance(_item, types.IntType):
                    _err_str = "data[%d] (%s) is not of type 'int'"
                    raise TypeError(_err_str % (_index, _item))
                elif _item < 0:
                    _err_str = "data[%d] (%s) < 0"
                    raise ValueError(_err_str % (_index, _item))
                elif _item > 255:
                    _err_str = "data[%d] (%s) > 255"
                    raise ValueError(_err_str % (_index, _item))
        self.__data = value

    @property
    def dlc(self):
        return self.__dlc

    @dlc.setter
    def dlc(self, value):
        if not isinstance(value, types.IntType):
            raise TypeError("dlc (%s) is not of type 'int'" % value)
        elif value < 0:
            raise ValueError("dlc (%s) < 0" % value)
        elif value > 8:
            raise ValueError("dlc (%s) > 8" % value)
        else:
            self.__dlc = value

    @property
    def flags(self):
        try:
            return self.__flags
        except AttributeError:
            return 0

    @flags.setter
    def flags(self, value):
        if not isinstance(value, types.IntType):
            raise TypeError("flags (%s) is not of type 'int'" % value)
        if (value & (0xFFFF - canstat.canMSG_MASK)) != 0:
            raise ValueError("flags (%s) must be a combination of the canMSG_* values listed in canstat.py" % value)
        if (value & canstat.canMSG_EXT) and (value & canstat.canMSG_STD):
            raise ValueError("a message can't be both standard (11-bit id) and extended (29-bit id)")
        self.__flags = value

    def __str__(self):
        _field_strings = []
        _field_strings.append("%.6f" % self.timestamp)
        if self.flags & canstat.canMSG_EXT:
            _field_strings.append("%.8x" % self.arbitration_id)
        else:
            _field_strings.append("%.4x" % self.arbitration_id)
        _field_strings.append("%.4x" % self.flags)
        _field_strings.append("%d" % self.dlc)
        _data_strings = []
        if self.data != None:
            for byte in self.data:
                _data_strings.append("%.2x" % byte)
        if len(_data_strings) > 0:
            _field_strings.append(" ".join(_data_strings))
        return "\t".join(_field_strings)


class MessageList(object):

    def __init__(self, messages=[], filter_criteria="True",
      message_type=Message, name="default"):
        self.messages = messages
        self.filter_criteria = filter_criteria
        self.message_type = message_type
        self.name = name

    @property
    def messages(self):
        return self.__messages

    @messages.setter
    def messages(self, value):
        if not isinstance(value, types.ListType):
            raise TypeError("messages is not of type 'list'")
        for (index, _msg) in enumerate(value):
            if not isinstance(_msg, self.message_type):
                raise TypeError("messages[%d] is not of type %s" % (index, self.message_type))
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
        if not isinstance(value, types.StringType):
            raise TypeError("filter_criteria is not of type 'str'")
        self.__filter_criteria = eval(value)

    @property
    def message_type(self):
        try:
            return self.__message_type
        except AttributeError:
            return Message

    @message_type.setter
    def message_type(self, value):
        if not isinstance(value, types.TypeType):
            raise TypeError("message_type is not a class")
        self.__message_type = value

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("name is not of type 'str'")
        self.__name = value

    @property
    def start_timestamp(self):
        return self.__start_timestamp

    @property
    def end_timestamp(self):
        return self.__end_timestamp

    def __str__(self):
        _header_str = "Message List '%s'"
        _header_str = _header_str % self.name
        retval = "-"*len(_header_str)
        retval += "\n%s\n" % _header_str
        retval += "-"*len(_header_str)
        retval += "\n"
        if self.filter_criteria == True:
            retval += "Applied filters: None\n"
        else:
            retval += "Applied filters: %s\n" % self.filter_criteria
        retval += "Message type: %s\n" % self.message_type
        retval += "Start timestamp = %f\n" % self.start_timestamp
        retval += "End timestamp = %f\n" % self.end_timestamp
        for _msg in self.messages:
            retval += "%s\n" % _msg
        return retval


class Bus(object):

    def __init__(self, channel, speed, tseg1, tseg2, sjw, no_samp,
      std_acceptance_filter=(0, 0), ext_acceptance_filter=(0, 0)):
        self.channel = channel
        self.speed = speed
        self.tseg1 = tseg1
        self.tseg2 = tseg2
        self.sjw = sjw
        self.no_samp = no_samp
        self.std_acceptance_filter = std_acceptance_filter
        self.ext_acceptance_filter = ext_acceptance_filter
        self.__rx_queue = Queue.Queue(0)
        self.__tx_queue = Queue.Queue(0)
        self.__listeners = []
        self.__old_stat_flags = 0
        self.__ctypes_callback = canlib.callback_dict[sys.platform](self.__callback)
        canlib.canBusOn(self.__handle)

    ############# Bus parameters (read/write) #############
    @property
    def channel(self):
        return self.__channel

    @channel.setter
    def channel(self, value):
        _num_channels = ctypes.c_int(0)
        canlib.canGetNumberOfChannels(ctypes.byref(_num_channels))
        if not isinstance(value, types.IntType):
            _err_str = "channel (%s) is not of type 'int'"
            raise TypeError(_err_str % type(value))
        elif value < 0:
            _err_str = "channel (%s) < 0"
            raise ValueError(_err_str % value)
        elif value > (_num_channels.value - 1):
            _err_str = "channel (%s) > %d"
            raise ValueError(_err_str % (value, _num_channels.value))
        else:
            if "__handle" in self.__dict__:
                canlib.canBusOff(self.__handle)
                canlib.kvSetNotifyCallback(self.__handle, ctypes.c_void_p(0),
                  ctypes.c_void_p(0), 0)
                canlib.canClose(self.__handle)
            self.__channel = value
            self.__handle = canlib.canOpenChannel(value,
              canlib.canOPEN_ACCEPT_VIRTUAL)
            canlib.canIoCtl(self.__handle, canlib.canIOCTL_SET_TIMER_SCALE, ctypes.byref(ctypes.c_long(1)), 4)
            self.__update_bus_parameters()
            canlib.canBusOn(self.__handle)

    @property
    def speed(self):
        return self.__speed

    @speed.setter
    def speed(self, value):
        if not isinstance(value, (types.IntType, types.LongType)):
            _err_str = "speed (%s) is not of type 'int' or type 'long'"
            raise TypeError(_err_str % value)
        elif value < 0:
            _err_str = "speed (%s) < 0"
            raise ValueError(_err_str % value)
        elif value > 1000000:
            _err_str = "speed (%s) > 1000000"
            raise ValueError(_err_str % value)
        else:
            self.__speed = value
            self.__update_bus_parameters()

    @property
    def tseg1(self):
        return self.__tseg1

    @tseg1.setter
    def tseg1(self, value):
        if not isinstance(value, (types.IntType)):
            _err_str = "tseg1 (%s) is not of type 'int'"
            raise TypeError(_err_str % value)
        elif value < 0:
            _err_str = "tseg1 (%s) < 0"
            raise ValueError(_err_str % value)
        elif value > 255:
            _err_str = "tseg1 (%s) > 255"
            raise ValueError(_err_str % value)
        else:
            self.__tseg1 = value
            self.__update_bus_parameters()

    @property
    def tseg2(self):
        return self.__tseg2

    @tseg2.setter
    def tseg2(self, value):
        if not isinstance(value, (types.IntType)):
            _err_str = "tseg2 (%s) is not of type 'int'"
            raise TypeError(_err_str % value)
        elif value < 0:
            _err_str = "tseg2 (%s) < 0"
            raise ValueError(_err_str % value)
        elif value > 255:
            _err_str = "tseg2 (%s) > 255"
            raise ValueError(_err_str % value)
        else:
            self.__tseg2 = value
            self.__update_bus_parameters()

    @property
    def sjw(self):
        return self.__sjw

    @sjw.setter
    def sjw(self, value):
        if not isinstance(value, types.IntType):
            _err_str = "sjw (%s) is not of type 'int'"
            raise TypeError(_err_str % value)
        elif value not in [1, 2, 3, 4]:
            _err_str = "sjw (%s) is not 1, 2, 3 or 4"
            raise ValueError(_err_str % value)
        else:
            self.__sjw = value
            self.__update_bus_parameters()

    @property
    def no_samp(self):
        return self.__no_samp

    @no_samp.setter
    def no_samp(self, value):
        if not isinstance(value, types.IntType):
            _err_str = "no_samp (%s) is not of type 'int'"
            raise TypeError(_err_str % value)
        elif value not in [1, 3]:
            _err_str = "sjw (%s) is not 1 or 3"
            raise ValueError(_err_str % value)
        else:
            self.__no_samp = value
            self.__update_bus_parameters()

    @property
    def std_acceptance_filter(self):
        return (self.__std_acceptance_code, self.__std_acceptance_mask)

    @std_acceptance_filter.setter
    def std_acceptance_filter(self, value):
        self.__set_acceptance_filter(value, canlib.ACCEPTANCE_FILTER_TYPE_STD)

    @property
    def ext_acceptance_filter(self):
        return (self.__ext_acceptance_code, self.__ext_acceptance_mask)

    @ext_acceptance_filter.setter
    def ext_acceptance_filter(self, value):
        self.__set_acceptance_filter(value, canlib.ACCEPTANCE_FILTER_TYPE_EXT)

    ############# Bus statistics (read only) ##############
    @property
    def bus_time(self):
        return (canlib.canReadTimer(self.__handle) / 1000000.0)

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

    ########### Device information (read only) ############
    @property
    def device_description(self):
        _buffer = ctypes.create_string_buffer(MAX_DEVICE_DESCR_LENGTH)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_DEVDESCR_ASCII, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_DEVICE_DESCR_LENGTH))
        return _buffer.value

    @property
    def manufacturer_name(self):
        _buffer = ctypes.create_string_buffer(MAX_MANUFACTURER_NAME_LENGTH)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_MFGNAME_ASCII, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_MANUFACTURER_NAME_LENGTH))
        return _buffer.value

    @property
    def firmware_version(self):
        _buffer = FW_VERSION_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_FIRMWARE_REV, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_FW_VERSION_LENGTH))
        _version_number = []
        for i in [6, 4, 0, 2]:
            _version_number.append((_buffer[i + 1] << 8) + _buffer[i])
        return "%d.%d.%d.%d" % (_version_number[0], _version_number[1],
          _version_number[2], _version_number[3])

    @property
    def hardware_version(self):
        _buffer = HW_VERSION_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_HARDWARE_REV, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_HW_VERSION_LENGTH))
        _version_number = []
        for i in [2, 0]:
            _version_number.append((_buffer[i + 1] << 8) + _buffer[i])
        return "%d.%d" % (_version_number[0], _version_number[1])

    @property
    def card_serial(self):
        _buffer = CARD_SN_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_SERIAL_NO, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_CARD_SN_LENGTH))
        _serial_number = 0
        for i in xrange(len(_buffer)):
            _serial_number += (_buffer[i] << (8 * i))
        return _serial_number

    @property
    def transceiver_serial(self):
        _buffer = TRANS_SN_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_TRANS_SERIAL_NO, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_TRANS_SN_LENGTH))
        serial_number = 0
        for i in xrange(len(_buffer)):
            serial_number += (_buffer[i] << (8 * i))
        return serial_number

    @property
    def card_number(self):
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_NUMBER, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        return _buffer.value

    @property
    def card_channel(self):
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CHAN_NO_ON_CARD, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        return _buffer.value

    @property
    def transceiver_type(self):
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_TRANS_TYPE, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        retval = _buffer.value
        return retval

    @property
    def channel_info(self):
        return ChannelInfo(channel=self.channel,
                           name=self.device_description,
                           manufacturer=self.manufacturer_name,
                           fw_version=self.firmware_version,
                           hw_version=self.hardware_version,
                           card_serial=self.card_serial,
                           trans_serial=self.transceiver_serial,
                           trans_type=self.transceiver_type,
                           card_number=self.card_number,
                           channel_on_card=self.card_channel)

    ################### Public functions ##################
    def read(self):
        try:
            return self.__rx_queue.get_nowait()
        except Queue.Empty:
            return None

    def write(self, msg):
        self.__tx_queue.put_nowait()
        self.__tx_callback()

    def clear_queues(self):
        while True:
            try:
                self.__rx_queue.get_nowait()
            except Queue.Empty:
                break
        while True:
            try:
                self.__tx_queue.get_nowait()
            except Queue.Empty:
                break
        canlib.canFlushTransmitQueue(self.__handle)
        canlib.canFlushReceiveQueue(self.__handle)

    def add_listener(self, listener):
        if not isinstance(listener, Listener):
            _err_str = "listener to be added (type %s) should be of type"
            _err_str += " 'Listener'"
            raise TypeError(_err_str % type(listener))
        else:
            self.__listeners.append(listener)

    def remove_listener(self, listener):
        if listener in self.__listeners:
            self.__listeners.remove(listener)

    def enable_callback(self):
        canlib.kvSetNotifyCallback(self.__handle, self.__ctypes_callback, None,
          canstat.canNOTIFY_ALL)

    def disable_callback(self):
        canlib.kvSetNotifyCallback(self.__handle, self.__ctypes_callback, None,
          canstat.canNOTIFY_NONE)

    def shutdown(self):
        self.disable_callback()
        canlib.canBusOff(self.__handle)
        time.sleep(0.05)
        canlib.canClose(self.__handle)

    ################## Private functions ##################
    def __get_bus_statistics(self):
        canlib.canRequestBusStatistics(self.__handle)
        _stats = canlib.c_canBusStatistics()
        canlib.canGetBusStatistics(self.__handle, ctypes.byref(_stats),
          ctypes.c_uint(28))
        return _stats

    def __set_acceptance_filter(self, value, msg_type):
        if msg_type == canlib.ACCEPTANCE_FILTER_TYPE_STD:
            _max_value = ((2 ** 11) - 1)
        elif msg_type == canlib.ACCEPTANCE_FILTER_TYPE_EXT:
            _max_value = ((2 ** 29) - 1)
        else:
            _err_str = "msg_type (%d) should be either"
            _err_str += " ACCEPTANCE_FILTER_TYPE_STD or"
            _err_str += " ACCEPTANCE_FILTER_TYPE_EXT"
            raise ValueError(_err_str % value)
        if not isinstance(value, types.TupleType):
            _err_str = "acceptance_filter (%s) is not a tuple"
            raise TypeError(_err_str % value)
        if len(value) != 2:
            _err_str = "acceptance_filter contains %d elements (should be 2)"
            raise IndexError(_err_str % len(value))
        if not isinstance(value[0], (types.IntType, types.LongType)):
            _err_str = "acceptance code (%s) is not of type 'int' or 'long'"
            raise TypeError(_err_str % value)
        if not isinstance(value[1], (types.IntType, types.LongType)):
            _err_str = "acceptance mask (%s) is not of type 'int' or 'long'"
            raise TypeError(_err_str % value)
        if value[0] < 0:
            _err_str = "acceptance code (%s) < 0"
            raise ValueError(_err_str % value)
        if value[0] > _max_value:
            _err_str = "acceptance code (%s) > %d" % (value[0], _max_value)
            raise ValueError(_err_str % value)
        if value[1] < 0:
            _err_str = "acceptance mask (%s) < 0"
            raise ValueError(_err_str % value)
        if value[1] > _max_value:
            _err_str = "acceptance mask (%s) > %d" % (value[1], _max_value)
            raise ValueError(_err_str % value)
        if msg_type == canlib.ACCEPTANCE_FILTER_TYPE_STD:
            self.__std_acceptance_code = value[0]
            self.__std_acceptance_mask = value[1]
            canlib.canSetAcceptanceFilter(self.__handle, self.std_acceptance_filter[0],
              self.std_acceptance_filter[1], msg_type)
        else:
            self.__ext_acceptance_code = value[0]
            self.__ext_acceptance_mask = value[1]
            canlib.canSetAcceptanceFilter(self.__handle, self.ext_acceptance_filter[0],
              self.ext_acceptance_filter[1], msg_type)

    def __update_bus_parameters(self):
        try:
            canlib.canBusOff(self.__handle)
            canlib.canSetBusParams(self.__handle, self.speed, self.tseg1,
              self.tseg2, self.sjw, self.no_samp, 0)
            canlib.canBusOn(self.__handle)
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
                self.__rx_queue.put_nowait(_rx_msg)

    def __get_message(self):
        _arb_id = ctypes.c_long(0)
        _data = ctypes.create_string_buffer(8)
        _dlc = ctypes.c_uint(0)
        _flags = ctypes.c_uint(0)
        _timestamp = ctypes.c_long(0)
        _status = canlib.canRead(self.__handle,
          ctypes.byref(_arb_id), ctypes.byref(_data),
          ctypes.byref(_dlc), ctypes.byref(_flags),
          ctypes.byref(_timestamp))
        if _status.value == canstat.canOK:
            _data_array = map(ord, _data)
            _rx_msg = Message(arb_id=_arb_id.value,
                              data=_data_array[:_dlc.value],
                              dlc=int(_dlc.value),
                              timestamp = (float(_timestamp.value) /
                                1000000))
            _rx_msg.flags = int(_flags.value) & canstat.canMSG_MASK
            return _rx_msg
        else:
            return None

    def __tx_callback(self):
        try:
            _to_send = self.__tx_queue.get_nowait()
        except Queue.Empty:
            return
        _byte_strings = [("%c" % byte) for byte in _to_send.payload]
        _data_string = "".join(_byte_strings)
        canlib.canWrite(self._canlib_handle, _to_send.device_id,
          _data_string, _to_send.dlc, _to_send.flags)

    def __status_callback(self, timestamp):
        canlib.canRequestChipStatus(self.__handle)
        _stat_flags = ctypes.c_long(0)
        canlib.canReadStatus(self.__handle, ctypes.byref(_stat_flags))
        if _stat_flags.value != self.__old_stat_flags:
            for _listener in self.__listeners:
                _listener.on_status_change(timestamp, _stat_flags.value, self.__old_stat_flags)
            self.__old_stat_flags = _stat_flags.value

    def __callback(self, hnd, context, event):
        if event == canstat.canNOTIFY_RX:
            self.__rx_callback()
        elif event == canstat.canNOTIFY_TX:
            self.__tx_callback()
        elif event == canstat.canNOTIFY_STATUS:
            _timestamp = canlib.canReadTimer(self.__handle)
            self.__status_callback(_timestamp)
        return 0


class Listener(object):

    def on_message_received(self, msg):
        pass

    def on_status_change(self, timestamp, new_status, old_status):
        pass


class ChannelInfo(object):

    def __init__(self, channel=0, name="", manufacturer="",
      fw_version="", hw_version="", card_serial=0, trans_serial=0,
      trans_type="", card_number=0, channel_on_card=0):
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
        if not isinstance(value, types.IntType):
            raise TypeError("channel is not of type 'int'")
        if value < 0:
            raise ValueError("channel < 0")
        self.__channel = value

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("name is not of type 'str'")
        self.__name = value

    @property
    def manufacturer(self):
        return self.__manufacturer

    @manufacturer.setter
    def manufacturer(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("manufacturer is not of type 'str'")
        self.__manufacturer = value

    @property
    def fw_version(self):
        return self.__fw_version

    @fw_version.setter
    def fw_version(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("fw_version is not of type 'str'")
        self.__fw_version = value

    @property
    def hw_version(self):
        return self.__hw_version

    @hw_version.setter
    def hw_version(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("hw_version is not of type 'str'")
        self.__hw_version = value

    @property
    def card_serial(self):
        return self.__card_serial

    @card_serial.setter
    def card_serial(self, value):
        if not isinstance(value, types.IntType):
            raise TypeError("card_serial is not of type 'int'")
        if value < 0:
            raise ValueError("card_serial < 0")
        self.__card_serial = value

    @property
    def trans_serial(self):
        return self.__trans_serial

    @trans_serial.setter
    def trans_serial(self, value):
        if not isinstance(value, types.IntType):
            raise TypeError("trans_serial is not of type 'int'")
        if value < 0:
            raise ValueError("trans_serial < 0")
        self.__trans_serial = value

    @property
    def trans_type(self):
        return canstat.canTransceiverTypeStrings[self.__trans_type]

    @trans_type.setter
    def trans_type(self, value):
        if not isinstance(value, types.LongType):
            raise TypeError("trans_type (type %s) is not of type 'long'" % type(value))
        if value not in canstat.canTransceiverTypeStrings.keys():
            raise ValueError("trans_type not known to CANLIB")
        self.__trans_type = value

    @property
    def card_number(self):
        return self.__card_number

    @card_number.setter
    def card_number(self, value):
        if not isinstance(value, types.LongType):
            raise TypeError("card_number is not of type 'long'")
        if value < 0:
            raise ValueError("card_number < 0")
        self.__card_number = value

    @property
    def channel_on_card(self):
        return self.__channel_on_card

    @channel_on_card.setter
    def channel_on_card(self, value):
        if not isinstance(value, types.LongType):
            raise TypeError("channel_on_card is not of type 'long'")
        if value < 0:
            raise ValueError("channel_on_card < 0")
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
        retval += "\n"
        return retval


class LogInfo(object):

    def __init__(self, log_start_time=None, log_end_time=None,
      original_file_name="default.dat", test_location="default",
      tester_name="default"):
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
        if not isinstance(value, (datetime.datetime, types.NoneType)):
            raise TypeError("log_end_time is not of type 'datetime.datetime' or 'NoneType'")
        try:
            if self.log_end_time < value:
                raise ValueError("log start time is after log end time")
        except (AttributeError, TypeError):
            pass
        self.__log_start_time = value

    @property
    def log_end_time(self):
        return self.__log_end_time

    @log_end_time.setter
    def log_end_time(self, value):
        if not isinstance(value, (datetime.datetime, types.NoneType)):
            raise TypeError("log_end_time is not of type 'datetime.datetime' or 'NoneType'")
        try:
            if self.log_start_time > value:
                raise ValueError("log end time is before log start time")
        except (AttributeError, TypeError):
            pass
        self.__log_end_time = value

    @property
    def original_file_name(self):
        return self.__original_file_name

    @original_file_name.setter
    def original_file_name(self, value):
        if not isinstance(value, types.StringType):
            raise ValueError("original_file_name is not of type 'str'")
        self.__original_file_name = value

    @property
    def test_location(self):
        return self.__test_location

    @test_location.setter
    def test_location(self, value):
        if not isinstance(value, types.StringType):
            raise ValueError("test_location is not of type 'str'")
        self.__test_location = value

    @property
    def tester_name(self):
        return self.__tester_name

    @tester_name.setter
    def tester_name(self, value):
        if not isinstance(value, types.StringType):
            raise ValueError("tester_name is not of type 'str'")
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
        retval += "\n"
        return retval


class MachineInfo(object):

    def __init__(self, machine_name="", python_version="", os_type=""):
        self.machine_name = machine_name
        self.python_version = python_version
        self.os_type = os_type
        self.canlib_version = get_canlib_info()
        self.pycanlib_version = __version__

    @property
    def machine_name(self):
        return self.__machine_name

    @machine_name.setter
    def machine_name(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("machine_name is not of type 'str'")
        self.__machine_name = value

    @property
    def python_version(self):
        return self.__python_version

    @python_version.setter
    def python_version(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("python_version is not of type 'str'")
        self.__python_version = value

    @property
    def os_type(self):
        return self.__os_type

    @os_type.setter
    def os_type(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("os_type is not of type 'str'")
        self.__os_type = value

    @property
    def canlib_version(self):
        return self.__canlib_version

    @canlib_version.setter
    def canlib_version(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("canlib_version is not of type 'str'")
        self.__canlib_version = value

    @property
    def pycanlib_version(self):
        return self.__pycanlib_version

    @pycanlib_version.setter
    def pycanlib_version(self, value):
        if not isinstance(value, types.StringType):
            raise TypeError("pycanlib_version is not of type 'str'")
        self.__pycanlib_version = value

    def __str__(self):
        retval = "-"*len("Machine Info")
        retval += "\nMachine Info\n"
        retval += "-"*len("Machine Info")
        retval += "\n"
        retval += "Machine name: %s\n" % self.machine_name
        retval += "Python: %s\n" % self.python_version
        retval += "OS: %s\n" % self.os_type
        retval += "CANLIB: %s\n" % self.canlib_version
        retval += "pycanlib: %s\n" % self.pycanlib_version
        retval += "\n"
        return retval


def get_host_machine_info():
    if sys.platform == "win32":
        _machine_name = os.getenv("COMPUTERNAME")
    else:
        _machine_name = os.getenv("HOSTNAME")
    _python_version = sys.version[:sys.version.index(" ")]
    return MachineInfo(machine_name=_machine_name,
                       python_version=_python_version,
                       os_type=sys.platform)


def get_canlib_info():
    """
    Method: get_canlib_info

    Returns the version of the CANLIB SDK installed on the host machine, as
    a string.
    """
    _canlib_prod_ver_32 = \
      canlib.canGetVersionEx(canlib.canVERSION_CANLIB32_PRODVER32)
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
        if not isinstance(value, LogInfo):
            raise TypeError("log_info is not of type 'LogInfo'")
        self.__log_info = value

    @property
    def channel_info(self):
        return self.__channel_info

    @channel_info.setter
    def channel_info(self, value):
        if not isinstance(value, ChannelInfo):
            raise TypeError("channel_info is not of type 'ChannelInfo'")
        self.__channel_info = value

    @property
    def machine_info(self):
        return self.__machine_info

    @machine_info.setter
    def machine_info(self, value):
        if not isinstance(value, MachineInfo):
            raise TypeError("machine_info is not of type 'MachineInfo'")
        self.__machine_info = value

    @property
    def message_lists(self):
        return self.__message_lists

    @message_lists.setter
    def message_lists(self, value):
        if not isinstance(value, types.ListType):
            raise TypeError("message_lists is not of type 'list'")
        for (_index, _value) in enumerate(value):
            if not isinstance(_value, MessageList):
                raise TypeError("message_lists[%d] is not of type MessageList" % _index)
        self. __message_lists = value

    def __str__(self):
        retval = ""
        retval += "%s" % self.machine_info
        retval += "%s" % self.log_info
        retval += "%s" % self.channel_info
        for _list in self.message_lists:
            retval += "%s" % _list
        return retval
