Fixed ``ASCReader`` support for CANoe 7.x CAN FD records that place the CAN
identifier before the ``Rx``/``Tx`` direction. CANoe decimal DLC codes are now
resolved against the record's authoritative data-length field.
