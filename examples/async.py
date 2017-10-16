import asyncio
import can


can.rc['interface'] = 'virtual'
can.rc['channel'] = 'vcan0'

loop = asyncio.get_event_loop()


async def receiver():
    bus = can.interface.Bus()
    print("Receiver: Waiting for first message...")
    msg = await bus.async_recv()
    print("Receiver: Got %r" % msg)
    print("Receiver: Waiting 1 second...")
    await asyncio.sleep(1)
    print("Receiver: Waiting for second message...")
    msg = await bus.async_recv()
    print("Receiver: Got %r" % msg)
    print("Receiver: Waiting for a message with a timeout...")
    try:
        msg = await asyncio.wait_for(bus.async_recv(), timeout=1.1)
    except asyncio.TimeoutError:
        print("Receiver: Timeout occurred")
    print("Receiver: Shutting down bus")
    bus.shutdown()

async def sender():
    bus = can.interface.Bus()
    msg = can.Message(arbitration_id=0x123, data=[1,2,3,4,5])
    print("Sender: Waiting for 1 second...")
    await asyncio.sleep(1)
    print("Sender: Sending first message...")
    await bus.async_send(msg)
    await asyncio.sleep(0.01)
    print("Sender: Sending second message...")
    await bus.async_send(msg)
    print("Sender: Shutting down bus")
    bus.shutdown()

print("Scheduling sender and receiver concurrently")
loop.run_until_complete(asyncio.gather(receiver(), sender()))


async def iterate_messages():
    bus = can.interface.Bus()
    print("Infinite loop started. Printing messages...")
    try:
        async for msg in bus:
            print(msg)
    except asyncio.CancelledError:
        print("Iteration was cancelled")
    finally:
        bus.shutdown()

async def cancel_infinite_loop():
    print("Scheduling inifinite loop")
    task = asyncio.ensure_future(iterate_messages())
    # Allow task to start
    await asyncio.sleep(0)
    bus = can.interface.Bus()
    for i in range(1, 4):
        msg = can.Message(arbitration_id=i)
        print("Sending message %d" % i)
        await bus.async_send(msg)
        await asyncio.sleep(1)
    print("Stopping iterator task")
    task.cancel()
    bus.shutdown()

loop.run_until_complete(cancel_infinite_loop())
