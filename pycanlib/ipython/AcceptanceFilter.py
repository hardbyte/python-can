import ipipe

from pycanlib import CAN

class AcceptanceFilter(ipipe.Pipe):
    def __init__(self, std_acceptance_code=0, std_acceptance_mask=CAN.STD_ACCEPTANCE_MASK_ALL_BITS, ext_acceptance_code=0, ext_acceptance_mask=CAN.EXT_ACCEPTANCE_MASK_ALL_BITS):
        ipipe.Pipe.__init__(self)
        self.__filter = CAN.AcceptanceFilter(std_acceptance_code=std_acceptance_code, std_acceptance_mask=std_acceptance_mask, ext_acceptance_code=ext_acceptance_code, ext_acceptance_mask=ext_acceptance_mask)

    def __iter__(self):
        for _i, _item in enumerate(self.input):
            _item = self.__filter.filter_message(_item)
            if _item != None:
                yield _item
