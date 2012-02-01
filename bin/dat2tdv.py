"""
Converts pickled (*.dat) log files generated
by can_logger.py and the WriteLog ipython utility to human-readable
tab-delimited values format.
"""

import cPickle
import os
import sys

from pycanlib import CAN

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "rb") as _in_file:
                _log = cPickle.load(_in_file)
            _path = os.path.dirname(sys.argv[1])
            if len(_path) == 0:
                _path = "./"
            _log.write_to_file(format=CAN.LOG_FORMAT_TDV, name=("%s.log" % os.path.splitext(sys.argv[1])[0]), path=_path)
        except IOError:
            sys.stderr.write("ERROR: Input file %s not found\n" % sys.argv[1])
