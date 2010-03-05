import types

class pycanlibError(Exception):
    def __init__(self, parameter_name, parameter_value, function_name, reason):
        self.__parameter_name = parameter_name
        self.__parameter_value = parameter_value
        self.__function_name = function_name
        self.__reason = reason

    @property
    def parameter_name(self):
        return self.__parameter_name

    @property
    def parameter_value(self):
        return self.__parameter_value

    @property
    def function_name(self):
        return self.__function_name

    @property
    def reason(self):
        return self.__reason

    def __str__(self):
        return "%s: Bad parameter '%s' (%s, type %s) to function '%s' - reason '%s'" % (self.__class__.__name__, self.parameter_name, self.parameter_value, type(self.parameter_value), self.function_name, self.reason)

class ParameterTypeError(pycanlibError):
    pass

class ParameterRangeError(pycanlibError):
    pass

class ParameterValueError(pycanlibError):
    pass

def verify_parameter_type(function, parameter_name, parameter_value, allowable_types):
    if not isinstance(parameter_value, allowable_types):
        raise ParameterTypeError(parameter_name, parameter_value, function, ("Not one of the allowable types %s" % (allowable_types,)))

def verify_parameter_range(function, parameter_name, parameter_value, allowable_range):
    if parameter_value not in allowable_range:
        raise ParameterRangeError(parameter_name, parameter_value, function, ("Not in the allowable range %s" % (allowable_range,)))

def verify_parameter_min_value(function, parameter_name, parameter_value, min_value):
    if parameter_value < min_value:
        raise ParameterRangeError(parameter_name, parameter_value, function, ("Value less than minimum of %s" % (min_value,)))

def verify_parameter_max_value(function, parameter_name, parameter_value, max_value):
    if parameter_value > max_value:
        raise ParameterRangeError(parameter_name, parameter_value, function, ("Value greater than maximum of %s" % (max_value,)))

def verify_parameter_value_in_set(function, parameter_name, parameter_value, allowable_set):
    if parameter_value not in allowable_set:
        raise ParameterValueError(parameter_name, parameter_value, function, ("Value not in allowable set %s" % (allowable_set,)))

def verify_parameter_value_equal_to(function, parameter_name, parameter_value, allowable_value):
    verify_parameter_value_in_set(function, parameter_name, parameter_value, [allowable_value])
