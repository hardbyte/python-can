import types

class pycanlibError(Exception):
    pass

class ParameterTypeError(pycanlibError):
    pass

class ParameterRangeError(pycanlibError):
    pass

class ParameterValueError(pycanlibError):
    pass

def verify_parameter_type(function, parameter_name, parameter_value, allowable_types):
    if not isinstance(parameter_value, allowable_types):
        raise ParameterTypeError("%s - Type of parameter '%s' (%s) is not one of the allowable types %s" % (function, parameter_name, type(parameter_value), allowable_types))

def verify_parameter_range(function, parameter_name, parameter_value, allowable_range):
    if parameter_value not in allowable_range:
        raise ParameterRangeError("%s - Value of parameter '%s' (%s) is not in the range %s" % (function, parameter_name, parameter_value, allowable_range))

def verify_parameter_min_value(function, parameter_name, parameter_value, min_value):
    if parameter_value < min_value:
        raise ParameterRangeError("%s - Value of parameter '%s' (%s) is less than %s" % (function, parameter_name, parameter_value, min_value))

def verify_parameter_max_value(function, parameter_name, parameter_value, max_value):
    if parameter_value > max_value:
        raise ParameterRangeError("%s - Value of parameter '%s' (%s) is greater than %s" % (function, parameter_name, parameter_value, max_value))
