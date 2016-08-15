import time
import can

bus = can.interface.Bus(bustype='socketcan', channel='vcan0')

can_filters = [{"can_id": 1, "can_mask": 0xf}]
bus.set_filters(can_filters)
notifier = can.Notifier(bus, [can.Printer()])
time.sleep(10)

