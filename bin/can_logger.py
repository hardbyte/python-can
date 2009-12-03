import datetime
import logging
import logging.handlers
from optparse import OptionParser
import os
import os.path
import sys
import time
from xml.dom import minidom

from pycanlib import CAN, canlib


def ParseArguments(arguments):
    parser = OptionParser(" ".join(arguments[1:]))
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
    return parser.parse_args()


def CreateBusObject(options):
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
    return CAN.Bus(channel=_channel, flags=canlib.canOPEN_ACCEPT_VIRTUAL,
      speed=_speed, tseg1=_tseg1, tseg2=_tseg2, sjw=_sjw, noSamp=_noSamp,
      driverMode=_driverMode)


def SetupLogging(logFilePath, logFileNameBase):
    loggerObj = logging.getLogger("can_logger")
    loggerObj.setLevel(logging.INFO)
    _logStreamHandler = logging.StreamHandler()
    _logTimestamp = datetime.datetime.now()
    _dateString = _logTimestamp.strftime("%Y%m%d")
    _timeString = _logTimestamp.strftime("%H%M%S")
    fullLogFilePath = os.path.join(os.path.expanduser("~"),
      "%s" % logFilePath, "%s_%s_%s.log" % (logFileNameBase,
      _dateString, _timeString))
    if not os.path.isdir(os.path.dirname(fullLogFilePath)):
        os.makedirs(os.path.dirname(fullLogFilePath))
    _logFileHandler = logging.FileHandler(fullLogFilePath, mode="w")
    xmlLogFilePath = os.path.join(os.path.expanduser("~"),
      "%s" % logFilePath, "%s_%s_%s.xml" % (logFileNameBase,
      _dateString, _timeString))
    xmlFile = open(xmlLogFilePath, "w")
    _logFormatter = logging.Formatter("%(message)s")
    _logStreamHandler.setFormatter(_logFormatter)
    _logFileHandler.setFormatter(_logFormatter)
    loggerObj.addHandler(_logStreamHandler)
    loggerObj.addHandler(_logFileHandler)
    return loggerObj, xmlFile, _logTimestamp


def main(arguments):
    (options, args) = ParseArguments(arguments)
    bus = CreateBusObject(options)
    (loggerObj, xmlFile, startTime) = SetupLogging(options.logFilePath, options.logFileNameBase)
    loggerObj.info("-"*64)
    loggerObj.info("Host machine info")
    loggerObj.info("-"*64)
    hostMachineInfo = CAN.GetHostMachineInfo()
    for line in hostMachineInfo.__str__().split("\n"):
        loggerObj.info(line)
    loggerObj.info("-"*64)
    loggerObj.info("Channel info")
    loggerObj.info("-"*64)
    channelInfo = bus.GetChannelInfo()
    for line in channelInfo.__str__().split("\n"):
        loggerObj.info(line)
    msgList = []
    while True:
        try:
            msg = bus.Read()
            if msg != None:
                loggerObj.info(msg)
                msgList.append(msg)
            else:
                time.sleep(0.001)
        except KeyboardInterrupt:
            endTime = datetime.datetime.now()
            break
    _logDoc = minidom.Document()
    _logElement = _logDoc.createElement("pycanlib_log")
    _logElement.appendChild(hostMachineInfo.ToXML())
    _logElement.appendChild(channelInfo.ToXML())
    _logInfoElement = _logDoc.createElement("log_info")
    _logStartTimeElement = _logDoc.createElement("log_start_time")
    _logStartTimeText = _logDoc.createTextNode("%s" % startTime)
    _logStartTimeElement.appendChild(_logStartTimeText)
    _logInfoElement.appendChild(_logStartTimeElement)
    _logEndTimeElement = _logDoc.createElement("log_end_time")
    _logEndTimeText = _logDoc.createTextNode("%s" % endTime)
    _logEndTimeElement.appendChild(_logEndTimeText)
    _logInfoElement.appendChild(_logEndTimeElement)
    _logElement.appendChild(_logInfoElement)
    _logMessagesElement = _logDoc.createElement("messages")
    for _message in msgList:
        _logMessagesElement.appendChild(_message.ToXML())
    _logElement.appendChild(_logMessagesElement)
    _logDoc.appendChild(_logElement)
    xmlFile.write("%s" % _logDoc.toprettyxml())
    xmlFile.close()

if __name__ == "__main__":
    main(sys.argv)
