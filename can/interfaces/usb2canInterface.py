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
baudrate = '500'




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
messagetx = CanalMsg(80000000, 0, 11, 8, converted, boottimeEpoch)	
messagerx = CanalMsg(00000000, 0, 11, 8, converted, boottimeEpoch)	
	
# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('can.usb2can')

def setString (deviceID, baudrate = '500'):
	
	
	config = serial + '; ' + baudrate
	
	retrun config
	
def messageConvertTX(msg):
	
	#binary for flags, transmit bit set to 1
	bits = 80000000
	
	if msg.errorframe == true:
		bits = bits | 1 << 2

	if msg.remoteframe == true:
		bits = bits | 1 << 1
	
	
	if msg.extendedID == true:
		bits = bits | 1 << 0
	
	
	messagetx.flag = bits
	messagetx.sizeData = msg.dlc
	messagetx.data = msg.data
	messagetx.timestamp = boottimeEpoch
	
	return messagetx
	
def messageConvertRX(messagerx):
	
	
	return msgrx

class Usb2canBus(BusABC):
	
	def __init__(self, channel, *args, **kwargs):
	
	if 'ED' in kwargs:
		location = kwargs.find('ED', beg = 0 end = len(kwargs))
		deviceID = kwargs[location : (location + 7)
		connector = setString(deviceID)
	else:	
		deviceID = serial()
		connector = setString(deviceID, '500')
		
		
	def send(self, msg):
		
		
		
		
	def recv (self, timeout=None):
		test = 0
		
	def error(self):
		test = 0
	
	def close(self):
		status = can.CanalClose(device)
		#Print Error code, debug
		#print status
		