import datetime
from optparse import OptionParser
import os
import sys
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
  help=_helpStr, default="logger")

(options, args) = parser.parse_args()

_channel = int(options.channel)
_speed = int(options.speed)
_tseg1 = int(options.tseg1)
_tseg2 = int(options.tseg2)
_sjw = int(options.sjw)
_noSamp = int(options.noSamp)
if options.driverMode[0].lower() == "s":
    _driverMode = canlib.canDRIVER_SILENT
elif options.driverMode[0].lower() == "n":
    _driverMode = canlib.canDRIVER_NORMAL

bus = CAN.Bus(channel=_channel, flags=canlib.canOPEN_ACCEPT_VIRTUAL, speed=_speed,
  tseg1=_tseg1, tseg2=_tseg2, sjw=_sjw, noSamp=_noSamp)#, driverMode=_driverMode)
[logFile] = LogUtils.CreateLogFiles(("./%s" % options.logFileNameBase),
  options.logFileNameBase, datetime.now())
while True:
    try:
        msg = bus.Read()
        if msg != None:
            logFile.write("%s\n" % msg)
            print msg
        else:
            _time.sleep(0.001)
    except KeyboardInterrupt:
        break
logFile.close()
bus.threadRunning = False
