#!/usr/bin/env python

"""
This example demonstrates how to use async IO with python-can.
"""

import asyncio
import can


def print_message(msg):
    """Regular callback function. Can also be a coroutine."""
    print(msg)


async def main():
    """The main function that runs in the loop."""

    bus = can.Bus("vcan0", bustype="virtual", receive_own_messages=True)
    reader = can.AsyncBufferedReader()
    logger = can.Logger("logfile.asc")

    listeners = [
        print_message,  # Callback function
        reader,  # AsyncBufferedReader() listener
        logger,  # Regular Listener object
    ]
    # Create Notifier with an explicit loop to use for scheduling of callbacks
    loop = asyncio.get_event_loop()
    notifier = can.Notifier(bus, listeners, loop=loop)
    # Start sending first message
    bus.send(can.Message(arbitration_id=0))

    print("Bouncing 10 messages...")
    for _ in range(10):
        # Wait for next message from AsyncBufferedReader
        msg = await reader.get_message()
        # Delay response
        await asyncio.sleep(0.5)
        msg.arbitration_id += 1
        bus.send(msg)
    # Wait for last message to arrive
    await reader.get_message()
    print("Done!")

    # Clean-up
    notifier.stop()
    bus.shutdown()


if __name__ == "__main":
    try:
        # Get the default event loop
        LOOP = asyncio.get_event_loop()
        # Run until main coroutine finishes
        LOOP.run_until_complete(main())
    finally:
        LOOP.close()

    # or on Python 3.7+ simply
    # asyncio.run(main())
