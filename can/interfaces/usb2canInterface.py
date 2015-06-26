#this interface is for windows only, otherwise use socketCAN

import logging

logger = logging.getLogger(__name__)

from can.interfaces.usb2can import *
from can.bus import BusABC
from can.message import Message


#code to handle finding devices

import win32com.client
def WMIDateStringToDate(dtmDate):
    strDateTime = ""
    if (dtmDate[4] == 0):
        strDateTime = dtmDate[5] + '/'
    else:
        strDateTime = dtmDate[4] + dtmDate[5] + '/'
    if (dtmDate[6] == 0):
        strDateTime = strDateTime + dtmDate[7] + '/'
    else:
        strDateTime = strDateTime + dtmDate[6] + dtmDate[7] + '/'
        strDateTime = strDateTime + dtmDate[0] + dtmDate[1] + dtmDate[2] + dtmDate[3] + " " + dtmDate[8] + dtmDate[9] + ":" + dtmDate[10] + dtmDate[11] +':' + dtmDate[12] + dtmDate[13]
    return strDateTime

strComputer = "."
objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
objSWbemServices = objWMIService.ConnectServer(strComputer,"root\cimv2")
colItems = objSWbemServices.ExecQuery("SELECT * FROM Win32_USBControllerDevice")
for objItem in colItems:
    if objItem.AccessState != None:
        print "AccessState:" + ` objItem.AccessState`
    if objItem.Antecedent != None:
        print "Antecedent:" + ` objItem.Antecedent`
    if objItem.Dependent != None:
        print "Dependent:" + ` objItem.Dependent`
    if objItem.NegotiatedDataWidth != None:
        print "NegotiatedDataWidth:" + ` objItem.NegotiatedDataWidth`
    if objItem.NegotiatedSpeed != None:
        print "NegotiatedSpeed:" + ` objItem.NegotiatedSpeed`
    if objItem.NumberOfHardResets != None:
        print "NumberOfHardResets:" + ` objItem.NumberOfHardResets`
    if objItem.NumberOfSoftResets != None:
        print "NumberOfSoftResets:" + ` objItem.NumberOfSoftResets`









#end of device finding code

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



class Usb2canBus(BusABC):
	
	def __init__(self, channel, *args, **kwargs):
	
		#default to 500kb/s
		baudrate = 500
		
		
	def send(self, msg)