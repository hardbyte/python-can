"""
Exception classes.

Copyright (c) Marcel Kanter
"""

class CanError(Exception):
	""" Base class for all can related exceptions.
	"""
	pass


class CanInitializationError(CanError):
	""" Indicates an error related to the initialization.
	"""
	pass


class CanOperationError(CanError):
	""" Indicates an error while operation.
	For example:
	ACK error (e.g. only one bus member)
	Stuff, CRC error (e.g. malformed message)
	"""
	pass