import atexit
import ctypes
import logging
import os
import Queue
import sys
import types
from xml.dom import minidom

from pycanlib import canlib, canstat


canlib.canInitializeLibrary()


CAN_MODULE_LOGGER = logging.getLogger("pycanlib.CAN")
HANDLE_CLASS_LOGGER = logging.getLogger("pycanlib.CAN._Handle")
BUS_CLASS_LOGGER = logging.getLogger("pycanlib.CAN.Bus")
LOG_MESSAGE_CLASS_LOGGER = logging.getLogger("pycanlib.CAN.LogMessage")
CAN_MESSAGE_CLASS_LOGGER = logging.getLogger("pycanlib.CAN.Message")
INFO_MESSAGE_CLASS_LOGGER = logging.getLogger("pycanlib.CAN.InfoMessage")

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

try:
    VERSION_NUMBER_FILE = open(os.path.join(os.path.dirname(__file__),
                              "version.txt"), "r")
    __version__ = VERSION_NUMBER_FILE.readline()
    VERSION_NUMBER_FILE.close()
except IOError as read_error:#pragma: no cover
    print read_error
    __version__ = "UNKNOWN"


class PycanlibError(Exception):
    pass


TIMER_TICKS_PER_SECOND = 1000000
MICROSECONDS_PER_TIMER_TICK = (TIMER_TICKS_PER_SECOND / 1000000)


class InvalidParameterError(PycanlibError):

    def __init__(self, parameter_name, parameter_value, reason):
        PycanlibError.__init__(self)
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.reason = reason

    def __str__(self):
        return ("%s: invalid value '%s' for parameter '%s' - %s" %
          (self.__class__.__name__, self.parameter_value,
          self.parameter_name, self.reason))


class InvalidMessageParameterError(InvalidParameterError):
    pass


class InvalidBusParameterError(InvalidParameterError):
    pass


class LogMessage(object):

    def __init__(self, timestamp=0.0):
        _start_msg = ("Starting LogMessage.__init__ - timestamp %s" %
          timestamp)
        LOG_MESSAGE_CLASS_LOGGER.debug(_start_msg)
        if not isinstance(timestamp, types.FloatType):
            _bad_timestamp_error = InvalidMessageParameterError("timestamp",
              timestamp, ("expected float; received '%s'" %
              timestamp.__class__.__name__))
            LOG_MESSAGE_CLASS_LOGGER.debug("LogMessage.__init__: %s" %
              _bad_timestamp_error)
            raise _bad_timestamp_error
        if timestamp < 0:
            _bad_timestamp_error = InvalidMessageParameterError("timestamp",
              timestamp, "timestamp value must be positive")
            LOG_MESSAGE_CLASS_LOGGER.debug("LogMessage.__init__: %s" %
              _bad_timestamp_error)
            raise _bad_timestamp_error
        self.timestamp = timestamp
        _finish_msg = "LogMessage.__init__ completed successfully"
        LOG_MESSAGE_CLASS_LOGGER.debug(_finish_msg)

    def __str__(self):
        return "%.6f" % self.timestamp

    def to_xml(self, element_type="log_message"):
        _document = minidom.Document()
        retval = _document.createElement(element_type)
        _timestamp_element = _document.createElement("timestamp")
        _timestamp_text_node = _document.createTextNode("%s" %
          self.timestamp)
        _timestamp_element.appendChild(_timestamp_text_node)
        retval.appendChild(_timestamp_element)
        return retval


class Message(LogMessage):

    def __init__(self, device_id=0, data=None, dlc=0, flags=0,
      timestamp=0.0):
        if data is None:
            data = []
        LogMessage.__init__(self, timestamp)
        if not isinstance(device_id, types.IntType):
            raise InvalidMessageParameterError("device_id", device_id,
              ("expected int; received '%s'" %
              device_id.__class__.__name__))
        if device_id not in range(0, 2 ** 11):
            raise InvalidMessageParameterError("device_id", device_id,
              "device_id must be in range [0, 2**11-1]")
        self.device_id = device_id
        if len(data) not in range(0, 9):
            raise InvalidMessageParameterError("data", data,
              "data array length must be in range [0, 8]")
        for item in data:
            if not isinstance(item, types.IntType):
                raise InvalidMessageParameterError("data", data,
                  ("data array must contain only integers; found '%s'" %
                  item.__class__.__name__))
            if item not in range(0, 2 ** 8):
                raise InvalidMessageParameterError("data", data,
                  "data array element values must be in range [0, 2**8-1]")
        self.data = data
        if not isinstance(dlc, types.IntType):
            raise InvalidMessageParameterError("dlc", dlc,
              "expected int; received %s" % dlc.__class__.__name__)
        if dlc not in range(0, 9):
            raise InvalidMessageParameterError("dlc", dlc,
              "DLC value must be in range [0, 8]")
        self.dlc = dlc
        if not isinstance(flags, types.IntType):
            raise InvalidMessageParameterError("flags", flags,
              "expected int; received %s" % flags.__class__.__name__)
        if flags not in range(0, 2 ** 16):
            raise InvalidMessageParameterError("flags", flags,
              "flags value must be in range [0, 2**16-1]")
        self.flags = flags

    def __str__(self):
        _field_strings = []
        _field_strings.append(LogMessage.__str__(self))
        _field_strings.append("%.4x" % self.device_id)
        _field_strings.append("%.4x" % self.flags)
        _field_strings.append("%d" % self.dlc)
        _data_strings = []
        if self.data != None:
            for byte in self.data:
                _data_strings.append("%.2x" % byte)
        if len(_data_strings) > 0:
            _field_strings.append(" ".join(_data_strings))
        return "\t".join(_field_strings)

    def to_xml(self, element_type="can_message"):
        _document = minidom.Document()
        retval = LogMessage.to_xml(self, element_type)
        _device_id_element = _document.createElement("device_id")
        _device_id_text_node = _document.createTextNode("%.4x" % self.device_id)
        _device_id_element.appendChild(_device_id_text_node)
        _flags_element = _document.createElement("flags")
        _flags_text_node = _document.createTextNode("%.4x" % self.flags)
        _flags_element.appendChild(_flags_text_node)
        _dlc_element = _document.createElement("dlc")
        _dlc_text_node = _document.createTextNode("%d" % self.dlc)
        _dlc_element.appendChild(_dlc_text_node)
        retval.appendChild(_device_id_element)
        retval.appendChild(_flags_element)
        retval.appendChild(_dlc_element)
        if len(self.data) > 0:
            _data_element = _document.createElement("data")
            for i in xrange(len(self.data)):
                _data_byte_element = _document.createElement("byte_%d" % i)
                _data_byte_text_node = \
                  _document.createTextNode("%.2x" % self.data[i])
                _data_byte_element.appendChild(_data_byte_text_node)
                _data_element.appendChild(_data_byte_element)
            retval.appendChild(_data_element)
        return retval

class InfoMessage(LogMessage):

    def __init__(self, timestamp=0.0, info=None):
        LogMessage.__init__(self, timestamp)
        self.info = info

    def __str__(self):
        if self.info != None:
            return ("%s\t%s" % (LogMessage.__str__(self), self.info))
        else:
            return "%s" % LogMessage.__str__(self)

    def to_xml(self, element_type="info_message"):
        _document = minidom.Document()
        retval = LogMessage.to_xml(self, element_type)
        _info_element = _document.createElement("info")
        _info_text_node = _document.createTextNode(self.info)
        _info_element.appendChild(_info_text_node)
        retval.appendChild(_info_element)
        return retval


READ_HANDLE_REGISTRY = {}
WRITE_HANDLE_REGISTRY = {}


def _receive_callback(handle):#pragma: no cover
    #called by the callback registered with CANLIB, but coverage can't figure
    #that out
    CAN_MODULE_LOGGER.debug("Entering _receive_callback for handle %d" % handle)
    if READ_HANDLE_REGISTRY[handle] != None:
        READ_HANDLE_REGISTRY[handle].receive_callback()
    CAN_MODULE_LOGGER.debug("Leaving _receive_callback for handle %d" % handle)
    return 0


RX_CALLBACK = canlib.CALLBACKFUNC(_receive_callback)


def _transmit_callback(handle):
    CAN_MODULE_LOGGER.debug("Entering _transmit_callback for handle %d" %
                            handle)
    if WRITE_HANDLE_REGISTRY[handle] != None:
        WRITE_HANDLE_REGISTRY[handle].transmit_callback()
    CAN_MODULE_LOGGER.debug("Leaving _transmit_callback for handle %d" % handle)
    return 0


TX_CALLBACK = canlib.CALLBACKFUNC(_transmit_callback)


class _Handle(object):

    def __init__(self, channel, flags):
        _num_channels = ctypes.c_int(0)
        canlib.canGetNumberOfChannels(ctypes.byref(_num_channels))
        if channel not in range(0, _num_channels.value):
            raise InvalidBusParameterError("channel", channel,
              ("available channels on this system are in the range [0, %d]" %
              _num_channels.value))
        self.channel = channel
        if flags & (0xFFFF - canlib.FLAGS_MASK) != 0:
            raise InvalidBusParameterError("flags", flags,
              "must contain only the canOPEN_* flags listed in canlib.py")
        self.flags = flags
        try:
            self._canlib_handle = canlib.canOpenChannel(channel, flags)
        except canlib.CANLIBError as open_channel_error:
            if open_channel_error.errorCode == canstat.canERR_NOTFOUND:
                raise InvalidBusParameterError("flags", flags,
                  "no hardware is available that has all these capabilities")
            else:#pragma: no cover
                raise open_channel_error
        self.listeners = []
        self.tx_queue = Queue.Queue(0)
        _timer_res = ctypes.c_long(MICROSECONDS_PER_TIMER_TICK)
        canlib.canFlushReceiveQueue(self._canlib_handle)
        canlib.canFlushTransmitQueue(self._canlib_handle)
        canlib.canIoCtl(self._canlib_handle, canlib.canIOCTL_SET_TIMER_SCALE,
          ctypes.byref(_timer_res), 4)
        canlib.canBusOn(self._canlib_handle)
        self.reading = False
        self.writing = False
        self.receive_callback_enabled = True
        self.transmit_callback_enabled = True

    def get_canlib_handle(self):
        return self._canlib_handle

    def transmit_callback(self):
        HANDLE_CLASS_LOGGER.debug("Transmit buffer level for handle %d: %d" %
          (self._canlib_handle, self.get_transmit_buffer_level()))
        if not self.writing and self.transmit_callback_enabled:
            self.writing = True
            try:
                _to_send = self.tx_queue.get_nowait()
            except Queue.Empty:#pragma: no cover
                #this part of transmit_callback executes when CANLIB fires the
                #transmit callback event for this handle, but coverage isn't
                #smart enough to figure this out, so it thinks it isn't called
                #at all
                self.writing = False
                return
            _data_string = "".join([("%c" % byte) for byte in _to_send.data])
            canlib.canWrite(self._canlib_handle, _to_send.device_id,
              _data_string, _to_send.dlc, _to_send.flags)
            self.writing = False

    def write(self, msg):
        _old_size = self.tx_queue.qsize()
        self.tx_queue.put_nowait(msg)
        if _old_size == 0:
            self.transmit_callback()

    def receive_callback(self):#pragma: no cover
        #this is called by the callback registered with CANLIB, but because
        #coverage isn't smart enough to figure this out, it thinks this
        #function is never called at all
        _callback_entry_msg = "Entering _Handle.ReceiveCallback"
        HANDLE_CLASS_LOGGER.info(_callback_entry_msg)
        if not self.reading and self.receive_callback_enabled:
            self.reading = True
            _device_id = ctypes.c_long(0)
            _data = ctypes.create_string_buffer(8)
            _dlc = ctypes.c_uint(0)
            _flags = ctypes.c_uint(0)
            _timestamp = ctypes.c_long(0)
            _status = canlib.canRead(self._canlib_handle,
              ctypes.byref(_device_id), ctypes.byref(_data),
              ctypes.byref(_dlc), ctypes.byref(_flags),
              ctypes.byref(_timestamp))
            while _status.value == canstat.canOK:
                _data_array = []
                for _char in _data:
                    _data_array.append(ord(_char))
                HANDLE_CLASS_LOGGER.debug("Creating new Message object")
                _rx_msg = Message(_device_id.value, _data_array[:_dlc.value],
                  int(_dlc.value), int(_flags.value), (float(_timestamp.value) /
                  TIMER_TICKS_PER_SECOND))
                for _listener in self.listeners:
                    _listener.on_message_received(_rx_msg)
                _status = canlib.canRead(self._canlib_handle,
                  ctypes.byref(_device_id), ctypes.byref(_data),
                  ctypes.byref(_dlc), ctypes.byref(_flags),
                  ctypes.byref(_timestamp))
            _exit_str = "Leaving _Handle.ReceiveCallback - status is %s (%d)"
            _callback_exit_msg = (_exit_str %
              (canstat.canStatusLookupTable[_status.value], _status.value))
            HANDLE_CLASS_LOGGER.info(_callback_exit_msg)
            canlib.kvSetNotifyCallback(self._canlib_handle, RX_CALLBACK,
              ctypes.c_void_p(None), canstat.canNOTIFY_RX)
            self.reading = False

    def add_listener(self, listener):
        self.listeners.append(listener)

    def read_timer(self):
        return canlib.canReadTimer(self._canlib_handle)

    def get_receive_buffer_level(self):#pragma: no cover
        #this is called by the callback registered with CANLIB, but because
        #coverage isn't smart enough to figure this out, it thinks this
        #function is never called at all
        rx_level = ctypes.c_int(0)
        canlib.canIoCtl(self._canlib_handle,
          canlib.canIOCTL_GET_RX_BUFFER_LEVEL, ctypes.byref(rx_level), 4)
        return rx_level.value

    def get_transmit_buffer_level(self):
        tx_level = ctypes.c_int(0)
        canlib.canIoCtl(self._canlib_handle,
          canlib.canIOCTL_GET_TX_BUFFER_LEVEL, ctypes.byref(tx_level), 4)
        return tx_level.value

    def get_device_description(self):#pragma: no cover
        _buffer = ctypes.create_string_buffer(MAX_DEVICE_DESCR_LENGTH)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_DEVDESCR_ASCII, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_DEVICE_DESCR_LENGTH))
        return _buffer.value

    def get_device_manufacturer_name(self):#pragma: no cover
        _buffer = ctypes.create_string_buffer(MAX_MANUFACTURER_NAME_LENGTH)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_MFGNAME_ASCII, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_MANUFACTURER_NAME_LENGTH))
        return _buffer.value

    def get_device_firmware_version(self):#pragma: no cover
        _buffer = FW_VERSION_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_FIRMWARE_REV, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_FW_VERSION_LENGTH))
        _version_number = []
        for i in [6, 4, 0, 2]:
            _version_number.append((_buffer[i + 1] << 8) + _buffer[i])
        return "%d.%d.%d.%d" % (_version_number[0], _version_number[1],
          _version_number[2], _version_number[3])

    def get_device_hardware_version(self):#pragma: no cover
        _buffer = HW_VERSION_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_HARDWARE_REV, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_HW_VERSION_LENGTH))
        _version_number = []
        for i in [2, 0]:
            _version_number.append((_buffer[i + 1] << 8) + _buffer[i])
        return "%d.%d" % (_version_number[0], _version_number[1])

    def get_device_card_serial(self):#pragma: no cover
        _buffer = CARD_SN_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_SERIAL_NO, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_CARD_SN_LENGTH))
        _serial_number = 0
        for i in xrange(len(_buffer)):
            _serial_number += (_buffer[i] << (8 * i))
        return _serial_number

    def get_device_transceiver_serial(self):#pragma: no cover
        _buffer = TRANS_SN_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_TRANS_SERIAL_NO, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_TRANS_SN_LENGTH))
        serial_number = 0
        for i in xrange(len(_buffer)):
            serial_number += (_buffer[i] << (8 * i))
        return serial_number

    def get_device_card_number(self):#pragma: no cover
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_NUMBER, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        return _buffer.value

    def get_device_channel_on_card(self):#pragma: no cover
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CHAN_NO_ON_CARD, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        return _buffer.value

    def get_device_transceiver_type(self):#pragma: no cover
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_TRANS_TYPE, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        try:
            return canstat.canTransceiverTypeStrings[_buffer.value]
        except KeyError:
            return "Transceiver type %d is unknown to CANLIB" % _buffer.value

    def get_statistics(self):
        canlib.canRequestBusStatistics(self._canlib_handle)
        _stat_struct = canlib.c_canBusStatistics()
        canlib.canGetBusStatistics(self._canlib_handle,
          ctypes.byref(_stat_struct), ctypes.c_uint(28))
        return BusStatistics(_stat_struct.std_data,
                             _stat_struct.std_remote,
                             _stat_struct.ext_data,
                             _stat_struct.ext_remote,
                             _stat_struct.err_frame,
                             _stat_struct.bus_load,
                             _stat_struct.overruns)

class BusStatistics(object):
    def __init__(self, std_data, std_remote, ext_data, ext_remote, err_frame,
      bus_load, overruns):
        self.std_data = std_data
        self.std_remote = std_remote
        self.ext_data = ext_data
        self.ext_remote = ext_remote
        self.err_frame = err_frame
        self.bus_load = float(bus_load)/100
        self.overruns = overruns


def _get_handle(channel_number, flags, registry):
    _found_handle = False
    handle = None
    for _key in registry.keys():
        if (registry[_key].channel == channel_number) and \
          (registry[_key].flags == flags):
            _found_handle = True
            handle = registry[_key]
    if not _found_handle:
        handle = _Handle(channel_number, flags)
        registry[handle.get_canlib_handle()] = handle
    if registry == READ_HANDLE_REGISTRY:
        CAN_MODULE_LOGGER.debug("Setting notify callback for read handle %d" %
          handle.get_canlib_handle())
        canlib.kvSetNotifyCallback(handle.get_canlib_handle(), RX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_RX)
    else:
        CAN_MODULE_LOGGER.debug("Setting notify callback for write handle %d" %
          handle.get_canlib_handle())
        canlib.kvSetNotifyCallback(handle.get_canlib_handle(), TX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_TX)
    return handle


class ChannelInfo(object):#pragma: no cover

    def __init__(self, channel, name, manufacturer, fw_version, hw_version,
      card_serial, trans_serial, trans_type, card_number, channel_on_card):
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

    def __str__(self):
        retval = "CANLIB channel: %s\n" % self.channel
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

    def to_xml(self):
        _document = minidom.Document()
        retval = _document.createElement("channel_info")
        _channel_number_element = _document.createElement("canlib_channel")
        _channel_number_text = _document.createTextNode("%d" % self.channel)
        _channel_number_element.appendChild(_channel_number_text)
        retval.appendChild(_channel_number_element)
        _channel_name_element = _document.createElement("device_name")
        _channel_name_text = _document.createTextNode(self.name)
        _channel_name_element.appendChild(_channel_name_text)
        retval.appendChild(_channel_name_element)
        _channel_manufacturer_element = \
          _document.createElement("device_manufacturer")
        _channel_manufacturer_text = _document.createTextNode(self.manufacturer)
        _channel_manufacturer_element.appendChild(_channel_manufacturer_text)
        retval.appendChild(_channel_manufacturer_element)
        _channel_fw_version_element = \
          _document.createElement("device_firmware_version")
        _channel_fw_version_text = _document.createTextNode(self.fw_version)
        _channel_fw_version_element.appendChild(_channel_fw_version_text)
        retval.appendChild(_channel_fw_version_element)
        _channel_hw_version_element = \
          _document.createElement("device_hardware_version")
        _channel_hw_version_text = _document.createTextNode(self.hw_version)
        _channel_hw_version_element.appendChild(_channel_hw_version_text)
        retval.appendChild(_channel_hw_version_element)
        _channel_card_serial_element = \
          _document.createElement("device_serial_number")
        _channel_card_serial_text = _document.createTextNode("%s" %
          self.card_serial)
        _channel_card_serial_element.appendChild(_channel_card_serial_text)
        retval.appendChild(_channel_card_serial_element)
        _channel_trans_type_element = \
          _document.createElement("transceiver_type")
        _channel_trans_type_text = \
          _document.createTextNode(self.trans_type)
        _channel_trans_type_element.appendChild(
          _channel_trans_type_text)
        retval.appendChild(_channel_trans_type_element)
        _channel_trans_serial_element = \
          _document.createElement("transceiver_serial_number")
        _channel_trans_serial_text = \
          _document.createTextNode("%s" % self.trans_serial)
        _channel_trans_serial_element.appendChild(
          _channel_trans_serial_text)
        retval.appendChild(_channel_trans_serial_element)
        _channel_card_number_element = _document.createElement("card_number")
        _channel_card_number_text = _document.createTextNode("%s" %
          self.card_number)
        _channel_card_number_element.appendChild(_channel_card_number_text)
        retval.appendChild(_channel_card_number_element)
        _channel_number_on_card_element = \
          _document.createElement("card_channel")
        _channel_number_on_card_text = \
          _document.createTextNode("%s" % self.channel_on_card)
        _channel_number_on_card_element.appendChild(
          _channel_number_on_card_text)
        retval.appendChild(_channel_number_on_card_element)
        return retval


class MachineInfo(object):

    def __init__(self, machine_name, python_version, os_type):
        self.machine_name = machine_name
        self.python_version = python_version
        self.os_type = os_type

    def __str__(self):
        retval = "Machine name: %s\n" % self.machine_name
        retval += "Python version: %s\n" % self.python_version
        retval += "OS: %s\n" % self.os_type
        retval += "CANLIB: %s\n" % get_canlib_info()
        retval += "pycanlib version: %s\n" % __version__
        return retval

    def to_xml(self):
        _document = minidom.Document()
        retval = _document.createElement("machine_info")
        _machine_name_element = _document.createElement("name")
        _machine_name_text = _document.createTextNode(self.machine_name)
        _machine_name_element.appendChild(_machine_name_text)
        retval.appendChild(_machine_name_element)
        _machine_os_element = _document.createElement("os")
        _machine_os_text = _document.createTextNode(self.os_type)
        _machine_os_element.appendChild(_machine_os_text)
        retval.appendChild(_machine_os_element)
        _machine_python_element = _document.createElement("python_version")
        _machine_python_text = _document.createTextNode(self.python_version)
        _machine_python_element.appendChild(_machine_python_text)
        retval.appendChild(_machine_python_element)
        _machine_canlib_element = _document.createElement("canlib_version")
        _machine_canlib_text = _document.createTextNode(get_canlib_info())
        _machine_canlib_element.appendChild(_machine_canlib_text)
        retval.appendChild(_machine_canlib_element)
        _machine_pycanlib_element = \
          _document.createElement("pycanlib_version")
        _machine_pycanlib_text = _document.createTextNode(__version__)
        _machine_pycanlib_element.appendChild(_machine_pycanlib_text)
        retval.appendChild(_machine_pycanlib_element)
        return retval

def get_host_machine_info():#pragma: no cover
    if sys.platform == "win32":
        machine_name = os.getenv("COMPUTERNAME")
    else:
        machine_name = os.getenv("HOSTNAME")
    python_version = sys.version[:sys.version.index(" ")]
    return MachineInfo(machine_name, python_version, sys.platform)


def get_canlib_info():#pragma: no cover
    _canlib_prod_ver_32 = \
      canlib.canGetVersionEx(canlib.canVERSION_CANLIB32_PRODVER32)
    _major_ver_no = (_canlib_prod_ver_32 & 0x00FF0000) >> 16
    _minor_ver_no = (_canlib_prod_ver_32 & 0x0000FF00) >> 8
    if (_canlib_prod_ver_32 & 0x000000FF) != 0:
        _minor_ver_letter = "%c" % (_canlib_prod_ver_32 & 0x000000FF)
    else:
        _minor_ver_letter = ""
    return "%d.%d%s" % (_major_ver_no, _minor_ver_no, _minor_ver_letter)


def create_log_xml_tree(host_info, channel_info, start_time, end_time,
  msg_list):
    retval = minidom.Document()
    _log_element = retval.createElement("pycanlib_log")
    _log_element.appendChild(host_info.to_xml())
    _log_element.appendChild(channel_info.to_xml())
    _log_info_element = retval.createElement("log_info")
    _log_start_time_element = retval.createElement("log_start_time")
    _log_start_time_text = retval.createTextNode("%s" % start_time)
    _log_start_time_element.appendChild(_log_start_time_text)
    _log_info_element.appendChild(_log_start_time_element)
    _log_end_time_element = retval.createElement("log_end_time")
    _log_end_time_text = retval.createTextNode("%s" % end_time)
    _log_end_time_element.appendChild(_log_end_time_text)
    _log_info_element.appendChild(_log_end_time_element)
    _log_element.appendChild(_log_info_element)
    _log_messages_element = retval.createElement("messages")
    for _message in msg_list:
        _log_messages_element.appendChild(_message.to_xml())
    _log_element.appendChild(_log_messages_element)
    retval.appendChild(_log_element)
    return retval


class Bus(object):

    def __init__(self, channel=0, flags=0, speed=1000000, tseg1=1, tseg2=0,
                 sjw=1, no_samp=1, driver_mode=canlib.canDRIVER_NORMAL,
                 name="default"):
        self.name = name
        BUS_CLASS_LOGGER.info("Getting read handle for new Bus instance '%s'" %
          self.name)
        self._read_handle = _get_handle(channel, flags, READ_HANDLE_REGISTRY)
        BUS_CLASS_LOGGER.info("Read handle for Bus '%s' is %d" %
                            (self.name, self._read_handle.get_canlib_handle()))
        BUS_CLASS_LOGGER.info("Getting write handle for new Bus instance '%s'" %
                            self.name)
        self._write_handle = _get_handle(channel, flags, WRITE_HANDLE_REGISTRY)
        BUS_CLASS_LOGGER.info("Write handle for Bus '%s' is %s" %
                            (self.name, self._write_handle.get_canlib_handle()))
        _old_speed = ctypes.c_long(0)
        _old_tseg1 = ctypes.c_uint(0)
        _old_tseg2 = ctypes.c_uint(0)
        _old_sjw = ctypes.c_uint(0)
        _old_sample_no = ctypes.c_uint(0)
        _old_sync_mode = ctypes.c_uint(0)
        canlib.canGetBusParams(self._read_handle.get_canlib_handle(),
          ctypes.byref(_old_speed), ctypes.byref(_old_tseg1),
          ctypes.byref(_old_tseg2), ctypes.byref(_old_sjw),
          ctypes.byref(_old_sample_no), ctypes.byref(_old_sync_mode))
        if ((speed != _old_speed.value) or (tseg1 != _old_tseg1.value) or
            (tseg2 != _old_tseg2.value) or (sjw != _old_sjw.value) or
            (no_samp != _old_sample_no.value)):
            canlib.canBusOff(self._read_handle.get_canlib_handle())
            canlib.canSetBusParams(self._read_handle.get_canlib_handle(),
                                   speed, tseg1, tseg2, sjw, no_samp, 0)
            canlib.canBusOn(self._read_handle.get_canlib_handle())
        canlib.canSetDriverMode(self._read_handle.get_canlib_handle(),
          driver_mode, canstat.canTRANSCEIVER_RESNET_NA)
        if driver_mode != canlib.canDRIVER_SILENT:
            canlib.canGetBusParams(self._write_handle.get_canlib_handle(),
              ctypes.byref(_old_speed), ctypes.byref(_old_tseg1),
              ctypes.byref(_old_tseg2), ctypes.byref(_old_sjw),
              ctypes.byref(_old_sample_no), ctypes.byref(_old_sync_mode))
            if ((speed != _old_speed.value) or (tseg1 != _old_tseg1.value) or
                (tseg2 != _old_tseg2.value) or (sjw != _old_sjw.value) or
                (no_samp != _old_sample_no.value)):
                canlib.canBusOff(self._write_handle.get_canlib_handle())
                canlib.canSetBusParams(self._write_handle.get_canlib_handle(),
                                       speed, tseg1, tseg2, sjw, no_samp, 0)
                canlib.canBusOn(self._write_handle.get_canlib_handle())
            canlib.canSetDriverMode(self._write_handle.get_canlib_handle(),
              driver_mode, canstat.canTRANSCEIVER_RESNET_NA)
        self.driver_mode = driver_mode
        self.rx_queue = Queue.Queue(0)
        self.timer_offset = self._read_handle.read_timer()
        self._read_handle.add_listener(self)

    def read(self):
        try:
            return self.rx_queue.get_nowait()
        except Queue.Empty:
            BUS_CLASS_LOGGER.debug("Bus '%s': No messages available" %
              self.name)
            return None

    def add_listener(self, listener):
        self._read_handle.add_listener(listener)
        listener.set_write_bus(self)

    def write(self, msg):
        BUS_CLASS_LOGGER.debug("Bus '%s': Entering Write()" % self.name)
        if self.driver_mode != canlib.canDRIVER_SILENT:
            BUS_CLASS_LOGGER.debug("Bus '%s': writing message %s" %
              (self.name, msg))
            self._write_handle.write(msg)
        BUS_CLASS_LOGGER.debug("Bus '%s': Leaving Write()" % self.name)

    def read_timer(self):
        return (float(self._read_handle.read_timer() - self.timer_offset) /
          TIMER_TICKS_PER_SECOND)

    def on_message_received(self, msg):
        self.rx_queue.put_nowait(msg)

    def _get_device_description(self):#pragma: no cover
        return self._read_handle.get_device_description()

    def _get_device_manufacturer_name(self):#pragma: no cover
        return self._read_handle.get_device_manufacturer_name()

    def _get_device_firmware_version(self):#pragma: no cover
        return self._read_handle.get_device_firmware_version()

    def _get_device_hardware_version(self):#pragma: no cover
        return self._read_handle.get_device_hardware_version()

    def _get_device_card_serial(self):#pragma: no cover
        return self._read_handle.get_device_card_serial()

    def _get_device_transceiver_serial(self):#pragma: no cover
        return self._read_handle.get_device_transceiver_serial()

    def _get_device_card_number(self):#pragma: no cover
        return self._read_handle.get_device_card_number()

    def _get_device_channel_on_card(self):#pragma: no cover
        return self._read_handle.get_device_channel_on_card()

    def _get_device_transceiver_type(self):#pragma: no cover
        return self._read_handle.get_device_transceiver_type()

    def get_channel_info(self):#pragma: no cover
        return ChannelInfo(self._read_handle.channel,
                           self._get_device_description(),
                           self._get_device_manufacturer_name(),
                           self._get_device_firmware_version(),
                           self._get_device_hardware_version(),
                           self._get_device_card_serial(),
                           self._get_device_transceiver_serial(),
                           self._get_device_transceiver_type(),
                           self._get_device_card_number(),
                           self._get_device_channel_on_card())

    def get_statistics(self):
        return self._read_handle.get_statistics()

@atexit.register
def _cleanup():#pragma: no cover
    CAN_MODULE_LOGGER.info("Waiting for receive callbacks to complete...")
    for _handle in READ_HANDLE_REGISTRY.values():
        CAN_MODULE_LOGGER.info("\tHandle %d..." % _handle.get_canlib_handle())
        _handle.receiveCallbackEnabled = False
        while _handle.reading:
            pass
        CAN_MODULE_LOGGER.info("\tOK")
    CAN_MODULE_LOGGER.info("Waiting for transmit callbacks to complete...")
    for _handle in WRITE_HANDLE_REGISTRY.values():
        CAN_MODULE_LOGGER.info("\tHandle %d..." % _handle.get_canlib_handle())
        _handle.transmitCallbackEnabled = False
        while _handle.writing:
            pass
        CAN_MODULE_LOGGER.info("\tOK")
    CAN_MODULE_LOGGER.info("Clearing receive callbacks...")
    for _handle_number in READ_HANDLE_REGISTRY.keys():
        _handle = READ_HANDLE_REGISTRY[_handle_number]
        CAN_MODULE_LOGGER.info("\tHandle %d" % _handle.get_canlib_handle())
        canlib.kvSetNotifyCallback(_handle_number, None, None, 0)
        canlib.canFlushReceiveQueue(_handle_number)
    CAN_MODULE_LOGGER.info("Clearing transmit callbacks...")
    for _handle_number in WRITE_HANDLE_REGISTRY.keys():
        _handle = READ_HANDLE_REGISTRY[_handle_number]
        CAN_MODULE_LOGGER.info("\tHandle %d" % _handle.get_canlib_handle())
        canlib.kvSetNotifyCallback(_handle_number, None, None, 0)
        canlib.canFlushTransmitQueue(_handle_number)
