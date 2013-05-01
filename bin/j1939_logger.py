import argparse
import datetime, time
import can
can.rc['interface'] = 'socketcan_native'

from can.interfaces.interface import *
from can.protocols import j1939

bus = j1939.Bus(channel='can0')

log_start_time = datetime.datetime.now()
print('can.j1939 Logger (Started on {})\n'.format(log_start_time))

for msg in bus:
    print(msg)
