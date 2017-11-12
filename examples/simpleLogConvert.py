#!/usr/bin/env python
import sys
import can.io.logger
import can.io.player

reader = can.io.player.LogReader(sys.argv[1])
writer = can.io.logger.Logger(sys.argv[2])

for msg in reader:
    writer.on_message_received(msg)
