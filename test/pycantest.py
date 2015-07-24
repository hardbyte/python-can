#python-can test program to test an interface

import can
from can.interfaces.interface import Bus
import threading
from binascii import hexlify

can.rc['interface'] = 'usb2can'


#channel = None, can_filters=None ,

usb2can = can.interface.Bus(bustype = 'usb2can', serial = 'ED000200', flags = 0x00000008, baud = "500")

'''
m = can.Message(
                arbitration_id=self.ids[i],
                is_remote_frame=self.remote_flags[i],
                is_error_frame=self.error_flags[i],
                extended_id=self.extended_flags[i],
                data=self.data[i]
            )
'''

msg = can.Message(timestamp=0.0, is_remote_frame=False, extended_id=True, is_error_frame=False, arbitration_id=0, dlc=None, data=[0,1,2,3])			
			
			
usb2can.send(msg)




counter = 0

while counter is 0:
	rx = usb2can.recv(timeout=None)
	if rx is None:
		n = 5
		
	else:
		print ('\n')
		print ('\n')
		print str(hexlify(rx.data))
		print ('\n')
		print rx.timestamp
		print ('\n')
		print rx.is_remote_frame
		print ('\n')
		print rx.is_error_frame
		print ('\n')
		print rx.id_type
		print ('\n')
		print rx.dlc
		