import asyncio
import can

def print_message(msg):
    """Regular callback function. Can also be a coroutine."""
    print(msg)

async def main():
    can0 = can.Bus('vcan0', bustype='virtual', receive_own_messages=True)
    reader = can.AsyncBufferedReader()
    logger = can.Logger('logfile.asc')

    listeners = [
        print_message,  # Callback function
        reader,         # AsyncBufferedReader() listener
        logger          # Regular Listener object
    ]
    # Create Notifier with an explicit loop to use for scheduling of callbacks
    loop = asyncio.get_event_loop()
    notifier = can.Notifier(can0, listeners, loop=loop)
    # Start sending first message
    can0.send(can.Message(arbitration_id=0))

    print('Bouncing 10 messages...')
    for _ in range(10):
        # Wait for next message from AsyncBufferedReader
        msg = await reader.get_message()
        # Delay response
        await asyncio.sleep(0.5)
        msg.arbitration_id += 1
        can0.send(msg)
    # Wait for last message to arrive
    await reader.get_message()
    print('Done!')

    # Clean-up
    notifier.stop()
    can0.shutdown()

# Get the default event loop
loop = asyncio.get_event_loop()
# Run until main coroutine finishes
loop.run_until_complete(main())
loop.close()
