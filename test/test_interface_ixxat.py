"""
Unittest for ixxat interface.

Copyright (C) 2019 Marcel Kanter <marcel.kanter@googlemail.com>
"""

import unittest

import can

from can import CanInitializationError


class InterfaceIxxatTestCase(unittest.TestCase):
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
		
		# non-existent channel -> use arbitrary high value
		with self.assertRaises(CanInitializationError):
			bus = can.Bus(interface = 'ixxat', channel = 0xFFFFFFFFF)

if __name__ == '__main__':
	unittest.main()