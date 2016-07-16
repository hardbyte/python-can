USB2CAN Interface
=================

OVERVIEW
--------

The USB2CAN is a cheep CAN interface based on an ARM7 chip (STR750FV2).  Currently there is support for this device on both Linux and Windows though slightly different methods.

LINUX SUPPORT
-------------

Linux support is achieved through a socketcan type interface.  Drivers for this device were added to Kernel version 3.9 but then back-ported.  As of writing this it has been verified working on Ubuntu 14.04.
Once the device is plugged in the OS will automatically load the drivers and at that point it is just a matter of configuring the interface with the speed and any other options that you might want.

LINUX SETUP
-----------

    1. The driver should autoload when the device is plugged in, if not use modprobe to load the driver.
    2. Use the ip link command to configure it or use the socketcan interface in python-can to set it up.
        (ex. using the command line option)
        "sudo ip link set can0 up type can bitrate 500000 restart-ms 10000" sets bitrate to 500kbp/s on device can0
        

WINDOWS SUPPORT
---------------

Support though windows is achieved through a DLL very similar to the way the PCAN functions.  The API is called CANAL (CAN Abstraction Layer) which is a separate project designed to be used with 
VSCP which is a socket like messaging system that is not only cross platform but also supports other types of devices.  This device can be used through one of three ways
1)Through python-can
2)CANAL API either using the DLL and C/C++ or through the python wrapper that has been added to this project
3)VSCP
Using python-can is strongly suggested as with little extra work the same interface can be used on both Windows and Linux.

WINDOWS INSTALL
---------------

    1. To install on Windows download the USB2CAN Windows driver.  It is compatible with XP, Vista, Win7, Win8/8.1. (Written against driver version v1.0.2.1)
    2. Download the USB2CAN CANAL DLL from the USB2CAN website.  Place this in either the same directory you are running usb2can.py from or your DLL folder in your python install.
        (Written against CANAL DLL version v1.0.6)

WHAT WAS ADDED TO PYTHON-CAN TO MAKE THIS WORK
----------------------------------------------

There were three files added to make this work as well as the proper entries to make the library recognize the interface as a valid one
    1. usb2can.py
        This file is only a wrapper for the CANAL API that the interface expects.  There are also a couple of constants here to try and make dealing with the
        bitwise operations for flag setting a little easier.  Other than that this is only the CANAL API.  If a programmer wanted to work with the API directly this is 
        the file that allows you to do this.  The CANAL project does not provide this wrapper and normally must be accessed with C.
        
    2. usb2canInterface.py
        This file provides the translation to and from the python-can library to the CANAL API.  This is where all the logic is and setup code is.  Most issues if they are found
        will be either found here or within the DLL that is provided
        
    3. usb2canWin.py
        See the section below for the reason for adding this as it is a little odd.  What program does is if a serial number is not provided to the usb2canInterface file this
        program does WMI (Windows Management Instrumentation) calls to try and figure out what device to connect to.  It then returns the serial number of the device.
        Currently it is not really smart enough to figure out what to do if there are multiple devices.  This needs to be changed if people are using more than one interface.

    
    
Interface Specific Items
------------------------

    There are a few things that are kinda strange about this device and are not overly obvious about the code or things that are not done being implemented in the DLL.
    
1. You need the Serial Number to connect to the device under Windows.  This is part of the "setup string" that configures the device.  There are a few options for how to get this.
    1. Use usb2canWin.py to find the serial number
    2. Look on the device and enter it either through a prompt/barcode scanner/hardcode it.(Not recommended)
    3. Reprogram the device serial number to something and do that for all the devices you own.                         (Really Not Recommended,   can no longer use multiple devices on one computer)
    
2. In usb2can.py there is a structure called CANALMSG which has a unsigned byte array of size 8.  In the usb2canInterface file it passes in an unsigned byte array of size 8 also which if you pass less than 8 bytes in it stuffs it with extra zeros.  So if the data "01020304" is sent the message would look like "0102030400000000".  There is also a part of this structure called sizeData which is the actual length of the data that was sent not the stuffed message (in this case would be 4).  What then happens is although a message of size 8 is sent to the device only the length of information so the first 4 bytes of information would be sent.  This is done because the DLL expects a length of 8 and nothing else.  So to make it compatible that has to be sent through the wrapper.  If usb2canInterface sent an array of length 4 with sizeData of 4 as well the array would throw an incompatible data type error.  There is a Wireshark file posted in Issue #36 that demonstrates that the bus is only sending the data and not the extra zeros.
        
3. The masking features have not been implemented currently in the CANAL interface in the version currently on the USB2CAN website.  This may not be the case on the actual project so make sure to check there if they have been implemented if you need those features.
