import cPickle
import os
import sys

from pycanlib import CAN

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "rb") as _in_file:
                _log = cPickle.load(_in_file)
            _log.write_to_file(format=CAN.LOG_FORMAT_TDV, name=("%s.log" % os.path.splitext(_options.input_file)[0]), path=os.path.dirname(_options.input_file))
        except IOError:
            sys.stderr.write("ERROR: Input file %s not found\n" % sys.argv[1])
