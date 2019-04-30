"""
Unittest for ixxat interface.

Copyright (C) 2019 Marcel Kanter <marcel.kanter@googlemail.com>
"""

import unittest
import can

from can import CanError, CanBackEndError, CanInitializationError, CanOperationError

class SoftwareTestCase(unittest.TestCase):
	"""
	Test cases that test the software only and do not rely on an existing/connected hardware.
	"""
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_bus_creation(self):
		# channel must be >= 0
		with self.assertRaises(ValueError):
			bus = can.Bus(interface = 'ixxat', channel = -1)
		
		# rxFifoSize must be > 0
		with self.assertRaises(ValueError):
			bus = can.Bus(interface = 'ixxat', channel = 0, rxFifoSize = 0)
		
		# txFifoSize must be > 0
		with self.assertRaises(ValueError):
			bus = can.Bus(interface = 'ixxat', channel = 0, txFifoSize = 0)


class HardwareTestCase(unittest.TestCase):
	"""
	Test cases that rely on an existing/connected hardware.
	"""
	def setUp(self):
		try:
			bus = can.Bus(interface = 'ixxat', channel = 0)
		except:
			raise(unittest.SkipTest())
	
	def tearDown(self):
		pass
	
	def test_bus_creation(self):
		# non-existent channel -> use arbitrary high value
		with self.assertRaises(CanInitializationError):
			bus = can.Bus(interface = 'ixxat', channel = 0xFFFFFFFFF)
	
	def test_send_after_shutdown(self):
		bus = can.Bus(interface = 'ixxat', channel = 0)
		msg = can.Message(arbitration_id = 0x3FF, dlc = 0)
		bus.shutdown()
		with self.assertRaises(CanOperationError):
			bus.send(msg)


if __name__ == '__main__':
	unittest.main()