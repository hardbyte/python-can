from pycanlib import canlib, canstat

import ctypes
import Queue
import sys
import time
import types

canlib.canInitializeLibrary()

ID_TYPE_EXT = True
ID_TYPE_STD = False

REMOTE_FRAME = True
DATA_FRAME = False

WAKEUP_MSG = True

ERROR_FRAME = True

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
        return (canlib.canReadTimer(self.__handle) / 100000.0)

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
        try:
            return canstat.canTransceiverTypeStrings[_buffer.value]
        except KeyError:
            return "Transceiver type %d is unknown to CANLIB" % _buffer.value

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
        _rx_msg = self.__get_message()
        while _rx_msg != None:
            for _listener in self.__listeners:
                _listener.on_message_received(_rx_msg)
            self.__rx_queue.put_nowait(_rx_msg)
            _rx_msg = self.__get_message()

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
                                1000))
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
