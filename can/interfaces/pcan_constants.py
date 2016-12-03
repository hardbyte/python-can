from ctypes import *

# ///////////////////////////////////////////////////////////
# Type definitions
# ///////////////////////////////////////////////////////////

TPCANHandle            = c_ubyte  # Represents a PCAN hardware channel handle
TPCANStatus            = int      # Represents a PCAN status/error code
TPCANParameter         = c_ubyte  # Represents a PCAN parameter to be read or set
TPCANDevice            = c_ubyte  # Represents a PCAN device
TPCANMessageType       = c_ubyte  # Represents the type of a PCAN message
TPCANType              = c_ubyte  # Represents the type of PCAN hardware to be initialized
TPCANMode              = c_ubyte  # Represents a PCAN filter mode
TPCANBaudrate          = c_ushort  # Represents a PCAN Baud rate register value

# ///////////////////////////////////////////////////////////
# Value definitions
# ///////////////////////////////////////////////////////////

# Currently defined and supported PCAN channels
#
PCAN_NONEBUS             = TPCANHandle(0x00)  # Undefined/default value for a PCAN bus

PCAN_ISABUS1             = TPCANHandle(0x21)  # PCAN-ISA interface, channel 1
PCAN_ISABUS2             = TPCANHandle(0x22)  # PCAN-ISA interface, channel 2
PCAN_ISABUS3             = TPCANHandle(0x23)  # PCAN-ISA interface, channel 3
PCAN_ISABUS4             = TPCANHandle(0x24)  # PCAN-ISA interface, channel 4
PCAN_ISABUS5             = TPCANHandle(0x25)  # PCAN-ISA interface, channel 5
PCAN_ISABUS6             = TPCANHandle(0x26)  # PCAN-ISA interface, channel 6
PCAN_ISABUS7             = TPCANHandle(0x27)  # PCAN-ISA interface, channel 7
PCAN_ISABUS8             = TPCANHandle(0x28)  # PCAN-ISA interface, channel 8

PCAN_DNGBUS1             = TPCANHandle(0x31)  # PCAN-Dongle/LPT interface, channel 1

PCAN_PCIBUS1             = TPCANHandle(0x41)  # PCAN-PCI interface, channel 1
PCAN_PCIBUS2             = TPCANHandle(0x42)  # PCAN-PCI interface, channel 2
PCAN_PCIBUS3             = TPCANHandle(0x43)  # PCAN-PCI interface, channel 3
PCAN_PCIBUS4             = TPCANHandle(0x44)  # PCAN-PCI interface, channel 4
PCAN_PCIBUS5             = TPCANHandle(0x45)  # PCAN-PCI interface, channel 5
PCAN_PCIBUS6             = TPCANHandle(0x46)  # PCAN-PCI interface, channel 6
PCAN_PCIBUS7             = TPCANHandle(0x47)  # PCAN-PCI interface, channel 7
PCAN_PCIBUS8             = TPCANHandle(0x48)  # PCAN-PCI interface, channel 8

PCAN_USBBUS1             = TPCANHandle(0x51)  # PCAN-USB interface, channel 1
PCAN_USBBUS2             = TPCANHandle(0x52)  # PCAN-USB interface, channel 2
PCAN_USBBUS3             = TPCANHandle(0x53)  # PCAN-USB interface, channel 3
PCAN_USBBUS4             = TPCANHandle(0x54)  # PCAN-USB interface, channel 4
PCAN_USBBUS5             = TPCANHandle(0x55)  # PCAN-USB interface, channel 5
PCAN_USBBUS6             = TPCANHandle(0x56)  # PCAN-USB interface, channel 6
PCAN_USBBUS7             = TPCANHandle(0x57)  # PCAN-USB interface, channel 7
PCAN_USBBUS8             = TPCANHandle(0x58)  # PCAN-USB interface, channel 8

PCAN_PCCBUS1             = TPCANHandle(0x61)  # PCAN-PC Card interface, channel 1
PCAN_PCCBUS2             = TPCANHandle(0x62)  # PCAN-PC Card interface, channel 2

# Represent the PCAN error and status codes
#
PCAN_ERROR_OK            = TPCANStatus(0x00000)  # No error
PCAN_ERROR_XMTFULL       = TPCANStatus(0x00001)  # Transmit buffer in CAN controller is full
PCAN_ERROR_OVERRUN       = TPCANStatus(0x00002)  # CAN controller was read too late
PCAN_ERROR_BUSLIGHT      = TPCANStatus(0x00004)  # Bus error: an error counter reached the 'light' limit
PCAN_ERROR_BUSHEAVY      = TPCANStatus(0x00008)  # Bus error: an error counter reached the 'heavy' limit
PCAN_ERROR_BUSOFF        = TPCANStatus(0x00010)  # Bus error: the CAN controller is in bus-off state
PCAN_ERROR_ANYBUSERR     = TPCANStatus(PCAN_ERROR_BUSLIGHT | PCAN_ERROR_BUSHEAVY | PCAN_ERROR_BUSOFF)  # Mask for all bus errors
PCAN_ERROR_QRCVEMPTY     = TPCANStatus(0x00020)  # Receive queue is empty
PCAN_ERROR_QOVERRUN      = TPCANStatus(0x00040)  # Receive queue was read too late
PCAN_ERROR_QXMTFULL      = TPCANStatus(0x00080)  # Transmit queue is full
PCAN_ERROR_REGTEST       = TPCANStatus(0x00100)  # Test of the CAN controller hardware registers failed (no hardware found)
PCAN_ERROR_NODRIVER      = TPCANStatus(0x00200)  # Driver not loaded
PCAN_ERROR_HWINUSE       = TPCANStatus(0x00400)  # Hardware already in use by a Net
PCAN_ERROR_NETINUSE      = TPCANStatus(0x00800)  # A Client is already connected to the Net
PCAN_ERROR_ILLHW         = TPCANStatus(0x01400)  # Hardware handle is invalid
PCAN_ERROR_ILLNET        = TPCANStatus(0x01800)  # Net handle is invalid
PCAN_ERROR_ILLCLIENT     = TPCANStatus(0x01C00)  # Client handle is invalid
PCAN_ERROR_ILLHANDLE     = TPCANStatus(PCAN_ERROR_ILLHW | PCAN_ERROR_ILLNET | PCAN_ERROR_ILLCLIENT)  # Mask for all handle errors
PCAN_ERROR_RESOURCE      = TPCANStatus(0x02000)  # Resource (FIFO, Client, timeout) cannot be created
PCAN_ERROR_ILLPARAMTYPE  = TPCANStatus(0x04000)  # Invalid parameter
PCAN_ERROR_ILLPARAMVAL   = TPCANStatus(0x08000)  # Invalid parameter value
PCAN_ERROR_UNKNOWN       = TPCANStatus(0x10000)  # Unknow error
PCAN_ERROR_ILLDATA       = TPCANStatus(0x20000)  # Invalid data, function, or action
PCAN_ERROR_INITIALIZE    = TPCANStatus(0x40000)  # Channel is not initialized
PCAN_ERROR_ILLOPERATION  = TPCANStatus(0x80000)  # Invalid operation

# PCAN devices
#
PCAN_NONE                = TPCANDevice(0x00)  # Undefined, unknown or not selected PCAN device value
PCAN_PEAKCAN             = TPCANDevice(0x01)  # PCAN Non-Plug&Play devices. NOT USED WITHIN PCAN-Basic API
PCAN_ISA                 = TPCANDevice(0x02)  # PCAN-ISA, PCAN-PC/104, and PCAN-PC/104-Plus
PCAN_DNG                 = TPCANDevice(0x03)  # PCAN-Dongle
PCAN_PCI                 = TPCANDevice(0x04)  # PCAN-PCI, PCAN-cPCI, PCAN-miniPCI, and PCAN-PCI Express
PCAN_USB                 = TPCANDevice(0x05)  # PCAN-USB and PCAN-USB Pro
PCAN_PCC                 = TPCANDevice(0x06)  # PCAN-PC Card

# PCAN parameters
#
PCAN_DEVICE_NUMBER       = TPCANParameter(0x01)  # PCAN-USB device number parameter
PCAN_5VOLTS_POWER        = TPCANParameter(0x02)  # PCAN-PC Card 5-Volt power parameter
PCAN_RECEIVE_EVENT       = TPCANParameter(0x03)  # PCAN receive event handler parameter
PCAN_MESSAGE_FILTER      = TPCANParameter(0x04)  # PCAN message filter parameter
PCAN_API_VERSION         = TPCANParameter(0x05)  # PCAN-Basic API version parameter
PCAN_CHANNEL_VERSION     = TPCANParameter(0x06)  # PCAN device channel version parameter
PCAN_BUSOFF_AUTORESET    = TPCANParameter(0x07)  # PCAN Reset-On-Busoff parameter
PCAN_LISTEN_ONLY         = TPCANParameter(0x08)  # PCAN Listen-Only parameter
PCAN_LOG_LOCATION        = TPCANParameter(0x09)  # Directory path for log files
PCAN_LOG_STATUS          = TPCANParameter(0x0A)  # Debug-Log activation status
PCAN_LOG_CONFIGURE       = TPCANParameter(0x0B)  # Configuration of the debugged information (LOG_FUNCTION_***)
PCAN_LOG_TEXT            = TPCANParameter(0x0C)  # Custom insertion of text into the log file
PCAN_CHANNEL_CONDITION   = TPCANParameter(0x0D)  # Availability status of a PCAN-Channel
PCAN_HARDWARE_NAME       = TPCANParameter(0x0E)  # PCAN hardware name parameter
PCAN_RECEIVE_STATUS      = TPCANParameter(0x0F)  # Message reception status of a PCAN-Channel
PCAN_CONTROLLER_NUMBER   = TPCANParameter(0x10)  # CAN-Controller number of a PCAN-Channel
PCAN_TRACE_LOCATION      = TPCANParameter(0x11)  # Directory path for PCAN trace files
PCAN_TRACE_STATUS        = TPCANParameter(0x12)  # CAN tracing activation status
PCAN_TRACE_SIZE          = TPCANParameter(0x13)  # Configuration of the maximum file size of a CAN trace
PCAN_TRACE_CONFIGURE     = TPCANParameter(0x14)  # Configuration of the trace file storing mode (TRACE_FILE_***)
PCAN_CHANNEL_IDENTIFYING = TPCANParameter(0x15)  # Phisical identification of a USB based PCAN-Channel by blinking its associated LED

# PCAN parameter values
#
PCAN_PARAMETER_OFF       = int(0x00)  # The PCAN parameter is not set (inactive)
PCAN_PARAMETER_ON        = int(0x01)  # The PCAN parameter is set (active)
PCAN_FILTER_CLOSE        = int(0x00)  # The PCAN filter is closed. No messages will be received
PCAN_FILTER_OPEN         = int(0x01)  # The PCAN filter is fully opened. All messages will be received
PCAN_FILTER_CUSTOM       = int(0x02)  # The PCAN filter is custom configured. Only registered messages will be received
PCAN_CHANNEL_UNAVAILABLE = int(0x00)  # The PCAN-Channel handle is illegal, or its associated hadware is not available
PCAN_CHANNEL_AVAILABLE   = int(0x01)  # The PCAN-Channel handle is available to be connected (Plug&Play Hardware: it means furthermore that the hardware is plugged-in)
PCAN_CHANNEL_OCCUPIED    = int(0x02)  # The PCAN-Channel handle is valid, and is already being used

LOG_FUNCTION_DEFAULT     = int(0x00)   # Logs system exceptions / errors
LOG_FUNCTION_ENTRY       = int(0x01)   # Logs the entries to the PCAN-Basic API functions
LOG_FUNCTION_PARAMETERS  = int(0x02)   # Logs the parameters passed to the PCAN-Basic API functions
LOG_FUNCTION_LEAVE       = int(0x04)   # Logs the exits from the PCAN-Basic API functions
LOG_FUNCTION_WRITE       = int(0x08)   # Logs the CAN messages passed to the CAN_Write function
LOG_FUNCTION_READ        = int(0x10)   # Logs the CAN messages received within the CAN_Read function
LOG_FUNCTION_ALL         = int(0xFFFF)  # Logs all possible information within the PCAN-Basic API functions

TRACE_FILE_SINGLE        = int(0x00)   # A single file is written until it size reaches PAN_TRACE_SIZE
TRACE_FILE_SEGMENTED     = int(0x01)   # Traced data is distributed in several files with size PAN_TRACE_SIZE
TRACE_FILE_DATE          = int(0x02)   # Includes the date into the name of the trace file
TRACE_FILE_TIME          = int(0x04)   # Includes the start time into the name of the trace file
TRACE_FILE_OVERWRITE     = int(0x80)   # Causes the overwriting of available traces (same name)

# PCAN message types
#
PCAN_MESSAGE_STANDARD    = TPCANMessageType(0x00)  # The PCAN message is a CAN Standard Frame (11-bit identifier)
PCAN_MESSAGE_RTR         = TPCANMessageType(0x01)  # The PCAN message is a CAN Remote-Transfer-Request Frame
PCAN_MESSAGE_EXTENDED    = TPCANMessageType(0x02)  # The PCAN message is a CAN Extended Frame (29-bit identifier)
PCAN_MESSAGE_STATUS      = TPCANMessageType(0x80)  # The PCAN message represents a PCAN status message

# Frame Type / Initialization Mode
#
PCAN_MODE_STANDARD       = PCAN_MESSAGE_STANDARD
PCAN_MODE_EXTENDED       = PCAN_MESSAGE_EXTENDED

# Baud rate codes = BTR0/BTR1 register values for the CAN controller.
# You can define your own Baud rate with the BTROBTR1 register.
# Take a look at www.peak-system.com for our free software "BAUDTOOL"
# to calculate the BTROBTR1 register for every baudrate and sample point.
#
PCAN_BAUD_1M             = TPCANBaudrate(0x0014)  # 1 MBit/s
PCAN_BAUD_800K           = TPCANBaudrate(0x0016)  # 800 kBit/s
PCAN_BAUD_500K           = TPCANBaudrate(0x001C)  # 500 kBit/s
PCAN_BAUD_250K           = TPCANBaudrate(0x011C)  # 250 kBit/s
PCAN_BAUD_125K           = TPCANBaudrate(0x031C)  # 125 kBit/s
PCAN_BAUD_100K           = TPCANBaudrate(0x432F)  # 100 kBit/s
PCAN_BAUD_95K            = TPCANBaudrate(0xC34E)  # 95,238 kBit/s
PCAN_BAUD_83K            = TPCANBaudrate(0x852B)  # 83,333 kBit/s
PCAN_BAUD_50K            = TPCANBaudrate(0x472F)  # 50 kBit/s
PCAN_BAUD_47K            = TPCANBaudrate(0x1414)  # 47,619 kBit/s
PCAN_BAUD_33K            = TPCANBaudrate(0x8B2F)  # 33,333 kBit/s
PCAN_BAUD_20K            = TPCANBaudrate(0x532F)  # 20 kBit/s
PCAN_BAUD_10K            = TPCANBaudrate(0x672F)  # 10 kBit/s
PCAN_BAUD_5K             = TPCANBaudrate(0x7F7F)  # 5 kBit/s

# Supported No-Plug-And-Play Hardware types
#
PCAN_TYPE_ISA            = TPCANType(0x01)  # PCAN-ISA 82C200
PCAN_TYPE_ISA_SJA        = TPCANType(0x09)  # PCAN-ISA SJA1000
PCAN_TYPE_ISA_PHYTEC     = TPCANType(0x04)  # PHYTEC ISA
PCAN_TYPE_DNG            = TPCANType(0x02)  # PCAN-Dongle 82C200
PCAN_TYPE_DNG_EPP        = TPCANType(0x03)  # PCAN-Dongle EPP 82C200
PCAN_TYPE_DNG_SJA        = TPCANType(0x05)  # PCAN-Dongle SJA1000
PCAN_TYPE_DNG_SJA_EPP    = TPCANType(0x06)  # PCAN-Dongle EPP SJA1000
