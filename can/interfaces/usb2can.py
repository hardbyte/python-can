#This wrapper is for windows or direct access via CANAL API.  Socket CAN is recommended under Unix/Linux systems

from ctypes import *
from struct import *
#import collections

#type definitions

flags = c_ulong
pConfigureStr = c_char_p
handle = c_long
timeout = c_ulong
filter = c_ulong





class CanalStatistics(Structure):

	_fields_ = [('ReceiveFrams', c_ulong),
		('TransmistFrams', c_ulong),
		('ReceiveData', c_ulong),
		('TransmitData', c_ulong),
		('Overruns', c_ulong),
		('BusWarnings', c_ulong),
		('BusOff', c_ulong)]

stat = CanalStatistics

class CanalStatus(Structure):
	_fields_ = [('channel_status', c_ulong),
		('lasterrorcode', c_ulong),
		('lasterrorsubcode', c_ulong),
		('lasterrorstr', c_byte * 80)]
	

#data type for the CAN Message
class CanalMsg(Structure):
	
	
	_fields_ = [('flags', c_ulong), 
		('obid', c_ulong), 
		('id', c_ulong), 
		('sizeData', c_ubyte), 
		('data', c_ubyte * 8), 
		('timestamp', c_ulong)]
	
msg = CanalMsg		
	
class usb2can:
	
	def __init__(self):
		self.__m_dllBasic = windll.LoadLibrary("usb2can.dll")
		
		if self.__m_dllBasic == None:
			print "DLL cannot be loaded"
	



	def CanalOpen(self, pConfigureStr, flags):
		try:
			res = self.__m_dllBasic.CanalOpen(pConfigureStr, flags)
			return res
		except:
			print "Could not open"
			raise
	def CanalClose(self, handle):
		try:
			res = self.__m_dllBasic.CanalClose(handle)
			return res
		except:
			print "could not close port"
			raise
	def CanalSend(self, handle, msg):
		try:	
			res = self.__m_dllBasic.CanalSend(handle, msg)
			return res
		except:
			print "sending error"
			raise
	def CanalReceive(self, handle, msg):
		try:	
			res = self.__m_dllBasic.CanalReceive(handle, msg)
			return res
		except:
			print "Receive Error"
			raise		
		
	def CanalBlockingSend(self, handle, msg, timeout):
		try:	
			res = self.__m_dllBasic.CanalBlockingSend(handle, msg, timeout)
			return res
		except:
			print "sending error"
			raise		
	
	def CanalBlockingReceive(self, handle, msg, timeout):
		try:	
			res = self.__m_dllBasic.CanalBlockingReceive(handle, msg, timeout)
			return res
		except:
			print "receive Error"
			raise		
		
	def CanalGetStatus(self, handle, CanalStatus):
		try:
			res = self.__m_dllBasic.CanalGetStatus(handle, CanalStatus)
			return res
		except:
			print "failed to get status"
			raise
	
	
	
	
	def CanalGetStatistics(self, handle, CanalStatistics):
		try:	
			res = self.__m_dllBasic.CanalGetStatistics(handle, CanalStatistics)
			return res
		except:
			print "sending error"
			raise
	
	
	
	
	
	def CanalGetVersion(self):
		try:	
			res = self.__m_dllBasic.CanalGetVersion()
			return res
		except:
			print "sending error"
			raise
	
	
	
	
	
	def CanalGetDllVersion(self):
		try:	
			res = self.__m_dllBasic.CanalGetDllVersion()
			return res
		except:
			print "sending error"
			raise
	
	
	
	
	
	def CanalGetVendorString(self):
		try:	
			res = self.__m_dllBasic.CanalGetVendorString()
			return res
		except:
			print "sending error"
			raise	
	
	
	

