from constants import *

class Message(object):
    """
    Represents a CAN message.
    """
    
    def __init__(self, timestamp=0.0, is_remote_frame=False, extended_id=False,
                 is_wakeup=False, is_error_frame=False, arbitration_id=0, 
                 dlc=None, data=None):

        self.timestamp = timestamp
        self.id_type = extended_id

        self.is_remote_frame = is_remote_frame
        self.is_wakeup = is_wakeup
        self.is_error_frame = is_error_frame
        self.arbitration_id = arbitration_id
        
        if data is None:
            data = []
        self.data = bytearray(data)
        
        if dlc is None:
            self.dlc = len(data)
        else:
            self.dlc = dlc

    
    def __str__(self):
        field_strings = []
        field_strings.append("%15.6f" % self.timestamp)
        if self.flags & canMSG_EXT:
            arbitration_id_string = "%.8x" % self.arbitration_id
        else:
            arbitration_id_string = "%.4x" % self.arbitration_id
        field_strings.append(arbitration_id_string.rjust(8, " "))
        field_strings.append("%.4x" % self.flags)
        field_strings.append("%d" % self.dlc)
        data_strings = []
        if self.data != None:
            for byte in self.data:
                data_strings.append("%.2x" % byte)
        if len(data_strings) > 0:
            field_strings.append(" ".join(data_strings).ljust(24, " "))
        else:
            field_strings.append(" "*24)
        
        return "    ".join(field_strings).strip()

