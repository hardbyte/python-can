CANalyst-II
===========

CANalyst-II(+) is a USB to CAN Analyzer. The controlcan library is originally developed by
`ZLG ZHIYUAN Electronics`_.

If running on Windows you will need to place the ControlCAN.dll
file into the current working directory that is being used before you import the library.
For Posix systems the file name is libcontrolcan.so.

This file should be included in the software package that the manufacturer
of your interface has provided.

The file may not have one of the names above, it may have a different name.
If this is the case then you will need to rename the file to one of the file
names above.

You MUST use the file that is for your interface. If you have a clone of a CANalyst-II the
dll or so file for a genuine CANalyst-II will not work.

Here are some links to cloned devices drivers/software where you will be able to locate
the ControlCAN.dll or libcontrolcan.so file

clone that looks identical to the CANalyst-II
`CHUANGXIN Technology Linux Drivers`_.
`CHUANGXIN Technology Windows Drivers`_.

clone that does not look like the CANalyst-II
`Viewtool Ginkgo`_.

Bus
---

.. autoclass:: can.interfaces.canalystii.CANalystIIBus


.. _ZLG ZHIYUAN Electronics: http://www.zlg.com/can/can/product/id/42.html
.. _CHUANGXIN Technology Linux Drivers: http://24869997.s21d-24.faiusrd.com/0/ABUIABAAGAAgpqj__AUomOuchAM?f=CAN%E5%88%86%E6%9E%90%E4%BB%AA%E8%B5%84%E6%96%9920200702_Linux.7z&v=1595905068
.. _CHUANGXIN Technology Windows Drivers: http://24869997.s21d-24.faiusrd.com/0/ABUIABAAGAAgraT__AUoiq_FnwU?f=CAN%E5%88%86%E6%9E%90%E4%BB%AA%E8%B5%84%E6%96%9920200702.7z&v=1595904562
.. _Viewtool Ginkgo: http://viewtool.com/index.php/en/20-2016-07-29-02-10-12/16-ginkgo-series-drivers