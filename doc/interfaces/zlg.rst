.. _zlg:

ZLG USB CAN
===========


About
-----
Unofficial ZLG USBCAN/USBCANFD implementation for Linux

Author: Keelung.Yang@flex.com


Supported devices
-----------------
Tested on USBCANFD-200U (https://www.zlg.cn/can/can/product/id/223.html)

For other ZLG CAN devices, you can change ``bus.DeviceType`` 
to another value defined ``vci.ZCAN_DEVICE``


How to add new ZLG device
-------------------------
1. Add a new device type in ``vci.ZCAN_DEVICE``
2. Update ``ZlgBitTiming.speeds`` by device type in ``timming`` module
3. Update version infomation in ``zlg/__init__.py``


CAN filters
-----------
ZLG CAN Linux driver only supports filtering by ranges of CAN ID currently.
But the MCU(NXP LPC54616, in USBCANFD-200U) supports filtering by ranges and masks.
But they dropped mask filters and no plan to enable this feature again.
So hardware filtering is not supported in this interface currently.

Also, it is possible to convert limited masks into ranges asked by official driver.
But the count of filters is limited to 64 in official driver.
Although 128 standard ID filters and 64 extended ID filters supported in MCU.


Note
----
1. Before using this interface

   a. Install ``libusb`` package in your Linux distribution
   b. Download ``libusbcanfd.so`` from Linux driver package

   For more infomation, please check:
      https://manual.zlg.cn/web/#/188/6978

2. There are three official libraries which are incompatible with each other:
   
   a. VCI_*Functions & ZCAN_*Structures for Linux (CAN & CANFD)
   b. VCI_*Functions & VCI_*Structures for Windows (CAN only)
   c. ZCAN_*Functions & ZCAN_*Structures for Windows (CAN and CANFD)

   For more infomation, please check:
      USBCANFD for Linux, https://manual.zlg.cn/web/#/188/6982

      USBCANFD for Windows, https://www.zlg.cn/data/upload/software/Can/CAN_lib.rar

      USBCANFD resource, https://www.zlg.cn/can/down/down/id/223.html
      
3. The Device Type IDs are different between Linux and Windows
   
   Linux: https://manual.zlg.cn/web/#/188/6984

   Windows: https://manual.zlg.cn/web/#/152/6361

4. You can't detect ``BUS_OFF`` by Linux APIs currently, since there is 
   no such state in ``ZCAN_MSG_INF`` structure and the firmware will 
   restart automatically when ``BUS_OFF`` happened.

5. There is also an official python-can interface implementation for Windows only.
   
   But declared no sustaining anymore: https://manual.zlg.cn/web/#/169/6070
