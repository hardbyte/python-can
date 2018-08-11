import asyncio
import can

def message_available(bus):
    msg = bus.recv(0)
    if msg is None:
        # Should not happen
        return
    print(msg)

# Will only work on SocketCAN
bus = can.Bus('vcan0', bustype='socketcan')
loop = asyncio.get_event_loop()
# Start watching the bus for available messages.
# Call message_available() with the bus as argument.
loop.add_reader(bus, message_available, bus)
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    bus.shutdown()
    loop.close()
