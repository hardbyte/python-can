Scripts
=======

The following modules are callable from python-can.

They can be called for example by ``python -m can.logger`` or ``can_logger.py`` (if installed using pip).


can.logger
----------

Command line help, called with ``--help``::

    usage: python -m can.logger [-h] [-f LOG_FILE] [-v] [-c CHANNEL]
                                [-i {pcan,ixxat,socketcan_ctypes,kvaser,virtual,usb2can,vector,slcan,nican,socketcan,iscan,neovi,serial,socketcan_native}]
                                [--filter ...] [-b BITRATE]
                                [--active | --passive]

    Log CAN traffic, printing messages to stdout or to a given file.

    optional arguments:
      -h, --help            show this help message and exit
      -f LOG_FILE, --file_name LOG_FILE
                            Path and base log filename, for supported types see
                            can.Logger.
      -v                    How much information do you want to see at the command
                            line? You can add several of these e.g., -vv is DEBUG
      -c CHANNEL, --channel CHANNEL
                            Most backend interfaces require some sort of channel.
                            For example with the serial interface the channel
                            might be a rfcomm device: "/dev/rfcomm0" With the
                            socketcan interfaces valid channel examples include:
                            "can0", "vcan0"
      -i {pcan,ixxat,socketcan_ctypes,kvaser,virtual,usb2can,vector,slcan,nican,socketcan,iscan,neovi,serial,socketcan_native}, --interface {pcan,ixxat,socketcan_ctypes,kvaser,virtual,usb2can,vector,slcan,nican,socketcan,iscan,neovi,serial,socketcan_native}
                            Specify the backend CAN interface to use. If left
                            blank, fall back to reading from configuration files.
      --filter ...          Comma separated filters can be specified for the given
                            CAN interface: <can_id>:<can_mask> (matches when
                            <received_can_id> & mask == can_id & mask)
                            <can_id>~<can_mask> (matches when <received_can_id> &
                            mask != can_id & mask)
      -b BITRATE, --bitrate BITRATE
                            Bitrate to use for the CAN bus.
      --active              Start the bus as active, this is applied the default.
      --passive             Start the bus as passive.


can.player
----------

Command line help, called with ``--help``::

    usage: python -m can.player [-h] [-f LOG_FILE] [-v] [-c CHANNEL]
                                [-i {pcan,ixxat,socketcan_ctypes,kvaser,virtual,usb2can,vector,slcan,nican,socketcan,iscan,neovi,serial,socketcan_native}]
                                [-b BITRATE] [--ignore-timestamps]
                                [-g GAP] [-s SKIP]
                                input-file

    Replay CAN traffic.

    positional arguments:
      input-file            The file to replay. For supported types see
                            can.LogReader.

    optional arguments:
      -h, --help            show this help message and exit
      -f LOG_FILE, --file_name LOG_FILE
                            Path and base log filename, for supported types see
                            can.LogReader.
      -v                    Also print can frames to stdout. You can add several
                            of these to enable debugging
      -c CHANNEL, --channel CHANNEL
                            Most backend interfaces require some sort of channel.
                            For example with the serial interface the channel
                            might be a rfcomm device: "/dev/rfcomm0" With the
                            socketcan interfaces valid channel examples include:
                            "can0", "vcan0"
      -i {pcan,ixxat,socketcan_ctypes,kvaser,virtual,usb2can,vector,slcan,nican,socketcan,iscan,neovi,serial,socketcan_native}, --interface {pcan,ixxat,socketcan_ctypes,kvaser,virtual,usb2can,vector,slcan,nican,socketcan,iscan,neovi,serial,socketcan_native}
                            Specify the backend CAN interface to use. If left
                            blank, fall back to reading from configuration files.
      -b BITRATE, --bitrate BITRATE
                            Bitrate to use for the CAN bus.
      --ignore-timestamps   Ignore timestamps (send all frames immediately with
                            minimum gap between frames)
      -g GAP, --gap GAP     <s> minimum time between replayed frames
      -s SKIP, --skip SKIP  <s> skip gaps greater than 's' seconds
