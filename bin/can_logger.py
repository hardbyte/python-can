#!/usr/bin/env python
"""
can_logger.py logs CAN traffic to the terminal and to a file on disk.

Dynamic Controls 2010
"""

import datetime
import argparse

import can

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log CAN traffic, printing messages to stdout")
    
    parser.add_argument("-c", "--channel", type=str, dest="channel", 
                        help="""
                        If the CAN interface supports multiple channels, select which one
                        you are after here. For example on linux this might be vcan0 or can1
                        """, default='0')
    
    parser.add_argument("-f", "--file_name", dest="log_file",
                        help="""Path and base log filename, extension can be .txt, .csv, .db, .npz""",
                        default="can_logger")
        
    # TODO: Not all backends will support these options...
    parser.add_argument("-b", "--bitrate", type=int, dest="bitrate", 
                        help="CAN bus bitrate", default=1000000)
    
    parser.add_argument("--tseg1", type=int, dest="tseg1", 
                        help="CAN bus tseg1", default=4)
                        
    parser.add_argument("--tseg2", type=int, dest="tseg2", 
                        help="CAN bus tseg2", default=3)
                        
    parser.add_argument("--sjw", type=int, dest="sjw", 
                        help="Synchronisation Jump Width decides the maximum number of time quanta that the controller can resynchronise every bit.",
                        default=1)
                        
    parser.add_argument("-n", "--num_samples", type=int, dest="no_samp",
                        help="""Some CAN controllers can also sample each bit three times.
                                In this case, the bit will be sampled three quanta in a row, 
                                with the last sample being taken in the edge between TSEG1 and TSEG2.

                                Three samples should only be used for relatively slow baudrates.""", 
                        default=1)
    

    parser.add_argument("-v", action="count", dest="verbosity", 
                      help='''How much information do you want to see at the command line? 
                              You can add several of these e.g., -vv is DEBUG''', default=2)
    
    results = parser.parse_args()
    
    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, results.verbosity)]
    can.set_logging_level(logging_level_name)
    
    bus = can.Bus(channel=results.channel, 
                  bitrate=results.bitrate, 
                  tseg1=results.tseg1, 
                  tseg2=results.tseg2, 
                  sjw=results.sjw, 
                  no_samp=results.no_samp)

    log_start_time = datetime.datetime.now()
    
    listener = can.BufferedReader()
    bus.listeners.append(listener)
    
    print('Can Logger (Started on {})\n'.format(log_start_time))
    try:
        while True:
            msg = listener.get_message()
            if msg is not None and str(msg) != "":
                print(msg)
                
    except KeyboardInterrupt:
        pass
    finally:
        bus.shutdown()
    
