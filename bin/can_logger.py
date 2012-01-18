#!/usr/bin/env python
"""
can_logger.py: part of pycanlib, logs CAN traffic to the terminal and
to a file on disk.

Copyright (C) 2010 Dynamic Controls
"""

import cPickle
import datetime
import argparse
import os
import sys
import time

from pycanlib import CAN

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A logging system for CAN signals")
    parser.add_argument("-c", "--channel", type=int, dest="channel", help="CAN channel number", default=0)
    parser.add_argument("-b", "--bitrate", type=int, dest="bitrate", help="CAN bus bitrate", default=1000000)
    parser.add_argument("-t", "--tseg1", type=int, dest="tseg1", help="CAN bus tseg1", default=4)
    parser.add_argument("-u", "--tseg2", type=int, dest="tseg2", help="CAN bus tseg2", default=3)
    parser.add_argument("-w", "--sjw", type=int, dest="sjw", help="CAN bus SJW", default=1)
    parser.add_argument("-n", "--num_samples", type=int, dest="no_samp", help="CAN bus sample number", default=3)
    parser.add_argument("-l", "--log_file_name_base", dest="log_file_name_base", help="Base log file name, where log file names are <base>_<datestamp>_<timestamp>", default="can_logger")
    parser.add_argument("-p", "--log_file_path", dest="log_file_path", help="Log file path", default="can_logger")
    parser.add_argument("-v", "--verbosity_level", type = str, dest = "verbosity_level", help = "Sets logging level. Type 'v' to set to info, type 'vv' to set to debug", default = "")
    
    results = parser.parse_args()
    
    levelStr = results.verbosity_level
    levelInt = levelStr.count('v')
    CAN.set_logging_level(levelInt)
    
    bus = CAN.Bus(channel=results.channel, bitrate=results.bitrate, tseg1=results.tseg1, tseg2=results.tseg2, sjw=results.sjw, no_samp=results.no_samp)
    message_list = []
    log_start_time = datetime.datetime.now()
    timestamp_string = log_start_time.strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(os.path.expanduser("~"), "%s" % results.log_file_path, "%s_%s.dat" % (results.log_file_name_base,  timestamp_string))
    file_name = os.path.basename(log_file_path)
    if not os.path.exists(os.path.dirname(log_file_path)):
        os.makedirs(os.path.dirname(log_file_path))
    listener = CAN.BufferedReader()
    bus.listeners.append(listener)
    try:
        while True:
            msg = listener.get_message()
            if msg is not None and str(msg) != "":
                print msg
                message_list.append(msg)
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()
    time.sleep(0.5)
    log_obj = CAN.Log(log_info=CAN.LogInfo(log_start_time=log_start_time, log_end_time=datetime.datetime.now(), original_file_name=file_name, tester_name=("%s" % os.getenv("USERNAME"))), channel_info=bus.channel_info, machine_info=CAN.get_host_machine_info(), message_lists=[CAN.MessageList(messages=message_list)])
    with open(log_file_path, "wb") as log_file:
        cPickle.dump(log_obj, log_file)

