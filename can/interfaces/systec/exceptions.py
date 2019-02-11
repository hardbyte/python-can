# coding: utf-8

from .constants import ReturnCode
from can import CanError


class UcanException(CanError):
    """ Base class for USB can errors. """
    def __init__(self, result, func, arguments):
        self.result = result.value
        self.func = func
        self.arguments = arguments
        self.return_msgs = NotImplemented

    def __str__(self):
        return "Function %s returned %d: %s" % \
               (self.func.__name__, self.result, self.return_msgs.get(self.result, "unknown"))


class UcanError(UcanException):
    """ Exception class for errors from USB-CAN-library. """
    def __init__(self, result, func, arguments):
        super(UcanError, self).__init__(result, func, arguments)
        self.return_msgs = {
            ReturnCode.ERR_RESOURCE: "could not created a resource (memory, handle, ...)",
            ReturnCode.ERR_MAXMODULES: "the maximum number of opened modules is reached",
            ReturnCode.ERR_HWINUSE: "the specified module is already in use",
            ReturnCode.ERR_ILLVERSION: "the software versions of the module and library are incompatible",
            ReturnCode.ERR_ILLHW: "the module with the specified device number is not connected "
                                          "(or used by an other application)",
            ReturnCode.ERR_ILLHANDLE: "wrong USB-CAN-Handle handed over to the function",
            ReturnCode.ERR_ILLPARAM: "wrong parameter handed over to the function",
            ReturnCode.ERR_BUSY: "instruction can not be processed at this time",
            ReturnCode.ERR_TIMEOUT: "no answer from module",
            ReturnCode.ERR_IOFAILED: "a request to the driver failed",
            ReturnCode.ERR_DLL_TXFULL: "a CAN message did not fit into the transmit buffer",
            ReturnCode.ERR_MAXINSTANCES: "maximum number of applications is reached",
            ReturnCode.ERR_CANNOTINIT: "CAN interface is not yet initialized",
            ReturnCode.ERR_DISCONECT: "USB-CANmodul was disconnected",
            ReturnCode.ERR_NOHWCLASS: "the needed device class does not exist",
            ReturnCode.ERR_ILLCHANNEL: "illegal CAN channel",
            ReturnCode.ERR_RESERVED1: "reserved",
            ReturnCode.ERR_ILLHWTYPE: "the API function can not be used with this hardware",
        }


class UcanCmdError(UcanException):
    """ Exception class for errors from firmware in USB-CANmodul."""
    def __init__(self, result, func, arguments):
        super(UcanCmdError, self).__init__(result, func, arguments)
        self.return_msgs = {
            ReturnCode.ERRCMD_NOTEQU: "the received response does not match to the transmitted command",
            ReturnCode.ERRCMD_REGTST: "no access to the CAN controller",
            ReturnCode.ERRCMD_ILLCMD: "the module could not interpret the command",
            ReturnCode.ERRCMD_EEPROM: "error while reading the EEPROM",
            ReturnCode.ERRCMD_RESERVED1: "reserved",
            ReturnCode.ERRCMD_RESERVED2: "reserved",
            ReturnCode.ERRCMD_RESERVED3: "reserved",
            ReturnCode.ERRCMD_ILLBDR: "illegal baud rate value specified in BTR0/BTR1 for systec "
                                              "USB-CANmoduls",
            ReturnCode.ERRCMD_NOTINIT: "CAN channel is not initialized",
            ReturnCode.ERRCMD_ALREADYINIT: "CAN channel is already initialized",
            ReturnCode.ERRCMD_ILLSUBCMD: "illegal sub-command specified",
            ReturnCode.ERRCMD_ILLIDX: "illegal index specified (e.g. index for cyclic CAN messages)",
            ReturnCode.ERRCMD_RUNNING: "cyclic CAN message(s) can not be defined because transmission of "
                                               "cyclic CAN messages is already running",
        }


class UcanWarning(UcanException):
    """ Exception class for warnings, the function has been executed anyway. """
    def __init__(self, result, func, arguments):
        super(UcanWarning, self).__init__(result, func, arguments)
        self.return_msgs = {
            ReturnCode.WARN_NODATA: "no CAN messages received",
            ReturnCode.WARN_SYS_RXOVERRUN: "overrun in receive buffer of the kernel driver",
            ReturnCode.WARN_DLL_RXOVERRUN: "overrun in receive buffer of the USB-CAN-library",
            ReturnCode.WARN_RESERVED1: "reserved",
            ReturnCode.WARN_RESERVED2: "reserved",
            ReturnCode.WARN_FW_TXOVERRUN: "overrun in transmit buffer of the firmware (but this CAN message "
                                                  "was successfully stored in buffer of the ibrary)",
            ReturnCode.WARN_FW_RXOVERRUN: "overrun in receive buffer of the firmware (but this CAN message "
                                                  "was successfully read)",
            ReturnCode.WARN_FW_TXMSGLOST: "reserved",
            ReturnCode.WARN_NULL_PTR: "pointer is NULL",
            ReturnCode.WARN_TXLIMIT: "not all CAN messages could be stored to the transmit buffer in "
                                             "USB-CAN-library",
            ReturnCode.WARN_BUSY: "reserved"
        }
