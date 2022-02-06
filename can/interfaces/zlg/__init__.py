'''
Unofficial ZLG USBCAN/USBCANFD implementation for Linux
'''

__version__ = '1.4'
__date__    = '20220128'
__author__  = 'Keelung.Yang@flex.com'
__history__ = '''
    1. Initial creation, Keelung.Yang@flex.com, 2022-01-06
    2. Determine CAN-FD by data_bitrate, Keelung.Yang@flex.com, 2022-01-27
    3. Remove bus padding since it should be handled in upper layer, Keelung.Yang@flex.com, 2022-01-28
    4. Balance receiving CAN/CAN-FD messages, Keelung.Yang@flex.com, 2022-02-06
'''

from can.interfaces.zlg.bus import ZlgCanBus
