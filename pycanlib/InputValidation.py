"""
InputValidation.py: contains implementation of the input validation
functionality used in pycanlib.

Copyright (C) 2010 Dynamic Controls

E-mail: bpowell AT dynamiccontrols DOT com
"""
import types

class InputValidationError(Exception):
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
        return """Bad parameter '{self.parameter_name}'
with value: {self.parameter_value}
of type: {type_value}
passed to function '{self.function_name}'
Reason: '{self.reason}'""".format(self=self, type_value=type(self.parameter_value))

class ParameterTypeError(InputValidationError):
    pass

class ParameterRangeError(InputValidationError):
    pass

class ParameterValueError(InputValidationError):
    pass

def verify_parameter_type(function, parameter_name, parameter_value, allowable_types):
    if not isinstance(parameter_value, allowable_types):
        raise ParameterTypeError(parameter_name,
                                 parameter_value,
                                 function,
                                 "Not one of the allowable types:\n%s" % allowable_types
                                 )

def verify_parameter_list_type(function, parameter_name, list_parameter_value, allowable_types):
    if not isinstance(list_parameter_value, list):
        raise ParameterTypeError(parameter_name, 
                                 list_parameter_value,
                                 function,
                                 "Not a list")
    else:
        return all(verify_parameter_type(function, 
                                         parameter_name+'[%d]'%i, 
                                         obj, 
                                         allowable_types) 
                   for (i, obj) in enumerate(list_parameter_value))

def verify_parameter_range(function, parameter_name, parameter_value, allowable_range):
    if parameter_value not in allowable_range:
        raise ParameterRangeError(parameter_name, 
                                  parameter_value, 
                                  function, 
                                  "Not in the allowable range %s" % allowable_range)

def verify_parameter_min_value(function, parameter_name, parameter_value, min_value):
    if parameter_value < min_value:
        raise ParameterRangeError(parameter_name, 
                                  parameter_value, 
                                  function, 
                                  "Value less than minimum of %s" % min_value)

def verify_parameter_max_value(function, parameter_name, parameter_value, max_value):
    if parameter_value > max_value:
        raise ParameterRangeError(parameter_name, 
                                  parameter_value, 
                                  function, 
                                  "Value greater than maximum of %s" % max_value)

def verify_parameter_value_in_set(function, parameter_name, parameter_value, allowable_set):
    if parameter_value not in allowable_set:
        raise ParameterValueError(parameter_name, 
                                  parameter_value, 
                                  function, 
                                  "Value not in allowable set %s" % allowable_set)

def verify_parameter_value_equal_to(function, parameter_name, parameter_value, allowable_value):
    if not parameter_value == allowable_value:
        raise ParameterValueError(parameter_name, 
                                  parameter_value, function,
                                  "Value was not equal to %s" % allowable_value)
