from optparse import OptionParser
import sys
import time

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
    parser.add_option("-r", "--refreshInterval", dest="refreshInterval",
      help="Display refresh interval (seconds)", default=1)
    return parser.parse_args()


def CreateBusObject(options):
    _channel = int(options.channel)
    _speed = int(options.speed)
    _tseg1 = int(options.tseg1)
    _tseg2 = int(options.tseg2)
    _sjw = int(options.sjw)
    _noSamp = int(options.noSamp)
    return CAN.Bus(channel=_channel, flags=canlib.canOPEN_ACCEPT_VIRTUAL,
      speed=_speed, tseg1=_tseg1, tseg2=_tseg2, sjw=_sjw, no_samp=_noSamp)

def main(arguments):
    (options, args) = ParseArguments(arguments)
    bus = CreateBusObject(options)
    _refreshInterval = float(options.refreshInterval)
    try:
        while True:
            time.sleep(_refreshInterval)
            print "Bus load = %f%%" % bus.get_statistics().bus_load
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main(sys.argv)
