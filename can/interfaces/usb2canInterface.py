from usb2can import *
import logging

logger = logging.getLogger(__name__)

from can.interfaces.PCANBasic import *
from can.bus import BusABC
from can.message import Message

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