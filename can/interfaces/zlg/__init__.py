'''
Unofficial ZLG USBCAN/USBCANFD implementation for Linux
'''

__version__ = '1.1'
__date__    = '20220126'
__author__  = 'Keelung.Yang@flex.com'
__history__ = '''
    1. Initial creation, Keelung.Yang@flex.com, 2022-01-06
    2. Add bus padding support, Keelung.Yang@flex.com, 2022-01-26
'''

from can.interfaces.zlg.bus import ZlgCanBus
