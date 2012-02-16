"""
CAN.py: the core of pycanlib - contains implementations of all
the major classes in the library, which form abstractions of the
functionality provided by CANLIB.

Copyright (C) 2010 Dynamic Controls
"""
from pycanlib import canlib, canstat

import logging
import cPickle as pickle
import ctypes
import datetime
import os
import platform
import Queue as queue
import string
import sys
import threading
import time
import types

log = logging.getLogger('CAN')

log.debug("Loading CAN.py")

try:
    import hgversionutils
    __version__ = hgversionutils.get_version_number(os.path.join(os.path.dirname(__file__), ".."))
except ImportError:
    with open(os.path.join(os.path.dirname(__file__), "version.txt"), "r") as _version_file:
        __version__ = _version_file.readline().replace("\n", "")

log.debug("Initializing CAN library")
canlib.canInitializeLibrary()
log.debug("CAN library initialized")

ID_TYPE_EXTENDED = True
ID_TYPE_STANDARD = False

ID_TYPE_29_BIT = ID_TYPE_EXTENDED
ID_TYPE_11_BIT = ID_TYPE_STANDARD

REMOTE_FRAME = True
DATA_FRAME = False
WAKEUP_MSG = True
ERROR_FRAME = True

DRIVER_MODE_SILENT = False
DRIVER_MODE_NORMAL = (not DRIVER_MODE_SILENT)

STD_ACCEPTANCE_MASK_ALL_BITS = (2**11 - 1)
MAX_11_BIT_ID = STD_ACCEPTANCE_MASK_ALL_BITS

EXT_ACCEPTANCE_MASK_ALL_BITS = (2**29 - 1)
MAX_29_BIT_ID = EXT_ACCEPTANCE_MASK_ALL_BITS

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

def get_host_machine_info():
    log.debug("Getting host machine info")
    if sys.platform == "win32":
        machine_name = "%s" % os.getenv("COMPUTERNAME")
    else:
        machine_name = "%s" % os.getenv("HOSTNAME")
    platform_info = platform.platform()
    python_version = sys.version[:sys.version.index(" ")]
    return MachineInfo(machine_name, python_version, platform_info)

def get_canlib_version():
    if sys.platform == "win32":
        _version = canlib.canGetVersionEx(canlib.canVERSION_CANLIB32_PRODVER32)
        _major = ((_version & 0xFFFF0000) >> 16)
        _minor = ((_version & 0x0000FF00) >> 8)
        _letter = (_version & 0x000000FF)
        if _letter == 0:
            return "%d.%d" % (_major, _minor)
        else:
            return "%d.%d%s" % (_major, _minor, "%c" % _letter)
    else:
        _version = canlib.canGetVersion()
        return "%d.%d" % (((_version & 0xFF00) >> 8), (_version & 0x00FF))

def get_channel_info(channel):
    _device_description_buffer = ctypes.create_string_buffer(MAX_DEVICE_DESCR_LENGTH)
    _manufacturer_name_buffer = ctypes.create_string_buffer(MAX_MANUFACTURER_NAME_LENGTH)
    _firmware_version_buffer = FW_VERSION_ARRAY()
    _hardware_version_buffer = HW_VERSION_ARRAY()
    _card_serial_number_buffer = CARD_SN_ARRAY()
    _transceiver_serial_number_buffer = TRANS_SN_ARRAY()
    _transceiver_type_buffer = ctypes.c_ulong(0)
    _card_number_buffer = ctypes.c_ulong(0)
    _channel_on_card_buffer = ctypes.c_ulong(0)
    canlib.canGetChannelData(channel, canlib.canCHANNELDATA_CARD_FIRMWARE_REV, ctypes.byref(_firmware_version_buffer), ctypes.c_size_t(MAX_FW_VERSION_LENGTH))
    canlib.canGetChannelData(channel, canlib.canCHANNELDATA_CHAN_NO_ON_CARD, ctypes.byref(_channel_on_card_buffer), ctypes.c_size_t(4))
    canlib.canGetChannelData(channel, canlib.canCHANNELDATA_CARD_SERIAL_NO, ctypes.byref(_card_serial_number_buffer), ctypes.c_size_t(MAX_CARD_SN_LENGTH))
    #HACK
    if sys.platform == "win32":
        canlib.canGetChannelData(channel, canlib.canCHANNELDATA_DEVDESCR_ASCII, ctypes.byref(_device_description_buffer), ctypes.c_size_t(MAX_DEVICE_DESCR_LENGTH))
        canlib.canGetChannelData(channel, canlib.canCHANNELDATA_MFGNAME_ASCII, ctypes.byref(_manufacturer_name_buffer), ctypes.c_size_t(MAX_MANUFACTURER_NAME_LENGTH))
        canlib.canGetChannelData(channel, canlib.canCHANNELDATA_CARD_HARDWARE_REV, ctypes.byref(_hardware_version_buffer), ctypes.c_size_t(MAX_HW_VERSION_LENGTH))
        canlib.canGetChannelData(channel, canlib.canCHANNELDATA_TRANS_SERIAL_NO, ctypes.byref(_transceiver_serial_number_buffer), ctypes.c_size_t(MAX_TRANS_SN_LENGTH))
        canlib.canGetChannelData(channel, canlib.canCHANNELDATA_TRANS_TYPE, ctypes.byref(_transceiver_type_buffer), ctypes.c_size_t(4))
        canlib.canGetChannelData(channel, canlib.canCHANNELDATA_CARD_NUMBER, ctypes.byref(_card_number_buffer), ctypes.c_size_t(4))
    else:
#        sys.stderr.write("WARNING: not all channel information is not available on this system, as canGetChannelInfo is not implemented completely; canCHANNELDATA_DEVDESCR_ASCII has been approximated by canCHANNELDATA_CHANNEL_NAME\n")
        canlib.canGetChannelData(channel, canlib.canCHANNELDATA_CHANNEL_NAME, ctypes.byref(_device_description_buffer), ctypes.c_size_t(MAX_DEVICE_DESCR_LENGTH))
        _manufacturer_name_buffer.value = "<unimplemented>"
    #/HACK
    _firmware_version_number = []
    for i in [6, 4, 0, 2]:
        _firmware_version_number.append((_firmware_version_buffer[i + 1] << 8) + _firmware_version_buffer[i])
    _hardware_version_number = []
    for i in [2, 0]:
        _hardware_version_number.append((_hardware_version_buffer[i + 1] << 8) + _hardware_version_buffer[i])
    _card_serial_number = 0
    for i in xrange(len(_card_serial_number_buffer)):
        _card_serial_number += (_card_serial_number_buffer[i] << (8 * i))
    _transceiver_serial_number = 0
    for i in xrange(len(_transceiver_serial_number_buffer)):
        _transceiver_serial_number += (_transceiver_serial_number_buffer[i] << (8 * i))
    return ChannelInfo(channel, _device_description_buffer.value, _manufacturer_name_buffer.value, ".".join("%d" % _num for _num in _firmware_version_number), ".".join("%d" % _num for _num in _hardware_version_number), _card_serial_number, _transceiver_serial_number, _transceiver_type_buffer.value, _card_number_buffer.value, _channel_on_card_buffer.value)

class ChannelNotFoundError(Exception):
    pass

class Message(object):

    def __init__(self, timestamp=0.0, is_remote_frame=False, 
                 id_type=ID_TYPE_11_BIT, is_wakeup=False, 
                 is_error_frame=False, arbitration_id=0, 
                 data=None, dlc=0, info_strings=None):
        self.timestamp = timestamp
        self.id_type = id_type
        self.is_remote_frame = is_remote_frame
        self.is_wakeup = is_wakeup
        self.is_error_frame = is_error_frame
        self.arbitration_id = arbitration_id
        if data is None:
            self.data = []
        else:
            self.data = data
        self.dlc = dlc
        if info_strings is None:
            self.info_strings = []
        else:
            self.info_strings = info_strings
            
        log.debug('Created new message {}'.format(self))

    @property
    def timestamp(self):
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, value):
        self.__timestamp = value

    @property
    def is_remote_frame(self):
        if self.flags & canstat.canMSG_RTR:
            return REMOTE_FRAME
        else:
            return not REMOTE_FRAME

    @is_remote_frame.setter
    def is_remote_frame(self, value):
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
        _new_flags = self.flags & (0xFFFF - (canstat.canMSG_STD | canstat.canMSG_EXT))
        if value == ID_TYPE_EXTENDED:
            self.flags = (_new_flags | canstat.canMSG_EXT)
        else:
            self.flags = (_new_flags | canstat.canMSG_STD)

    @property
    def is_wakeup(self):
        if self.flags & canstat.canMSG_WAKEUP:
            return WAKEUP_MSG
        else:
            return not WAKEUP_MSG

    @is_wakeup.setter
    def is_wakeup(self, value):
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
        self.flags &= (0xFFFF - canstat.canMSG_ERROR_FRAME)
        if value == ERROR_FRAME:
            self.flags |= canstat.canMSG_ERROR_FRAME

    @property
    def arbitration_id(self):
        return self.__arbitration_id

    @arbitration_id.setter
    def arbitration_id(self, value):
        self.__arbitration_id = value

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = value

    @property
    def dlc(self):
        return self.__dlc

    @dlc.setter
    def dlc(self, value):
        self.__dlc = value

    @property
    def flags(self):
        try:
            return self.__flags
        except AttributeError:
            return 0

    @flags.setter
    def flags(self, value):
        self.__flags = value

    @property
    def info_strings(self):
        return self.__info_strings

    @info_strings.setter
    def info_strings(self, value):
        self.__info_strings = value

    def check_equality(self, other, fields):
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
            _arbitration_id_string = "%.8x" % self.arbitration_id
        else:
            _arbitration_id_string = "%.4x" % self.arbitration_id
        _field_strings.append(_arbitration_id_string.rjust(8, " "))
        _field_strings.append("%.4x" % self.flags)
        _field_strings.append("%d" % self.dlc)
        _data_strings = []
        if self.data != None:
            for byte in self.data:
                _data_strings.append("%.2x" % byte)
        if len(_data_strings) > 0:
            _field_strings.append(" ".join(_data_strings).ljust(24, " "))
        else:
            _field_strings.append(" "*24)
        _current_length = len("    ".join(_field_strings))
        if len(self.info_strings) > 0:
            _field_strings.append(("\n" + (" " * (_current_length + 4))).join(self.info_strings))
        return "    ".join(_field_strings).strip()

class TimestampMessage(object):
    def __init__(self, timestamp=0.0, info_strings=None):
        self.timestamp = timestamp
        if info_strings is not None:
            self.info_strings = info_strings
        else:
            self.info_strings = []

    @property
    def timestamp(self):
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, value):
        self.__timestamp = float(value)

    @property
    def info_strings(self):
        return self.__info_strings

    @info_strings.setter
    def info_strings(self, value):
        self.__info_strings = value

    def check_equality(self, other, fields):
        return False

    def __str__(self):
        if len(self.info_strings) > 0:
            retval = "%15.6f    " % self.timestamp
            retval += ("\n"+" "*len("%15.6f    " % self.timestamp)).join(self.info_strings)
        else:
            retval = ""
        return retval

class MessageList(object):

    def __init__(self, messages=None, filter_criteria="True", name="default"):
        if messages is None: messages = []
        self.messages = messages
        self.filter_criteria = filter_criteria
        self.name = name

    def __iter__(self):
        return (m for m in self.messages)

    def __getitem__(self, index):
        return self.messages[index]

    def __len__(self):
        return len(self.messages)

    @property
    def start_timestamp(self):
        if len(self.messages) > 0:
            return self.messages[0].timestamp
        else:
            return 0

    @property
    def end_timestamp(self):
        if len(self.messages) > 0:
            return self.messages[-1].timestamp
        else:
            return 0

    @property
    def filtered_messages(self):
        if self.filter_criteria != "True":
            _filter_criteria = self.filter_criteria.replace("CAN.", "")
            retval = []
            for message in self.messages:
                try:
                    if eval(_filter_criteria):
                        retval.append(message)
                except AttributeError:
                    pass
            return retval
        else:
            return self.messages

    def __str__(self):
        retval = "-"*len("Message List '%s'" % self.name)
        retval += "\nMessage List '%s'\n" % self.name
        retval += "-"*len("Message List '%s'" % self.name)
        retval += "\n"
        if self.filter_criteria == "True":
            retval += "Applied filters: None\n"
        else:
            retval += "Applied filters: %s\n" % self.filter_criteria
        retval += "Start timestamp = %f\n" % self.start_timestamp
        retval += "End timestamp = %f\n" % self.end_timestamp
        for msg in self.messages:
            retval += "%s\n" % msg
        return retval

class Log(object):
    """
    A Log object contains information about the CAN channel, the machine information
    and contains a record of the messages and errors.
    """

    def __init__(self, log_info, channel_info, machine_info, message_lists=None):
        self.log_info = log_info
        self.channel_info = channel_info
        self.machine_info = machine_info
        if message_lists is None: message_lists = []
        self.message_lists = message_lists

    def __str__(self):
        retval = ""
        retval += "%s\n" % self.machine_info
        retval += "%s\n" % self.log_info
        if self.channel_info != None:
            retval += "%s\n" % self.channel_info
        for _list in self.message_lists:
            retval += "%s" % _list
        return retval

    def write_to_file(self, filename, dat=False, csv=False, txt=True):
        """
        Export this Log to a file. 
        
        Will use format of extension according to
            .csv    create a csv file
            .txt    create a text file
            .dat    create a pickle dump of this object
        
        The export type can also be explicitly be given in this method's
        parameters - only the first one will be use.
            
        """
        if filename is None:
            path = os.path.expanduser("~/CAN_bus_logs/")
            name = self.log_info.original_file_name
            filename = os.path.join(path, name)
        
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        
        _, ext = os.path.splitext(filename)
        
        if dat or ext == '.dat':
            with open(filename, "wb") as bin_file:
                pickle.dump(self, bin_file)
        
        elif csv or ext == '.csv':
            from csv import writer
            with open(filename, "wb") as csv_file:
                csv_writer = writer(csv_file)
                for message_list in self.message_lists:
                    csv_writer.writerows(str(m).split() for m in message_list)

        elif txt or ext == '.txt':
            with open(filename, "wt") as txt_file:
                txt_file.write("%s\n" % self)
        
        
class MachineInfo(object):

    def __init__(self, machine_name="", python_version="", platform_info=""):
        self.machine_name = machine_name
        self.python_version = python_version
        self.platform_info = platform_info
        self.canlib_version = get_canlib_version()
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
        self.__machine_name = value

    @property
    def python_version(self):
        return self.__python_version

    @python_version.setter
    def python_version(self, value):
        self.__python_version = value

    @property
    def platform_info(self):
        return self.__platform_info

    @platform_info.setter
    def platform_info(self, value):
        self.__platform_info = value

    @property
    def canlib_version(self):
        return self.__canlib_version

    @canlib_version.setter
    def canlib_version(self, value):
        self.__canlib_version = value

    @property
    def module_versions(self):
        return self.__module_versions

    @module_versions.setter
    def module_versions(self, value):
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

class ChannelInfo(object):

    def __init__(self, channel, device_description, manufacturer_name, firmware_version, hardware_version, card_serial, transceiver_serial, transceiver_type, card_number, channel_on_card):
        self.channel = channel
        self.device_description = device_description
        self.manufacturer_name = manufacturer_name
        self.firmware_version = firmware_version
        self.hardware_version = hardware_version
        self.card_serial = card_serial
        self.transceiver_serial = transceiver_serial
        self.transceiver_type = transceiver_type
        self.card_number = card_number
        self.channel_on_card = channel_on_card

    @property
    def channel(self):
        return self.__channel

    @channel.setter
    def channel(self, value):
        self.__channel = value

    @property
    def device_description(self):
        return self.__device_description

    @device_description.setter
    def device_description(self, value):
        self.__device_description = value

    @property
    def manufacturer_name(self):
        return self.__manufacturer_name

    @manufacturer_name.setter
    def manufacturer_name(self, value):
        self.__manufacturer_name = value

    @property
    def firmware_version(self):
        return self.__firmware_version

    @firmware_version.setter
    def firmware_version(self, value):
        self.__firmware_version = value

    @property
    def hardware_version(self):
        return self.__hardware_version

    @hardware_version.setter
    def hardware_version(self, value):
        self.__hardware_version = value

    @property
    def card_serial(self):
        return self.__card_serial

    @card_serial.setter
    def card_serial(self, value):
        self.__card_serial = value

    @property
    def transceiver_serial(self):
        return self.__transceiver_serial

    @transceiver_serial.setter
    def transceiver_serial(self, value):
        self.__transceiver_serial = value

    @property
    def transceiver_type(self):
        return self.__transceiver_type

    @transceiver_type.setter
    def transceiver_type(self, value):
        self.__transceiver_type = value

    @property
    def card_number(self):
        return self.__card_number

    @card_number.setter
    def card_number(self, value):
        self.__card_number = value

    @property
    def channel_on_card(self):
        return self.__channel_on_card

    @channel_on_card.setter
    def channel_on_card(self, value):
        self.__channel_on_card = value

    def __str__(self):
        retval = "-"*len("Channel Info")
        retval += "\nChannel Info\n"
        retval += "-"*len("Channel Info")
        retval += "\n"
        retval += "CANLIB channel: %s\n" % self.channel
        retval += "Device Description: '%s'\n" % self.device_description
        retval += "Manufacturer Name: '%s'\n" % self.manufacturer_name
        retval += "Firmware version: %s\n" % self.firmware_version
        retval += "Hardware version: %s\n" % self.hardware_version
        retval += "Card serial number: %s\n" % self.card_serial
        retval += "Transceiver type: %d (%s)\n" % (self.transceiver_type, canlib.lookup_transceiver_type(self.transceiver_type))
        retval += "Transceiver serial number: %s\n" % self.transceiver_serial
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

class Bus(object):

    def __init__(self, channel, bitrate, tseg1, tseg2, sjw, no_samp, driver_mode=DRIVER_MODE_NORMAL, single_handle=False):
        log.debug('Initialising bus instance')
        self.single_handle = single_handle
        num_channels = ctypes.c_int(0)
        canlib.canGetNumberOfChannels(ctypes.byref(num_channels))
        num_channels = int(num_channels.value)
        log.debug('Found %d available channels' % num_channels)

        if type(channel) == str:
            _channel = get_canlib_channel_from_url(channel)
            if _channel is None:
                raise ChannelNotFoundError(channel)
        else:
            _channel = channel

        self.channel_info = get_channel_info(_channel)
        log.info('Channel information:\n%s' % str(self.channel_info))

        self.writing_event = threading.Event()
        self.done_writing = threading.Condition()

        log.debug('Creating read handle to bus channel: %s' % _channel)
        self.__read_handle = canlib.canOpenChannel(_channel, canlib.canOPEN_ACCEPT_VIRTUAL)
        canlib.canIoCtl(self.__read_handle, canlib.canIOCTL_SET_TIMER_SCALE, ctypes.byref(ctypes.c_long(1)), 4)
        canlib.canSetBusParams(self.__read_handle, bitrate, tseg1, tseg2, sjw, no_samp, 0)

        
        '''
        Bit of a hack, on linux using kvvirtualcan module it seems you must read
        and write on separate channels of the same bus.
        '''
        
        if platform.system() == "Linux" and "virtual" in str(self.channel_info).lower():
            log.debug('Detected virtual channel on linux')
            for chan in range(num_channels):
                c = (chan + 1) % num_channels
                channel_info = get_channel_info(c)
                if "virtual" in str(channel_info).lower() and c != _channel:
                    log.info('Creating seperate TX handle on channel: %s' % c)
                    self.__write_handle = canlib.canOpenChannel(c, canlib.canOPEN_ACCEPT_VIRTUAL)
                    log.info('Going bus on RX handle')
                    canlib.canBusOn(self.__read_handle)
                    break

        if self.single_handle:
            log.debug("We don't require separate handles to the bus")
            self.__write_handle = self.__read_handle
        else:
            log.debug('Creating seperate handle for TX on channel: %s' % _channel)
            self.__write_handle = canlib.canOpenChannel(_channel, canlib.canOPEN_ACCEPT_VIRTUAL)
            canlib.canBusOn(self.__read_handle)

        __driver_mode = canlib.canDRIVER_SILENT if driver_mode == DRIVER_MODE_SILENT else canlib.canDRIVER_NORMAL
        
        canlib.canSetBusOutputControl(self.__write_handle, __driver_mode)
        log.debug('Going bus on TX handle')
        canlib.canBusOn(self.__write_handle)
        
        self.__listeners = []
        self.__tx_queue = queue.Queue(0)
        self.__read_thread = threading.Thread(target=self.__read_process)
        self.__write_thread = threading.Thread(target=self.__write_process)
        self.__read_thread.daemon = True
        self.__write_thread.daemon = True
        self.__threads_running = True
        self.__read_thread.start()
        self.__write_thread.start()
        self.timer_offset = None

    @property
    def listeners(self):
        return self.__listeners

    @listeners.setter
    def listeners(self, value):
        self.__listeners = value
    
    def __convert_timestamp(self, value):
        if not hasattr(self, 'timer_offset') or self.timer_offset is None: #Use the current value if the offset has not been set yet
            self.timer_offset = value
        
        if value < self.timer_offset: # Check for overflow
            MAX_32BIT = 0xFFFFFFFF # The maximum value that the timer reaches on a 32-bit machine
            MAX_64BIT = 0x9FFFFFFFF # The maximum value that the timer reaches on a 64-bit machine
            if ctypes.sizeof(ctypes.c_long) == 8:
                value += MAX_64BIT
            elif ctypes.sizeof(ctypes.c_long) == 4:
                value += MAX_32BIT
            else:
                assert False, 'Unknown platform. Expected a long to be 4 or 8 bytes long but it was %i bytes.' % ctypes.sizeof(ctypes.c_long)
            assert value > self.timer_offset, 'CAN Timestamp overflowed. The timer offset was ' + str(self.timer_offset) 
        
        return (float(value - self.timer_offset) / 1000000) # Convert from us into seconds

    def __read_process(self):
        """
        The consumer thread.
        Note: gets overwritten by J1939.Bus
        """
        log.info('Read process starting')
        while self.__threads_running:
            rx_msg = self.__get_message()
            
            if rx_msg is not None:

                for listener in self.listeners:
                    listener.on_message_received(rx_msg)

    def __get_message(self):
        '''
        Read a message from kvaiser device.
        
        In single handle mode this blocks the sending of messages for up to 1ms
        before releasing the lock.
        '''
        arb_id = ctypes.c_long(0)
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        timestamp = ctypes.c_ulong(0)
        
        if self.single_handle:
            
            self.done_writing.acquire()
            
            while self.writing_event.is_set():
                # releases the underlying lock, and then blocks until it is awakened 
                # by a notify() from the tx thread. Once awakened it re-acquires the lock
                self.done_writing.wait()

        #log.debug('Reading for 1ms on handle: %s' % self.__read_handle)
        status = canlib.canReadWait(self.__read_handle, 
                                     ctypes.byref(arb_id), 
                                     ctypes.byref(data), 
                                     ctypes.byref(dlc), 
                                     ctypes.byref(flags), 
                                     ctypes.byref(timestamp),
                                     1  # This is a 1 ms blocking read
                                     )
        if self.single_handle:
            # Don't want to keep the done_writing condition's Lock
            self.done_writing.release()

        
        if status.value == canstat.canOK:
            #log.log(9, 'read complete -> status OK')
            data_array = map(ord, data)
            if int(flags.value) & canstat.canMSG_EXT:
                id_type = ID_TYPE_EXTENDED
            else:
                id_type = ID_TYPE_STANDARD
            msg_timestamp = self.__convert_timestamp(timestamp.value)
            rx_msg = Message(arbitration_id=arb_id.value, 
                             data=data_array[:dlc.value],
                             dlc=int(dlc.value), 
                             id_type=id_type, 
                             timestamp=msg_timestamp)
            rx_msg.flags = int(flags.value) & canstat.canMSG_MASK
            #log.info('Got message: %s' % rx_msg)
            return rx_msg
        else:
            #log.debug('read complete -> status not okay')
            return TimestampMessage(timestamp=0)

    def __write_process(self):
        while self.__threads_running:
            tx_msg = None
            have_lock = False
            try:
                if self.single_handle:
                    if not self.__tx_queue.empty():
                        # Tell the rx thread to give up the can handle
                        # because we have a message to write to the bus
                        self.writing_event.set()
                        # Acquire a lock that the rx thread has started waiting on
                        self.done_writing.acquire()
                        have_lock = True
                    else:
                        raise queue.Empty('')
                    
                while not self.__tx_queue.empty():
                    tx_msg = self.__tx_queue.get(timeout=0.05)
                    if tx_msg is not None:
                        self.__put_message(tx_msg)
                        
            except queue.Empty:
                pass
            if self.single_handle and have_lock:
                self.writing_event.clear()
                # Tell the rx thread it can start again
                self.done_writing.notify()
                self.done_writing.release()
                have_lock = False
            

    def __put_message(self, tx_msg):
        canlib.canWriteWait(self.__write_handle,
                            tx_msg.arbitration_id,
                            "".join([("%c" % byte) for byte in tx_msg.data]),
                             tx_msg.dlc,
                             tx_msg.flags,
                             5)

    def write_for_period(self, messageGapInSeconds, totalPeriodInSeconds, message):
        _startTime = time.time()
        while (time.time() - _startTime) < totalPeriodInSeconds:
            self.write(message)
            
            _startOfPause = time.time()
            while (time.time() - _startOfPause) < messageGapInSeconds and (time.time() - _startTime) < totalPeriodInSeconds:
                time.sleep(0.001)

    def write(self, msg):
        ''''
        :param msg: A Message object to write to bus.
        '''
        self.__tx_queue.put_nowait(msg)

    def shutdown(self):
        self.__threads_running = False
        canlib.canBusOff(self.__write_handle)
        canlib.canClose(self.__write_handle)

def get_canlib_channel_from_url(url):
    (_type, _remainder) = url.split("://")
    (_serial, _channel) = _remainder.split("/")
    _serial = int(_serial)
    _channel = int(_channel)
    _num_channels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_num_channels))
    for channel in xrange(_num_channels.value):
        _bus = Bus(channel=channel, bitrate=1000000, tseg1=4, tseg2=3, sjw=1, no_samp=1)
        if (_type == "leaf" and (string.find(string.lower(_bus.channel_info.device_description), "leaf") != -1)) or (_type == "usbcanii" and ((string.find(string.lower(_bus.channel_info.device_description), "usbcan ii") != -1) or (string.find(string.lower(_bus.channel_info.device_description), "usbcanii") != -1))):
            if (_bus.channel_info.card_serial, _bus.channel_info.channel_on_card) == (_serial, _channel):
                _bus.shutdown()
                return channel
        _bus.shutdown()

class Listener(object):
    def on_message_received(self, msg):
        raise NotImplementedError("%s has not implemented on_message_received" % self.__class__.__name__)

class BufferedReader(Listener):

    def __init__(self):
        self.__buffer = queue.Queue(0)

    def on_message_received(self, msg):
        self.__buffer.put_nowait(msg)

    def get_message(self):
        try:
            return self.__buffer.get(timeout=0.5)
        except queue.Empty:
            return None

class AcceptanceFilter(Listener):

    def __init__(self, std_acceptance_code=0, ext_acceptance_code=0, std_acceptance_mask=STD_ACCEPTANCE_MASK_ALL_BITS, ext_acceptance_mask=EXT_ACCEPTANCE_MASK_ALL_BITS):
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
        self.__std_acceptance_code = value

    @property
    def std_acceptance_mask(self):
        return self.__std_acceptance_mask

    @std_acceptance_mask.setter
    def std_acceptance_mask(self, value):
        self.__std_acceptance_mask = value

    @property
    def ext_acceptance_code(self):
        return self.__ext_acceptance_code

    @ext_acceptance_code.setter
    def ext_acceptance_code(self, value):
        self.__ext_acceptance_code = value

    @property
    def ext_acceptance_mask(self):
        return self.__ext_acceptance_mask

    @ext_acceptance_mask.setter
    def ext_acceptance_mask(self, value):
        self.__ext_acceptance_mask = value

    def on_message_received(self, msg):
        _filtered_message = self.filter_message(msg)
        if _filtered_message != None:
            for _listener in self.__listeners:
                _listener.on_message_received(msg)

    def add_listener(self, listener):
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
        if ((msg.arbitration_id ^ _code) & _mask) == 0:
            return msg
        else:
            return None

class MessagePrinter(Listener):
    def on_message_received(self, msg):
        print msg
