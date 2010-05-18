import cPickle
import os
from optparse import OptionParser

from pycanlib import CAN

if __name__ == "__main__":
    _parser = OptionParser()
    _parser.add_option("-i", "--inputFile", dest="input_file", help="DAT file to decode")
    (_options, _args) = _parser.parse_args()
    with open(_options.input_file, "rb") as _in_file:
        _log = cPickle.load(_in_file)
    _log.write_to_file(format=CAN.LOG_FORMAT_TDV, name=("%s.log" % os.path.splitext(_options.input_file)[0]), path=os.path.dirname(_options.input_file))
