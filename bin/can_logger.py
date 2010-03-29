import cPickle
import datetime
import logging
import optparse
import os
import sys
import time

from pycanlib import CAN, canlib


class _CANLoggerListener(CAN.Listener):

    def __init__(self, logger):
        self.msg_list = []
        self.__logger = logger

    def on_message_received(self, msg):
        self.__logger.info(msg)
        self.msg_list.append(msg)

def _parse_arguments(arguments):
    parser = optparse.OptionParser(" ".join(arguments[1:]))
    parser.add_option("-c", "--channel", dest="channel", help="CAN channel number", default="0")
    parser.add_option("-s", "--speed", dest="speed", help="CAN bus speed", default="105263")
    parser.add_option("-t", "--tseg1", dest="tseg1", help="CAN bus tseg1", default="10")
    parser.add_option("-u", "--tseg2", dest="tseg2", help="CAN bus tseg2", default="8")
    parser.add_option("-w", "--sjw", dest="sjw", help="CAN bus SJW", default="4")
    parser.add_option("-n", "--noSamp", dest="no_samp", help="CAN bus sample number", default="1")
    parser.add_option("-l", "--logFileNameBase", dest="log_file_name_base", help="Base log file name, where log file names are <base>_<datestamp>_<timestamp>", default="can_logger")
    parser.add_option("-p", "--logFilePath", dest="log_file_path", help="Log file path", default="can_logger")
    return parser.parse_args()

def _create_bus_object(options):
    _channel = int(options.channel)
    _speed = int(options.speed)
    _tseg1 = int(options.tseg1)
    _tseg2 = int(options.tseg2)
    _sjw = int(options.sjw)
    _no_samp = int(options.no_samp)
    return CAN.Bus(channel=_channel, speed=_speed, tseg1=_tseg1, tseg2=_tseg2, sjw=_sjw, no_samp=_no_samp)

def _setup_logging(file_path, file_name_base):
    _logger = logging.getLogger("can_logger")
    _logger.setLevel(logging.INFO)
    _log_handler = logging.StreamHandler()
    _log_formatter = logging.Formatter("%(message)s")
    _log_handler.setFormatter(_log_formatter)
    _logger.addHandler(_log_handler)
    _log_timestamp = datetime.datetime.now()
    _timestamp_string = _log_timestamp.strftime("%Y%m%d_%H%M%S")
    _log_file_path = os.path.join(os.path.expanduser("~"), "%s" % file_path, "%s_%s.dat" % (file_name_base, _timestamp_string))
    if not os.path.exists(os.path.dirname(_log_file_path)):
        os.makedirs(os.path.dirname(_log_file_path))
    _log_file = open(_log_file_path, "wb")
    return _logger, _log_file, os.path.basename(_log_file_path), _log_timestamp

def main(arguments):
    (options, args) = _parse_arguments(arguments)
    bus = _create_bus_object(options)
    (_logger, _log_file, _file_name, _log_start_time) = _setup_logging(options.log_file_path, options.log_file_name_base)
    _logger_listener = _CANLoggerListener(_logger)
    bus.add_listener(_logger_listener)
    try:
        bus.enable_callback()
        while True:
            time.sleep(0.001)
    except KeyboardInterrupt:
        bus.shutdown()
    _log_info = CAN.LogInfo(log_start_time=_log_start_time, log_end_time=datetime.datetime.now(), original_file_name=_file_name, tester_name=os.getenv("USERNAME"))
    _channel_info = bus.channel_info
    _machine_info = CAN.get_host_machine_info()
    _message_lists = [CAN.MessageList(messages=_logger_listener.msg_list)]
    _log_obj = CAN.Log(log_info=_log_info, channel_info=_channel_info, machine_info=_machine_info, message_lists=_message_lists)
    cPickle.dump(_log_obj, _log_file)
    _log_file.close()

if __name__ == "__main__":
    main(sys.argv)
