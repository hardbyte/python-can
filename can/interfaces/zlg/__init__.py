'''
Unofficial ZLG USBCAN/USBCANFD implementation for Linux
'''

__version__ = '1.2'
__date__    = '20220127'
__author__  = 'Keelung.Yang@flex.com'
__history__ = '''
    1. Initial creation, Keelung.Yang@flex.com, 2022-01-06
    2. Add bus padding support, Keelung.Yang@flex.com, 2022-01-26
    3. Determine CAN-FD by data_bitrate, Keelung.Yang@flex.com, 2022-01-27
'''

from can.interfaces.zlg.bus import ZlgCanBus
