from ctypes import c_ubyte

from can.interfaces.systec.constants import ReturnCode
from can.interfaces.systec.exceptions import UcanError


def test_ucan_error_accepts_ctypes_result_code() -> None:
    def ucan_write_can_msg_ex() -> None:
        pass

    result = c_ubyte(ReturnCode.ERR_ILLPARAM)

    error = UcanError(result, ucan_write_can_msg_ex, ("arg",))

    assert error.error_code == ReturnCode.ERR_ILLPARAM
    assert "wrong parameter handed over to the function" in str(error)
