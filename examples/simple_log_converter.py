#!/usr/bin/env python

"""
Use this to convert .can/.asc files to .log files.
Can be easily adapted for all sorts of files.

Usage: python3 simple_log_convert.py sourceLog.asc targetLog.log
"""

import sys

import can


def main():
    """The transcoder"""

    with can.LogReader(sys.argv[1]) as reader:
        with can.Logger(sys.argv[2]) as writer:
            for msg in reader:
                writer.on_message_received(msg)


if __name__ == "__main__":
    main()
