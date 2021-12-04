.. _cfuc:

CAN over Serial for uCAN CAN FD USB CONVERTER (CFUC) device
===============
More info on device can be found on https://ucandevices.github.io/cfuc.html 
Device works on LINUX and WINDOWS uses serial interface that uses virtual port COM like
``/dev/ttyS1`` or ``/dev/ttyUSB0`` on Linux machines or ``COM1`` on Windows. 
All tranfered data via USB is more less like strucured like stm32 CAN FD perfierial so detail explenation 
of all parameters can be found in STM32G431CBUx, a lot of custom setup of stm32 CAN FD periferial 
registers can be done directly from python. 

What is supported 
---
    Classical CAN
    CAN-FD with BRS Baudrate up to 8Mbs

What is not-supported yet 
---
    Hardware filtering
    Hardware timestamp

Example Usage
---
import can
    bus = can.Bus(bustype="cfuc", channel="COM1", CANBaudRate=250000, IsFD=True, FDDataBaudRate=500000)

