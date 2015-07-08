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
enableFlags = 0x00000008

#call function to get serial number
#serial = serial()
#test statement to check serial number
#print serial

#set default to 500 kbps
#baudrate = '500'




boottimeEpoch = 0
try:
    import uptime
    import datetime
    boottimeEpoch = (uptime.boottime() - datetime.datetime.utcfromtimestamp(0)).total_seconds()
except:
    boottimeEpoch = 0

	
#logic to convert from native python type to converted ctypes.  Using a tuple
j = tuple(int(z,16) for z in data)
converted = (c_ubyte * 8) (*j)
#initalize the message object, send object
messagerx = CanalMsg(00000000, 0, 11, 8, converted, boottimeEpoch)	
	
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
	
def messageConvertTX(msg):
	
	#binary for flags, transmit bit set to 1
	bits = 80000000
	
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
	
	if 'ED' in kwargs:
		location = kwargs.find('ED', beg = 0 end = len(kwargs))
		deviceID = kwargs[location : (location + 7)
		#add code to find baudrate
		
		#code to add baudrate
		
		connector = setString(deviceID, baudrate)
	else:	
		deviceID = serial()
		connector = setString(deviceID, baudrate)
	
	handle = can.CanalOpen(connector, enableFlags)
		
	def send(self, msg):
		
		tx = messagveConvertTX(msg)
		can.CanalSend(handle, byref(msg))
		
		#enable debug mode
		#debug = can.CanalSend(handle, byref(msg))
		#return debug
		
		
	def recv (self, timeout=None):
		
		can.CanalReceive(handle, byref(messagerx))
		rx = messageConvertRX(messagerx)
		return rx
		
	def error(self):
		test = 0
	
	def close(self):
		status = can.CanalClose(device)
		#Print Error code, debug
		#print status
		