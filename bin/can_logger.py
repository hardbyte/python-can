import cPickle
import datetime
import logging
import optparse
import os
import time

from pycanlib import CAN

class _CANLoggerListener(CAN.Listener):

    def __init__(self, logger):
        self.msg_list = []
        self.__logger = logger

    def on_message_received(self, msg):
        self.__logger.info(msg)
        self.msg_list.append(msg)

if __name__ == "__main__":
    _parser = optparse.OptionParser()
    _parser.add_option("-c", "--channel", type="int", dest="channel", help="CAN channel number", default="0")
    _parser.add_option("-s", "--speed", type="int", dest="speed", help="CAN bus speed", default="105263")
    _parser.add_option("-t", "--tseg1", type="int", dest="tseg1", help="CAN bus tseg1", default="10")
    _parser.add_option("-u", "--tseg2", type="int", dest="tseg2", help="CAN bus tseg2", default="8")
    _parser.add_option("-w", "--sjw", type="int", dest="sjw", help="CAN bus SJW", default="4")
    _parser.add_option("-n", "--num_samples", type="int", dest="no_samp", help="CAN bus sample number", default="1")
    _parser.add_option("-l", "--log_file_name_base", dest="log_file_name_base", help="Base log file name, where log file names are <base>_<datestamp>_<timestamp>", default="can_logger")
    _parser.add_option("-p", "--log_file_path", dest="log_file_path", help="Log file path", default="can_logger")
    (_options, _args) = _parser.parse_args()
    _bus = CAN.Bus(channel=_options.channel, speed=_options.speed, tseg1=_options.tseg1, tseg2=_options.tseg2, sjw=_options.sjw, no_samp=_options.no_samp)
    _logger = logging.getLogger("can_logger")
    _logger.setLevel(logging.INFO)
    _log_handler = logging.StreamHandler()
    _log_formatter = logging.Formatter("%(message)s")
    _log_handler.setFormatter(_log_formatter)
    _logger.addHandler(_log_handler)
    _log_timestamp = datetime.datetime.now()
    _log_start_time = _log_timestamp
    _timestamp_string = _log_timestamp.strftime("%Y%m%d_%H%M%S")
    _log_file_path = os.path.join(os.path.expanduser("~"), "%s" % _options.log_file_path, "%s_%s.dat" % (_options.log_file_name_base, _timestamp_string))
    _file_name = os.path.basename(_log_file_path)
    if not os.path.exists(os.path.dirname(_log_file_path)):
        os.makedirs(os.path.dirname(_log_file_path))
    _log_file = open(_log_file_path, "wb")
    _logger_listener = _CANLoggerListener(_logger)
    _bus.add_listener(_logger_listener)
    try:
        _bus.enable_callback()
        while True:
            time.sleep(0.001)
    except KeyboardInterrupt:
        pass
    finally:
        _bus.shutdown()
    _log_obj = CAN.Log(log_info=CAN.LogInfo(log_start_time=_log_start_time, log_end_time=datetime.datetime.now(), original_file_name=_file_name, tester_name=os.getenv("USERNAME")), channel_info=_bus.channel_info, machine_info=CAN.get_host_machine_info(), message_lists=[CAN.MessageList(messages=_logger_listener.msg_list)])
    cPickle.dump(_log_obj, _log_file)
    _log_file.close()
