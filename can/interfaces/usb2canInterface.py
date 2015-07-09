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

enableFlags = c_ulong
#enable status messages
enableFlags


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

def setString (deviceID, baudrate = '500'):
	
	
	config = serial + '; ' + baudrate
	
	retrun config

#returns 2*offset if the bit is set to 1, returns zero if bit is set to zero	
def testBit(number, offset):
	mask = 1 << offset
	return(number & mask)

#logic to convert from native python type to converted ctypes.  Using a tuple
def dataConvert(data)
	j = tuple(int(z,16) for z in data)
	converted = (c_ubyte * 8) (*j)
	return converted
	
def messageConvertTX(msg):
	
	#binary for flags, transmit bit set to 1
	bits = 80000000
	
	converted = dataConvert('00000000')
	
	messagetx = CanalMsg(bits, 0, 11, 8, converted, boottimeEpoch)
	
	if msg.is_error_frame == true:
		bits = bits | 1 << 2
	
	
	if msg.is_remote_frame == true:
		bits = bits | 1 << 1
	
	
	if msg.extended_id == true:
		bits = bits | 1 << 0
	
	
	messagetx.flag = bits
	messagetx.id = msg.arbitration_id
	messagetx.sizeData = msg.dlc
	messagetx.data = msg.data
	messagetx.timestamp = boottimeEpoch
	
	return messagetx
	
def messageConvertRX(messagerx):
	
	converted = dataConvert('00000000')
	bits = messagerx.flag
	
	if testBit(bits, 0) != 0:
		msgrx.extended_id = true
	else:
		msgrx.extended_id = false
	
	if testBit(bits, 1) != 0:
		msgrx.is_remote_frame = true
	else:
		msgrx.is_remote_frame = false
	
	if testBit(bits, 2) != 0:
		msgrx.is_error_frame = true
	else:
		msgrx.is_error_frame = false
	
	msgrx.arbitration_id = messagerx.id
	msgrx.dlc = messagerx.sizeData
	msgrx.data = messagerx.data
	msgrx. = boottimeEpoch
	
	
	return msgrx

class Usb2canBus(BusABC):
	
	def __init__(self, channel, *args, **kwargs):
	
	can = usb2can()
	
	enableFlags = c_ulong
	
	#set flags on the connection
	if '0x0000000' in kwargs:
		location = kwargs.find('0x0000000', beg = 0 end = len(kwargs))
		enableFlags = kwargs[location : (location + 10)
	else:
		enableFlags = 0x00000008
	
	
	
	#code to get the serial number of the device
	if 'ED' in kwargs:
		location = kwargs.find('ED', beg = 0 end = len(kwargs))
		deviceID = kwargs[location : (location + 7)
		#add code to find baudrate
		
		#code to add baudrate
		
		#connector = setString(deviceID, baudrate)
	else:	
		deviceID = serial()
		#baudrate = 500
		#connector = setString(deviceID, baudrate)
	
	#set baudrate
	
	if 'baud' in kwargs:
		location = kwargs.find('baud', beg = 0 end = len(kwargs))
		br = kwargs[location + 4 : (location + 1)
		#logic to figure out what the different baud settings mean
		if br == 25:
			baudrate = 250
		elif br == 5c:
			baudrate = 500
		elif br == 12:
			baudrate = 125
		elif br == 8c:
			baudrate = 800
		elif br == 1c:
			baudrate = 100	
		elif br == 05:
			baudrate = 5
		elif br == 10:
			baudrate = 10
		elif br == 20:
			baudrate = 20
		elif br == 33:
			baudrate = 33
		elif br == 47:
			baudrate = 47
		elif br == 50:
			baudrate = 50
		elif br == 83:
			baudrate = 83
		elif br == 95:
			baudrate = 95
		elif br == 1k:
			baudrate = 1000	
	else
		baudrate = 500
		
	connector = setString(deviceID, baudrate)
	handle = can.CanalOpen(connector, enableFlags)
		
	def send(self, msg):
		
		tx = messagveConvertTX(msg)
		can.CanalSend(handle, byref(tx))
		
		#enable debug mode
		#debug = can.CanalSend(handle, byref(msg))
		#return debug
		
		
	def recv (self, timeout=None):
		
		messagerx = CanalMsg(00000000, 0, 11, 8, converted, boottimeEpoch)
		can.CanalReceive(handle, byref(messagerx))
		rx = messageConvertRX(messagerx)
		return rx
		
	def error(self):
		test = 0
#implementation of a close function to shut down the device safely	
	def shutdown(self):
		status = can.CanalClose(device)
		#Print Error code, debug
		#print status
