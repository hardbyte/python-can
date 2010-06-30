"""
busload.py: an example script illustrating access to the bus
load measurement taken by the CAN device.

Copyright (C) 2010 Dynamic Controls

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Contact details
---------------

Postal address:
    Dynamic Controls
    17 Print Place
    Addington
    Christchurch 8024
    New Zealand

E-mail: bpowell AT dynamiccontrols DOT com
"""
import optparse
import sys
import time

from pycanlib import CAN, canlib


def _parse_arguments(arguments):
    _parser = optparse.OptionParser(" ".join(arguments[1:]))
    _parser.add_option("-c", "--channel", dest="channel", help="CAN channel number")
    _parser.add_option("-s", "--speed", dest="speed", help="CAN bus speed")
    _parser.add_option("-t", "--tseg1", dest="tseg1", help="CAN bus tseg1")
    _parser.add_option("-u", "--tseg2", dest="tseg2", help="CAN bus tseg2")
    _parser.add_option("-w", "--sjw", dest="sjw", help="CAN bus SJW")
    _parser.add_option("-n", "--noSamp", dest="no_samp", help="CAN bus sample number")
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
