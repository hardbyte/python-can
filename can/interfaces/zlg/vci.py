'''
Wrap libusbcanfd.so
'''

#######################################################################
# For consistency, use the coding style and definitions 
#   as similar as USBCANFD_DEMO.py in Linux driver package
#   https://manual.zlg.cn/web/#/146
#######################################################################

import logging

from enum import unique, auto, Enum, Flag
from ctypes import c_ubyte, c_uint8, c_uint16, c_uint32 
from ctypes import cdll, byref, Structure


log = logging.getLogger('can.zlg')
lib = cdll.LoadLibrary('libusbcanfd.so')

ZCAN_DEVICE_TYPE  = c_uint32
ZCAN_DEVICE_INDEX = c_uint32
ZCAN_CHANNEL      = c_uint32


@unique
class ZCAN_DEVICE(Enum):
    '''CAN Device Type
       Only USBCAN / USBCANFD_200U supported now
       For more infomation, please check
       https://manual.zlg.cn/web/#/188/6984
    '''
    USBCAN          =   4
    USBCANFD_200U   =   33


class ZCAN_MODE(Flag):
    LISTEN_ONLY =   auto()  # 0: Normal, 1: Listen only
    BOSCH       =   auto()  # 0: ISO, 1: BOSCH
    NORMAL      =   (~LISTEN_ONLY & ~BOSCH) & 0x03


@unique
class ZCAN_REF(Enum):
    FILTER      =   0x14    # CAN Message Filter
    TRES        =   0x18    # Termination resistor
    TX_TIMEOUT  =   0x44    # Send timeout in ms
    TTX_SETTING =   0x16    # Timing send settins
    TTX_ENABLE  =   0x17    # Timing send enable

    @property
    def value(self) -> c_uint32:
        return c_uint32(super().value)


class ZCAN_TRES(Structure): # Termination resistor
    ON  = 1
    OFF = 0
    _fields_=[
        ('enable', c_uint8)
    ]


class ZCAN_MSG_INFO(Structure):
    _fields_ = [
        ('txm', c_uint32, 4),   # TXTYPE, 0: normal, 1: once, 2: self
        ('fmt', c_uint32, 4),   # 0:CAN2.0, 1:CANFD
        ('sdf', c_uint32, 1),   # 0: data frame, 1: remote frame
        ('sef', c_uint32, 1),   # 0: std frame, 1: ext frame
        ('err', c_uint32, 1),   # error flag
        ('brs', c_uint32, 1),   # bit-rate switch, 0: Not speed up, 1: speed up
        ('est', c_uint32, 1),   # error state 
        ('pad', c_uint32, 19)
    ]


class ZCAN_MSG_HDR(Structure):  
    _fields_ = [
        ('ts',      c_uint32),      # timestamp
        ('id',      c_uint32),      # can-id
        ('info',    ZCAN_MSG_INFO),
        ('pad',     c_uint16),
        ('chn',     c_uint8),       # channel
        ('len',     c_uint8)        # data length
    ]


class ZCAN_20_MSG(Structure):  
    _fields_ = [
        ('header',  ZCAN_MSG_HDR),
        ('dat',     c_ubyte*8)
    ]


class ZCAN_FD_MSG(Structure):  
    _fields_ = [
        ('header',  ZCAN_MSG_HDR),
        ('dat',     c_ubyte*64)
    ]


class ZCAN_ERR_MSG(Structure):  
    _fields_ = [
        ('header',  ZCAN_MSG_HDR),
        ('dat',     c_ubyte*8)
    ]


class ZCAN_BIT_TIMING(Structure):
    _fields_ = [
        ('tseg1',   c_uint8),
        ('tseg2',   c_uint8),
        ('sjw',     c_uint8),
        ('smp',     c_uint8),   # Not used
        ('brp',     c_uint16)
    ]


class ZCANFD_INIT(Structure):
    _fields_ = [
        ('clk',     c_uint32),
        ('mode',    c_uint32),
        ('atim',    ZCAN_BIT_TIMING),
        ('dtim',    ZCAN_BIT_TIMING)
    ]


def vci_device_open(type_, index) -> bool:
    ret = lib.VCI_OpenDevice(type_, index)
    if ret == 0:
        log.error(f'Failed to open device {type_}:{index} !')
    else:
        log.info(f'Open device {type_}:{index} successfully!')
    return ret != 0


def vci_device_close(type_, index) -> bool:
    ret = lib.VCI_CloseDevice(type_, index)
    if ret == 0:
        log.error(f'Failed to open device {type_}:{index}')
    else:
        log.info(f'Open device {type_}:{index} successfully')
    return ret != 0


def vci_channel_open(type_, index, channel,
                     clock,
                     atiming,
                     dtiming=None,
                     mode=ZCAN_MODE.NORMAL
    ) -> bool:
    init = ZCANFD_INIT()
    init.mode   =   mode.value
    init.clk    =   clock
    init.atim   =   atiming
    init.dtim   =   dtiming or atiming
    ret = lib.VCI_InitCAN(type_, index, channel, byref(init))
    if ret == 0:
        log.error(f'CH{channel.value}: Initialize failed')
    else:
        log.info(f'CH{channel.value}: Initialized')
        ret = lib.VCI_StartCAN(type_, index, channel)
        if ret == 0:
            log.error(f'CH{channel.value}: Start failed')
        else:
            log.info(f'CH{channel.value}: Started')
    return ret != 0

def vci_channel_close(type_, index, channel) -> bool:
    ret = lib.VCI_ResetCAN(type_, index, channel)
    if ret == 0:
        log.error(f'CH{channel.value}: Close failed')
    else:
        log.info(f'CH{channel.value}: Closed')
    return ret != 0


def vci_channel_read_info(type_, index, channel, info) -> bool:
    ret = lib.VCI_ReadErrInfo(type_, index, channel, byref(info))
    if ret == 0:
        log.error(f'CH{channel.value}: Failed to read error infomation')
    else:
        log.info(f'CH{channel.value}: Read error infomation successfully')
    return ret != 0


def vci_channel_enable_tres(type_, index, channel, value) -> bool:
    tres = ZCAN_TRES(enable=ZCAN_TRES.ON if value else ZCAN_TRES.OFF)
    ret = lib.VCI_SetReference(type_, index, channel, ZCAN_REF.TRES.value, byref(tres))
    if ret == 0:
        log.error(f'CH{channel.value}: Failed to {"enable" if value else "disable"} '
                  f'termination resistor')
    else:
        log.info(f'CH{channel.value}: {"Enable" if value else "Disable"} '
                 f'termination resistor successfully')
    return ret != 0


def vci_can_send(type_, index, channel, msgs, count) -> int:
    ret = lib.VCI_Transmit(type_, index, channel, byref(msgs), count)
    if ret == 0:
        log.error(f'CH{channel.value}: Failed to send CAN message(s)')
    else:
        log.debug(f'CH{channel.value}: Sent {len(msgs)} CAN message(s)')
    return ret


def vci_canfd_send(type_, index, channel, msgs, count) -> int:
    ret = lib.VCI_TransmitFD(type_, index, channel, byref(msgs), count)
    if ret == 0:
        log.error(f'CH{channel.value}: Failed to send CANFD message(s)')
    else:
        log.debug(f'CH{channel.value}: Sent {len(msgs)} CANFD message(s)')
    return ret


def vci_can_recv(type_, index, channel, msgs, count, timeout) -> int:
    ret = lib.VCI_Receive(type_, index, channel, byref(msgs), count, timeout)
    log.debug(f'CH{channel.value}: Received {len(msgs)} CAN message(s)')
    return ret


def vci_canfd_recv(type_, index, channel, msgs, count, timeout) -> int:
    ret = lib.VCI_ReceiveFD(type_, index, channel, byref(msgs), count, timeout)
    log.debug(f'CH{channel.value}: Received {len(msgs)} CANFD message(s)')
    return ret


def vci_can_get_recv_num(type_, index, channel) -> int:
    ret = lib.VCI_GetReceiveNum(type_, index, channel)
    log.debug(f'CH{channel.value}: {ret} CAN message(s) in FIFO')
    return ret


def vci_canfd_get_recv_num(type_, index, channel) -> int:
    if isinstance(channel, c_uint32):
        channel = c_uint32(channel.value | 0x80000000)
    else:
        channel = c_uint32(int(channel) | 0x80000000)
    ret = lib.VCI_GetReceiveNum(type_, index, channel)
    log.debug(f'CH{channel.value&0x7FFF_FFFF}: {ret} CANFD message(s) in FIFO')
    return ret
