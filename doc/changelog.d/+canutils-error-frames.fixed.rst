Fixed ``CanutilsLogReader`` reading candump error frames of any class other than bus error
as data frames. Error frames now keep their error class in ``arbitration_id``, their data
bytes, channel and direction, and ``CanutilsLogWriter`` writes that error class instead of
always writing the bus error class.
