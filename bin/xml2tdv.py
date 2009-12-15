import os.path
from optparse import OptionParser
import sys
from xml.dom import minidom

from pycanlib import CAN

def _convert_xml_to_tdv(xml_doc):
    retval = ""
    if len(xml_doc.getElementsByTagName("MachineInfo")) == 1:
        _machine_info = xml_doc.getElementsByTagName("MachineInfo")[0]
        retval += "%s" % CAN.MachineInfo(xml=_machine_info)
    else:
        raise Exception("Log documents must have exactly one MachineInfo element")
    if len(xml_doc.getElementsByTagName("ChannelInfo")) == 1:
        _channel_info = xml_doc.getElementsByTagName("ChannelInfo")[0]
        retval += "%s" % CAN.ChannelInfo(xml=_channel_info)
    else:
        raise Exception("Log documents must have exactly one ChannelInfo element")
    retval += "\n".join([CAN.Message(xml=_msg).__str__() for _msg in xml_doc.getElementsByTagName("Message")])
    return retval


if __name__ == "__main__":
    _parser = OptionParser()
    _parser.add_option("-f", "--inputFile", dest="input_file",
      help="XML file to decode")
    (_options, _args) = _parser.parse_args()
    _in_file = open(_options.input_file, "r")
    _out_file = open(("%s.log" % os.path.splitext(_options.input_file)[0]), "w")
    _log_data = "".join(_in_file.readlines()).replace("\t", "").replace("\n", "")
    _log_doc = minidom.parseString(_log_data)
    _in_file.close()
    _out_file.write(_convert_xml_to_tdv(_log_doc))
    _out_file.close()
