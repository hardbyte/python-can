import optparse
import sys
import time

from pycanlib import CAN, canlib


def _parse_arguments(arguments):
    _parser = optparse.OptionParser(" ".join(arguments[1:]))
    _parser.add_option("-c", "--channel", dest="channel", help="CAN channel number", default="0")
    _parser.add_option("-s", "--speed", dest="speed", help="CAN bus speed", default="105263")
    _parser.add_option("-t", "--tseg1", dest="tseg1", help="CAN bus tseg1", default="10")
    _parser.add_option("-u", "--tseg2", dest="tseg2", help="CAN bus tseg2", default="8")
    _parser.add_option("-w", "--sjw", dest="sjw", help="CAN bus SJW", default="4")
    _parser.add_option("-n", "--noSamp", dest="no_samp", help="CAN bus sample number", default="1")
    _parser.add_option("-r", "--refreshInterval", dest="refresh_interval", help="Display refresh interval (seconds)", default=1)
    return _parser.parse_args()

def _create_bus_object(options):
    _channel = int(options.channel)
    _speed = int(options.speed)
    _tseg1 = int(options.tseg1)
    _tseg2 = int(options.tseg2)
    _sjw = int(options.sjw)
    _no_samp = int(options.no_samp)
    return CAN.Bus(channel=_channel, speed=_speed, tseg1=_tseg1, tseg2=_tseg2, sjw=_sjw, no_samp=_no_samp)

def main(arguments):
    (_options, _args) = _parse_arguments(arguments)
    _bus = _create_bus_object(_options)
    _refresh_interval = float(_options.refresh_interval)
    try:
        while True:
            time.sleep(_refresh_interval)
            print "Bus load = %f%%" % _bus.bus_load
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main(sys.argv)
