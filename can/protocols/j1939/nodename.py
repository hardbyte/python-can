from .constants import j1939_industry_groups


class NodeName(object):

    def __init__(self, value=0):
        self.value = value

    @property
    def value(self):
        retval = self.identity_number
        retval += (self.manufacturer_code << 21)
        retval += (self.ecu_instance << 32)
        retval += (self.function_instance << 35)
        retval += (self.function << 40)
        retval += (self.reserved_bit << 48)
        retval += (self.vehicle_system << 49)
        retval += (self.vehicle_system_instance << 56)
        retval += (self.industry_group << 60)
        retval += (self.arbitrary_address_capable << 63)
        return retval

    @value.setter
    def value(self, value):
        """
        Value should be a number between [0, (2 ** 64) - 1]
        """
        self.identity_number = value & ((2 ** 21) - 1)
        self.manufacturer_code = (value >> 21) & ((2 ** 11) - 1)
        self.ecu_instance = (value >> 32) & ((2 ** 3) - 1)
        self.function_instance = (value >> 35) & ((2 ** 5) - 1)
        self.function = (value >> 40) & ((2 ** 8) - 1)
        self.reserved_bit = (value >> 48) & 1
        self.vehicle_system = (value >> 49) & ((2 ** 7) - 1)
        self.vehicle_system_instance = (value >> 56) & ((2 ** 4) - 1)
        self.industry_group = (value >> 60) & ((2 ** 3) - 1)
        self.arbitrary_address_capable = (value >> 63) & 1

    @property
    def arbitrary_address_capable(self):
        return self.__arbitrary_address_capable

    @arbitrary_address_capable.setter
    def arbitrary_address_capable(self, value):
        """Should evaluate to True or False"""
        self.__arbitrary_address_capable = bool(value)

    @property
    def industry_group(self):
        return self.__industry_group

    @industry_group.setter
    def industry_group(self, value):
        """
        Value should be in j1939_industry_groups
        """
        assert value in j1939_industry_groups
        self.__industry_group = value

    @property
    def vehicle_system_instance(self):
        return self.__vehicle_system_instance

    @vehicle_system_instance.setter
    def vehicle_system_instance(self, value):
        """
        An int between 0 and 15.
        """
        self.__vehicle_system_instance = value

    @property
    def vehicle_system(self):
        return self.__vehicle_system

    @vehicle_system.setter
    def vehicle_system(self, value):
        """
        An int between 0 and (2 ** 7) - 1.
        """
        self.__vehicle_system = value

    @property
    def reserved_bit(self):
        return self.__reserved_bit

    @reserved_bit.setter
    def reserved_bit(self, value):
        self.__reserved_bit = bool(value)

    @property
    def function(self):
        return self.__function

    @function.setter
    def function(self, value):
        """
        An int between 0 and (2 ** 8) - 1
        """
        self.__function = value

    @property
    def function_instance(self):
        return self.__function_instance

    @function_instance.setter
    def function_instance(self, value):
        """
        Int between 0 and (2 ** 5) - 1
        """
        self.__function_instance = value

    @property
    def ecu_instance(self):
        return self.__ecu_instance

    @ecu_instance.setter
    def ecu_instance(self, value):
        """
        Int between 0 and (2 ** 3) - 1
        """
        self.__ecu_instance = value

    @property
    def manufacturer_code(self):
        return self.__manufacturer_code

    @manufacturer_code.setter
    def manufacturer_code(self, value):
        """
        Int between 0 and (2 ** 11) - 1
        """
        self.__manufacturer_code = value

    @property
    def identity_number(self):
        return self.__identity_number

    @identity_number.setter
    def identity_number(self, value):
        """
        Int between 0 and (2 ** 21) - 1
        """
        self.__identity_number = value

    @property
    def bytes(self):
        return [
            (self.value & (0xFF << 56)) >> 56,
            (self.value & (0xFF << 48)) >> 48,
            (self.value & (0xFF << 40)) >> 40,
            (self.value & (0xFF << 32)) >> 32,
            (self.value & (0xFF << 24)) >> 24,
            (self.value & (0xFF << 16)) >> 16,
            (self.value & (0xFF << 8)) >> 8,
            (self.value & 0xFF)
        ]

    @bytes.setter
    def bytes(self, value):
        """
        A list of ints between 0 and (2 ** 8) - 1

        """
        # TODO use python's builtin bytes type
        self.value = int("".join("%.2X" % _byte for _byte in value), 16)

    def __str__(self):
        return "%.16X" % self.value

    def __repr__(self):
        return self.__str__()
