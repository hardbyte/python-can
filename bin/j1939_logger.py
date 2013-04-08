import argparse
import datetime, time
import can
can.rc['interface'] = 'socketcan_native'

from can.interfaces.interface import *
from can.protocols import j1939

bus = j1939.Bus(channel='vcan0')

log_start_time = datetime.datetime.now()
print('can.j1939 Logger (Started on {})\n'.format(log_start_time))

listener = can.Printer(None)
bus.listeners.append(listener)

try:
    while  bus._threads_running:
        # TODO detect if the bus thread has died
        time.sleep(0.5)

except KeyboardInterrupt:
    pass
finally:
    bus.shutdown()



# TODO get going with all interfaces and arguments...
if False and __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log CAN traffic, printing messages to stdout")
    
    interfaces._add_subparsers(parser)
    results = parser.parse_args()
    can.rc['interface'] = results.interface
    
    from can.interfaces.interface import *
    from can.protocols import j1939

    bus = Bus(**results.__dict__)