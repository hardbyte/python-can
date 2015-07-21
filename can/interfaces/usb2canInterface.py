#this interface is for windows only, otherwise use socketCAN

import logging
import ctypes



logger = logging.getLogger(__name__)

#from can.interfaces.usb2can import *
from usb2can import *
from can.bus import BusABC
from can.message import Message
#from can.usb2canSerialFindWin import serial
from usb2canSerialFindWin import serial



boottimeEpoch = 0
try:
    import uptime
    import datetime
    boottimeEpoch = (uptime.boottime() - datetime.datetime.utcfromtimestamp(0)).total_seconds()
except:
    boottimeEpoch = 0

# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('can.usb2can')
#setup the string for the device
def setString (deviceID, baudrate = '500'):
	
	
	#config = deviceID + '; ' + baudrate
	config = "%s; %s" % (deviceID, baudrate)
	
	return (config)

#returns 2*offset if the bit is set to 1, returns zero if bit is set to zero	
def testBit(number, offset):
	mask = 1 << offset
	return(number & mask)

#logic to convert from native python type to converted ctypes.  Using a tuple
def dataConvert(data):
	j = tuple(int(z,16) for z in data)
	converted = (c_ubyte * 8) (*j)
	return converted

#TODO issue with data being zeros or anything other than 8 must be fixed
def messageConvertTX(msg):
	
	#binary for flags, transmit bit set to 1
	
	#should auto initalize for me
	#rawBytes = dataConvert([0,0,0,0,0,0,0,0])
	#rawBytes = dataConvert('00000000')
	
	#messagetx = CanalMsg(bits, 0, msg.arbitration_id, len(msg.data), rawBytes, 0)
	
	messagetx = CanalMsg()
	
	length = len(msg.data)
	messagetx.sizeData = length
	
	messagetx.id = msg.arbitration_id
	
	'''
	temp = bytearray(msg.data)
	rawBytes = (ctypes.c_uint8 * 8).from_buffer_copy(temp)
	'''
	for i in range(length)):
		messagetx.data[i] = msg.data[i]
	
	'''
	temp = bytearray(msg.data)
	messagetx.data = (ctypes.c_uint8 * 8).from_buffer_copy(temp)
	'''
	
	
	'''
	length = c_ubyte
	length = len(msg.data)
	if length < 8:
		padding = 8 - length
		
		while padding is not 0:
			msg.data.append(0)
			padding = padding - 1
		
	'''
	messagetx.flags = 80000000
	
	if msg.is_error_frame == True:
		messagetx.flags = messagetx.flags | 1 << 2
	
	
	if msg.is_remote_frame == True:
		messagetx.flags = messagetx.flags | 1 << 1
	
	
	if msg.id_type == True:
		messagetx.flags = messagetx.flags | 1 << 0
	
	'''
	temp = bytearray(msg.data)
	rawBytes = (ctypes.c_uint8 * 8).from_buffer_copy(temp)
	'''
	#old message tx for if while loop.
	#messagetx = CanalMsg(bits, 0, msg.arbitration_id, length, rawBytes, 0)
	
		
	
	return messagetx
#convert the message from the CANAL type to pythoncan type	
def messageConvertRX(messagerx):
	
	#converted = dataConvert('00000000')
	#flag is from Canal device
	bits = messagerx.flags
	
	msgrx = Message()
	
	if testBit(bits, 0) != 0:
		msgrx.id_type = True
	else:
		msgrx.id_type = False
	
	if testBit(bits, 1) != 0:
		msgrx.is_remote_frame = True
	else:
		msgrx.is_remote_frame = False
	
	if testBit(bits, 2) != 0:
		msgrx.is_error_frame = True
	else:
		msgrx.is_error_frame = False
	
	msgrx.arbitration_id = messagerx.id
	msgrx.dlc = messagerx.sizeData
	
	
	msgrx.data = bytearray(messagerx.data)
	
	msgrx.timestamp = messagerx.timestamp
	
	
	return msgrx
#interface functions
class Usb2canBus(BusABC):
	
	#can = usb2can()
	
	def __init__(self, channel, *args, **kwargs):
	
		self.can = usb2can()
	
		enableFlags = c_ulong
	
		#set flags on the connection
		if 'flags' in kwargs:
			enableFlags = kwargs["flags"]
			
		else:
			enableFlags = 0x00000008
	
	
	
		#code to get the serial number of the device
		if 'serial' in kwargs:
			
			deviceID = kwargs["serial"]
			
		
			#connector = setString(deviceID, baudrate)
		else:	
			deviceID = serial()
			#baudrate = 500
			#connector = setString(deviceID, baudrate)
	
		#set baudrate
	
		if 'baud' in kwargs:
			
			br = kwargs["baud"]
			
			#set custom baud rate (ex:500000 bitrate must be 500)
			#max rate is 1000 kbps
			baudrate = int(br)
			
		#set default value		
		else:
			baudrate = 500
		
		connector = setString(deviceID, baudrate)
		
		self.handle = self.can.CanalOpen(connector, enableFlags)
		
	#send a message	
	def send(self, msg):
		
		tx = messageConvertTX(msg)
		self.can.CanalSend(self.handle, byref(tx))
		
		#enable debug mode
		#debug = can.CanalSend(handle, byref(msg))
		#return debug
		
	#recieve a message	
	def recv (self, timeout=None):
		
		status = 1
		#converted = dataConvert('00000000')
		#messagerx = CanalMsg(00000000, 0, 11, 8, converted, int(boottimeEpoch))
		messagerx = CanalMsg()
		
		while status != 0:
		
			if status != 0:
				status = self.can.CanalReceive(self.handle, byref(messagerx))
				rx = messageConvertRX(messagerx)
				
		
		return rx	
		

#implementation of a close function to shut down the device safely	
	def shutdown(self):
		status = self.can.CanalClose(self.handle)