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


def vci_device_open(dt, di) -> bool:
    ret = lib.VCI_OpenDevice(c_uint32(dt), c_uint32(di))
    if ret == 0:
        log.error(f'Failed to open device {dt}:{di} !')
    else:
        log.info(f'Open device {dt}:{di} successfully!')
    return ret != 0


def vci_device_close(dt, di) -> bool:
    ret = lib.VCI_CloseDevice(c_uint32(dt), c_uint32(di))
    if ret == 0:
        log.error(f'Failed to open device {dt}:{di}')
    else:
        log.info(f'Open device {dt}:{di} successfully')
    return ret != 0


def vci_channel_open(dt, di, ch,
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
    ret = lib.VCI_InitCAN(c_uint32(dt), c_uint32(di), c_uint32(ch), byref(init))
    if ret == 0:
        log.error(f'CH{ch}: Initialize failed')
    else:
        log.info(f'CH{ch}: Initialized')
        ret = lib.VCI_StartCAN(c_uint32(dt), c_uint32(di), c_uint32(ch))
        if ret == 0:
            log.error(f'CH{ch}: Start failed')
        else:
            log.info(f'CH{ch}: Started')
    return ret != 0

def vci_channel_close(dt, di, ch) -> bool:
    ret = lib.VCI_ResetCAN(c_uint32(dt), c_uint32(di), c_uint32(ch))
    if ret == 0:
        log.error(f'CH{ch}: Close failed')
    else:
        log.info(f'CH{ch}: Closed')
    return ret != 0


def vci_channel_read_info(dt, di, ch, info) -> bool:
    ret = lib.VCI_ReadErrInfo(c_uint32(dt), c_uint32(di), c_uint32(ch), byref(info))
    if ret == 0:
        log.error(f'CH{ch}: Failed to read error infomation')
    else:
        log.info(f'CH{ch}: Read error infomation successfully')
    return ret != 0


def vci_channel_enable_tres(dt, di, ch, value) -> bool:
    ref = ZCAN_REF.TRES.value
    tres = ZCAN_TRES(enable=ZCAN_TRES.ON if value else ZCAN_TRES.OFF)
    ret = lib.VCI_SetReference(c_uint32(dt), c_uint32(di), c_uint32(ch), c_uint32(ref), byref(tres))
    if ret == 0:
        log.error(f'CH{ch}: Failed to {"enable" if value else "disable"} '
                  f'termination resistor')
    else:
        log.info(f'CH{ch}: {"Enable" if value else "Disable"} '
                 f'termination resistor successfully')
    return ret != 0


def vci_can_send(dt, di, ch, msgs, count) -> int:
    ret = lib.VCI_Transmit(c_uint32(dt), c_uint32(di), c_uint32(ch), byref(msgs), c_uint32(count))
    if ret == 0:
        log.error(f'CH{ch}: Failed to send CAN message(s)')
    else:
        log.debug(f'CH{ch}: Sent {len(msgs)} CAN message(s)')
    return ret


def vci_canfd_send(dt, di, ch, msgs, count) -> int:
    ret = lib.VCI_TransmitFD(c_uint32(dt), c_uint32(di), c_uint32(ch), byref(msgs), c_uint32(count))
    if ret == 0:
        log.error(f'CH{ch}: Failed to send CANFD message(s)')
    else:
        log.debug(f'CH{ch}: Sent {len(msgs)} CANFD message(s)')
    return ret


def vci_can_recv(dt, di, ch, msgs, count, timeout) -> int:
    ret = lib.VCI_Receive(c_uint32(dt), c_uint32(di), c_uint32(ch), byref(msgs), c_uint32(count), c_uint32(timeout))
    log.debug(f'CH{ch}: Received {len(msgs)} CAN message(s)')
    return ret


def vci_canfd_recv(dt, di, ch, msgs, count, timeout) -> int:
    ret = lib.VCI_ReceiveFD(c_uint32(dt), c_uint32(di), c_uint32(ch), byref(msgs), c_uint32(count), c_uint32(timeout))
    log.debug(f'CH{ch}: Received {len(msgs)} CANFD message(s)')
    return ret


def vci_can_get_recv_num(dt, di, ch) -> int:
    ret = lib.VCI_GetReceiveNum(c_uint32(dt), c_uint32(di), c_uint32(ch))
    log.debug(f'CH{ch}: {ret} CAN message(s) in FIFO')
    return ret


def vci_canfd_get_recv_num(dt, di, ch) -> int:
    ch = ch | 0x80000000
    ret = lib.VCI_GetReceiveNum(c_uint32(dt), c_uint32(di), c_uint32(ch))
    log.debug(f'CH{ch&0x7FFF_FFFF}: {ret} CANFD message(s) in FIFO')
    return ret
