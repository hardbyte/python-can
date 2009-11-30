import datetime
import logging
import logging.handlers
from optparse import OptionParser
import os
import os.path
import time

from pycanlib import CAN, canlib

parser = OptionParser()
parser.add_option("-c", "--channel", dest="channel",
  help="CAN channel number", default="0")
parser.add_option("-s", "--speed", dest="speed", help="CAN bus speed",
  default="105263")
parser.add_option("-t", "--tseg1", dest="tseg1", help="CAN bus tseg1",
  default="10")
parser.add_option("-u", "--tseg2", dest="tseg2", help="CAN bus tseg2",
  default="8")
parser.add_option("-w", "--sjw", dest="sjw", help="CAN bus SJW",
  default="4")
parser.add_option("-n", "--noSamp", dest="noSamp",
  help="CAN bus sample number", default="1")
parser.add_option("-d", "--driverMode", dest="driverMode",
  help="Mode (silent/normal) for Kvaser CAN bus output driver",
  default="silent")
_helpStr = "Base log file name, where log file names are"
_helpStr += " <base>_<datestamp>_<timestamp>"
parser.add_option("-l", "--logFileNameBase", dest="logFileNameBase",
  help=_helpStr, default="can_logger")
parser.add_option("-p", "--logFilePath", dest="logFilePath",
  help="Log file path", default="can_logger")

(options, args) = parser.parse_args()

_channel = int(options.channel)
_speed = int(options.speed)
_tseg1 = int(options.tseg1)
_tseg2 = int(options.tseg2)
_sjw = int(options.sjw)
_noSamp = int(options.noSamp)
if options.driverMode.lower() == "silent":
    _driverMode = canlib.canDRIVER_SILENT
elif options.driverMode.lower() == "normal":
    _driverMode = canlib.canDRIVER_NORMAL

bus = CAN.Bus(channel=_channel, flags=canlib.canOPEN_ACCEPT_VIRTUAL,
  speed=_speed, tseg1=_tseg1, tseg2=_tseg2, sjw=_sjw, noSamp=_noSamp,
  driverMode=_driverMode)

_loggerObj = logging.getLogger("can_logger")
_loggerObj.setLevel(logging.INFO)
_logStreamHandler = logging.StreamHandler()
_logTimestamp = datetime.datetime.now()
_dateString = _logTimestamp.strftime("%Y%m%d")
_timeString = _logTimestamp.strftime("%H%M%S")
fullLogFilePath = os.path.join(os.path.expanduser("~"),
  "%s" % options.logFilePath, "%s_%s_%s.log" % (options.logFileNameBase,
  _dateString, _timeString))
if not os.path.isdir(os.path.dirname(fullLogFilePath)):
    os.makedirs(os.path.dirname(fullLogFilePath))
_logFileHandler = logging.FileHandler(fullLogFilePath, mode="w")
_logFormatter = logging.Formatter("%(message)s")
_logStreamHandler.setFormatter(_logFormatter)
_logFileHandler.setFormatter(_logFormatter)
_loggerObj.addHandler(_logStreamHandler)
_loggerObj.addHandler(_logFileHandler)

for line in bus.GetChannelInfo().__str__().split("\n"):
    _loggerObj.info(line)
while True:
    try:
        msg = bus.Read()
        if msg != None:
            _loggerObj.info(msg)
        else:
            time.sleep(0.001)
    except KeyboardInterrupt:
        break
time.sleep(0.1)
