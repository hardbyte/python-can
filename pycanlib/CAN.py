"""
CAN.py: the core of pycanlib - contains implementations of all
the major classes in the library, which form abstractions of the
functionality provided by CANLIB.

Copyright (C) 2010 Dynamic Controls
"""

import ctypes
import logging
import pickle
import datetime
import ctypes
import os
import platform
try:
    import queue
except ImportError:
    import Queue as queue
import string
import sys
import threading
import time
import types
import argparse
import multiprocessing

from pycanlib import socketcanlib

# This canMSG_EXT variable was the only variable being used from the file canstat.py, 
# which has been removed
canMSG_EXT = 0x0004

CAN_RAW =       1
CAN_BCM =       2
MSK_ARBID =     0x1FFFFFFF
MSK_FLAGS =     0xE0000000

#Extended flag is in the same place for pycan and socketcan
EXTFLG =        0x0004

SKT_ERRFLG  =   0x0001
SKT_RTRFLG  =   0x0002

PYCAN_ERRFLG =  0x0020
PYCAN_STDFLG =  0x0002
PYCAN_RTRFLG =  0x0001

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('CAN')

log.debug("Loading CAN.py")

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

# Sets the level of messages that are displayed. Default is 'Warning'
def set_logging_level(level):
    if level == 2:
        log.setLevel(logging.DEBUG)
    elif level == 1:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARNING)

def get_host_machine_info():
    log.debug("Getting host machine info")
    if sys.platform == "win32":
        machine_name = "%s" % os.getenv("COMPUTERNAME")
    else:
        machine_name = "%s" % os.getenv("HOSTNAME")
    platform_info = platform.platform()
    python_version = sys.version[:sys.version.index(" ")]
    return MachineInfo(machine_name, python_version, platform_info)

class ChannelNotFoundError(Exception):
    pass


class Message (object) :
    def __init__(self, timestamp=0, is_remote_frame=False, id_type=ID_TYPE_11_BIT,
                 is_wakeup=False, is_error_frame=False, arbitration_id=0, data=None, 
                 dlc=0, info_strings=None):
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
    
    def __str__(self):
        _field_strings = []
        _field_strings.append("%15.6f" % self.timestamp)
        if self.flags & canMSG_EXT:
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
        for mlist in self.message_lists:
            retval += "%s" % mlist
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

    def __str__(self):
        retval = "-" * len("Machine Info")
        retval += "\nMachine Info\n"
        retval += "-" * len("Machine Info")
        retval += "\n"
        retval += "Machine name: %s\n" % self.machine_name
        retval += "Python: %s\n" % self.python_version
        retval += "OS: %s\n" % self.platform_info
        #~ retval += "CANLIB: %s\n" % self.canlib_version
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
    """The CAN Bus Object."""
    channel_info = "socketcan channel"

    def __init__(self,
                 channel,
                 bitrate,
                 tseg1,
                 tseg2,
                 sjw,
                 no_samp,
                 driver_mode=DRIVER_MODE_NORMAL,
                 single_handle=False):
        """
        @param channel
            The Channel id to create this bus with.
        @param bitrate
            Bitrate of channel in bit/s
        @param driver_mode
            Silent or normal.
        @param single_handle
            If True the bus is created with one handle shared between both writing and reading.
        
        TODO - rename these to be clearer, document what they do.
        @param tseg1
        @param tseg2
        @param sjw
        @param no_samp
        """    

        self.socketID = socketcanlib.createSocket(CAN_RAW)
        socketcanlib.bindSocket(self.socketID)
        
        # TODO: setBusParams
        #socketcanlib.setBusParams(self.socketID, bitrate, tseg1, tseg2, sjw, no_samp)
        
        self.listeners = []
        
        self.__read_thread = threading.Thread(target=self.__read_process)
        self.__read_thread.daemon = True
        
        # TODO: add writing capability back!
        #self.__tx_queue = multiprocessing.Queue(0)
        #self.__write_thread = threading.Thread(target=self.__write_process)
        #self.__write_thread.daemon = True

        self.__threads_running = True
        log.debug("starting the read process thread")
        self.__read_thread.start()
        #self.__write_thread.start()
        
        # Used to zero the timestamps from the first message
        self.timer_offset = None
        
        '''
        Approximate offset between time.time() and CAN timestamps (~2ms accuracy)
        There will always be some lag between when the message is on the bus to when it reaches python
        Allow messages to be on the bus for a while before reading this value so it has a chance to correct itself'''
        self.pc_time_offset = None

    def __convert_timestamp (self, value):
        if self.timer_offset is None:
            # Use the current value if the offset has not been set yet
            self.timer_offset = value
            self.pc_time_offset = time.time()
            
        timestamp = (float(value - self.timer_offset) / 1000000) # Convert from us into seconds
        lag = (time.time() - self.pc_time_offset) - timestamp 
        if lag < 0: # If we see a timestamp that is quicker than the ever before, update the offset
            self.pc_time_offset += lag
        return timestamp
        
    def __get_message(self):
        
        rx_msg = Message()

        log.debug("I'm about to try to get a msg")

        # todo error checking...?
        packet = socketcanlib.capturePacket(self.socketID)

        log.debug("I've got a message")

        arbitration_id = packet['CAN ID'] & MSK_ARBID

        # Flags: EXT, RTR, ERR
        flags = (packet['CAN ID'] & MSK_FLAGS) >> 29

        # To keep flags consistent with pycanlib, their positions need to be switched around
        flags = (flags | PYCAN_ERRFLG) & ~(SKT_ERRFLG) if flags & SKT_ERRFLG else flags 
        flags = (flags | PYCAN_RTRFLG) & ~(SKT_RTRFLG) if flags & SKT_RTRFLG else flags
        flags = (flags | PYCAN_STDFLG) & ~(EXTFLG) if not(flags & EXTFLG) else flags

        if flags & EXTFLG:
            rx_msg.id_type = ID_TYPE_EXTENDED
            log.debug("CAN: Extended")
        else:
            rx_msg.id_type = ID_TYPE_STANDARD
            log.debug("CAN: Standard")

        rx_msg.arbitration_id = arbitration_id
        rx_msg.dlc = packet['DLC']
        rx_msg.flags = flags
        rx_msg.data = packet['Data']
        rx_msg.timestamp = self.__convert_timestamp(packet['Timestamp'])
        
        return rx_msg

    def __read_process(self):
            while(self.__threads_running):
                rx_msg = self.__get_message()
                log.debug("Got msg: %s" % rx_msg)
                for listener in self.listeners:
                    listener.on_message_received(rx_msg)
    
    def shutdown(self):
        self.__threads_running = False
        
        # TODO: any shutdown stuff for the socketcanlib?

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

class MessagePrinter(Listener):
    def on_message_received(self, msg):
        print (msg)
