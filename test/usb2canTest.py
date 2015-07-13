from usb2can import *
from ctypes import *
import ctypes
from binascii import hexlify
import time
import os
import sys
from sys import getsizeof

testString = c_char_p
testFlag = c_ulong
testFlag = 0x00000008
testString = 'ED000200; 250'
counter = c_long
counter = 0

file = open('output.txt', 'w')

#data = 00000000

data = '01234567'
j = tuple(int(z,16) for z in data)

converted = (c_ubyte * 8) (*j)
#print converted
	
msg = CanalMsg(80000000, 0, 11, 8, converted, counter)

#creates can object
	
can = usb2can ()
#returns device ID
device = can.CanalOpen(testString, testFlag)
   


bool = True


while(bool == True):
	
	received = can.CanalReceive(device, byref(msg))
	
	if(received != 8):
		file.write(str(received))
		file.write('\n')
		file.write(str(hexlify(string_at(msg.data, sizeof(msg.data)))))
	
file.flush()
file.close()

#test statement for sending
'''
while (bool == True):
	#prints device ID
	#print device
	#exit condition for loop
	condition = can.CanalSend(device, byref(msg))
	msg = CanalMsg(80000000, 0, 11, 8, converted, counter)
	print condition
	counter = counter + 1
	print counter
	time.sleep(1)
	if( counter == 1000):
		bool = False
'''
#condition = can.CanalSend(device, byref(msg))
#print condition




#sendError = can.CanalSend(device, )

#device is the device ID
test2 = can.CanalClose(device)
print test2
	

