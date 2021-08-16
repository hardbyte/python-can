# Status return values.
ECI_NO_ERROR = 0x00
CAN_NO_RX_MESSAGES = 0x88
CAN_NO_ERROR_MESSAGES = 0x89
ECI_NO_MORE_DEVICES = 0x80  # From FindNextDevice

# Allowed values for BaudRate in CANOpen function.
CAN_BAUD_250K = 0
CAN_BAUD_500K = 1
CAN_BAUD_1MB = 2
CAN_BAUD_125K = 3

# Allowed values for the BaudRate in SerialOpen function.
# NOTE: This is here for completeness but serial is not implemented.
# SERIAL_BAUD_2400 = 0
# SERIAL_BAUD_4800 = 1
# SERIAL_BAUD_9600 = 2
# SERIAL_BAUD_19200 = 3
# SERIAL_BAUD_28800 = 4
# SERIAL_BAUD_38400 = 5
# SERIAL_BAUD_57600 = 6

# Allowed values for the SetupCommand in CANSetupDevice function.
CAN_CMD_TRANSMIT = 0
# Allowed values for the SetupProperty in CANSetupDevice function.
CAN_PROPERTY_ASYNC = 0
CAN_PROPERTY_SYNC = 1

# Allowed flags for GetQueueSize function with CAN handle.
CAN_GET_EFF_SIZE = 0
CAN_GET_MAX_EFF_SIZE = 1
CAN_GET_SFF_SIZE = 2
CAN_GET_MAX_SFF_SIZE = 3
CAN_GET_ERROR_SIZE = 4
CAN_GET_MAX_ERROR_SIZE = 5
CAN_GET_TX_SIZE = 6
CAN_GET_MAX_TX_SIZE = 7

# Allowed flags for GetQueueSize function with serial handle.
# NOTE: This is here for completeness but serial is not implemented.
# SER_GET_RX_SIZE = 8
# SER_GET_MAX_RX_SIZE = 9
# SER_GET_TX_SIZE = 10
# SER_GET_MAX_TX_SIZE = 11

# Allowed flags for StartDeviceSearch function.
FIND_OPEN = 0x82
FIND_UNOPEN = 0x83
FIND_ALL = 0x87
FIND_NEXT = 0x00

# ErrorMessage Control Bytes - these correspond to CAN error frames (and
# similar errors) that occurred on the bus.
CAN_ERR_BUS = (
    0x11  # A CAN Bus error has occurred (DataByte contains ErrorCaptureCode Register)
)
CAN_ERR_BUS_OFF_EVENT = 0x12  # Bus off due to error
CAN_ERR_RESET_AFTER_BUS_OFF = 0x13  # Error reseting SJA1000 after bus off event
CAN_ERR_RX_LIMIT_REACHED = 0x16  # The default rx error limit (96) has been reached
CAN_ERR_TX_LIMIT_REACHED = 0x17  # The default tx error limit (96) has been reached
CAN_BUS_BACK_ON_EVENT = 0x18  # Bus has come back on after a bus off event due to errors
CAN_ARBITRATION_LOST = (
    0x19  # Arbitration lost (DataByte contains location lost) see SJA1000 datasheet
)
CAN_ERR_PASSIVE = 0x1A  # SJA1000 has entered error passive mode
CAN_ERR_OVERRUN = 0x1B  # Embedded firmware has received a receive overrun
CAN_ERR_OVERRUN_PC = 0x1C  # PC driver received a receive overrun
ERR_ERROR_FIFO_OVERRUN = 0x20  # Error buffer full - new errors will be lost
ERR_EFF_RX_FIFO_OVERRUN = 0x21  # EFF Receive buffer full - messages will be lost
ERR_SFF_RX_FIFO_OVERRUN = 0x22  # SFF Receive buffer full - messages will be lost

# Other Constants
# Constants from API but that aren't used in functions.
TIMESTAMP_RESL = 64e-6  # 64 us
