import cPickle
import datetime
import optparse
import os
import sys
import time

from pycanlib import CAN

if __name__ == "__main__":
    _parser = optparse.OptionParser()
    _parser.add_option("-c", "--channel", type="int", dest="channel", help="CAN channel number")
    _parser.add_option("-b", "--bitrate", type="int", dest="bitrate", help="CAN bus bitrate")
    _parser.add_option("-t", "--tseg1", type="int", dest="tseg1", help="CAN bus tseg1")
    _parser.add_option("-u", "--tseg2", type="int", dest="tseg2", help="CAN bus tseg2")
    _parser.add_option("-w", "--sjw", type="int", dest="sjw", help="CAN bus SJW")
    _parser.add_option("-n", "--num_samples", type="int", dest="no_samp", help="CAN bus sample number")
    _parser.add_option("-l", "--log_file_name_base", dest="log_file_name_base", help="Base log file name, where log file names are <base>_<datestamp>_<timestamp>", default="can_logger")
    _parser.add_option("-p", "--log_file_path", dest="log_file_path", help="Log file path", default="can_logger")
    (_options, _args) = _parser.parse_args()
    _bus = CAN.Bus(channel=_options.channel, bitrate=_options.bitrate, tseg1=_options.tseg1, tseg2=_options.tseg2, sjw=_options.sjw, no_samp=_options.no_samp)
    _message_list = []
    _log_start_time = datetime.datetime.now()
    _timestamp_string = _log_start_time.strftime("%Y%m%d_%H%M%S")
    _log_file_path = os.path.join(os.path.expanduser("~"), "%s" % _options.log_file_path, "%s_%s.dat" % (_options.log_file_name_base, _timestamp_string))
    _file_name = os.path.basename(_log_file_path)
    if not os.path.exists(os.path.dirname(_log_file_path)):
        os.makedirs(os.path.dirname(_log_file_path))
    _listener = CAN.BufferedReader()
    _bus.add_listener(_listener)
    try:
        while True:
            _msg = _listener.get_message()
            if _msg != None:
                print _msg
                _message_list.append(_msg)
    except KeyboardInterrupt:
        pass
    finally:
        _bus.shutdown()
    time.sleep(0.5)
    _log_obj = CAN.Log(log_info=CAN.LogInfo(log_start_time=_log_start_time, log_end_time=datetime.datetime.now(), original_file_name=_file_name, tester_name=("%s" % os.getenv("USERNAME"))), channel_info=_bus.channel_info, machine_info=CAN.get_host_machine_info(), message_lists=[CAN.MessageList(messages=_message_list)])
    with open(_log_file_path, "wb") as _log_file:
        cPickle.dump(_log_obj, _log_file)

