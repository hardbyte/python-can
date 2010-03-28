import cPickle
import os
from optparse import OptionParser

if __name__ == "__main__":
    _parser = OptionParser()
    _parser.add_option("-f", "--inputFile", dest="input_file", help="DAT file to decode")
    (_options, _args) = _parser.parse_args()
    _in_file = open(_options.input_file, "rb")
    _log = cPickle.load(_in_file)
    _in_file.close()
    _out_file = open(("%s.log" % os.path.splitext(_options.input_file)[0]), "w")
    _out_file.write("%s" % _log)
    _out_file.close()
