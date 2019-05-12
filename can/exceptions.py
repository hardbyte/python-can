"""
Exception classes.
"""

class CanError(Exception):
	""" Base class for all can related exceptions.
	"""
	pass


class CanBackEndError(CanError):
	""" Indicates an error related to the backend (e.g. driver/OS/library)
	Examples:
	- A call to a library function results in an unexpected return value
	"""
	pass


class CanInitializationError(CanError):
	""" Indicates an error related to the initialization.
	Examples for situations when this exception may occur:
	- Try to open a non-existent device and/or channel
	- Try to use an invalid setting, which is ok by value, but not ok for the interface
	"""
	pass


class CanOperationError(CanError):
	""" Indicates an error while in operation.
	"""
	pass


class CanTimeoutError(CanError):
	""" Indicates a timeout of an operation.
	"""
	pass
