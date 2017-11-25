Scripts
=======

The following modules are callable from python-can.

can.logger
----------

Command line help (``python -m can.logger --help``)::

    usage: python -m can.logger [-h] [-f LOG_FILE] [-v] [-c CHANNEL]
                                [-i {iscan,slcan,virtual,socketcan_ctypes,usb2can,ixxat,socketcan_native,kvaser,neovi,vector,nican,pcan,serial,remote,socketcan}]
                                [--filter ...] [-b BITRATE]

    Log CAN traffic, printing messages to stdout or to a given file

    optional arguments:
      -h, --help            show this help message and exit
      -f LOG_FILE, --file_name LOG_FILE
                            Path and base log filename, extension can be .txt,
                            .asc, .csv, .db, .npz
      -v                    How much information do you want to see at the command
                            line? You can add several of these e.g., -vv is DEBUG
      -c CHANNEL, --channel CHANNEL
                            Most backend interfaces require some sort of channel.
                            For example with the serial interface the channel
                            might be a rfcomm device: "/dev/rfcomm0" With the
                            socketcan interfaces valid channel examples include:
                            "can0", "vcan0"
      -i {iscan,slcan,virtual,socketcan_ctypes,usb2can,ixxat,socketcan_native,kvaser,neovi,vector,nican,pcan,serial,remote,socketcan}, --interface {iscan,slcan,virtual,socketcan_ctypes,usb2can,ixxat,socketcan_native,kvaser,neovi,vector,nican,pcan,serial,remote,socketcan}
                            Specify the backend CAN interface to use. If left
                            blank, fall back to reading from configuration files.
      --filter ...          Comma separated filters can be specified for the given
                            CAN interface: <can_id>:<can_mask> (matches when
                            <received_can_id> & mask == can_id & mask)
                            <can_id>~<can_mask> (matches when <received_can_id> &
                            mask != can_id & mask)
      -b BITRATE, --bitrate BITRATE
                            Bitrate to use for the CAN bus.


can.player
----------

Command line help (``python -m can.player --help``)::

    usage: python -m can.player [-h] [-f LOG_FILE] [-v] [-c CHANNEL]
                                [-i {kvaser,virtual,slcan,nican,neovi,ixxat,serial,usb2can,socketcan_ctypes,remote,socketcan_native,iscan,vector,pcan,socketcan}]
                                [-b BITRATE] [--ignore-timestamps] [-g GAP]
                                [-s SKIP]
                                input-file

    Replay CAN traffic

    positional arguments:
      input-file            The file to replay. Supported types: .db, .blf

    optional arguments:
      -h, --help            show this help message and exit
      -f LOG_FILE, --file_name LOG_FILE
                            Path and base log filename, extension can be .txt,
                            .asc, .csv, .db, .npz
      -v                    Also print can frames to stdout. You can add several
                            of these to enable debugging
      -c CHANNEL, --channel CHANNEL
                            Most backend interfaces require some sort of channel.
                            For example with the serial interface the channel
                            might be a rfcomm device: "/dev/rfcomm0" With the
                            socketcan interfaces valid channel examples include:
                            "can0", "vcan0"
      -i {kvaser,virtual,slcan,nican,neovi,ixxat,serial,usb2can,socketcan_ctypes,remote,socketcan_native,iscan,vector,pcan,socketcan}, --interface {kvaser,virtual,slcan,nican,neovi,ixxat,serial,usb2can,socketcan_ctypes,remote,socketcan_native,iscan,vector,pcan,socketcan}
                            Specify the backend CAN interface to use. If left
                            blank, fall back to reading from configuration files.
      -b BITRATE, --bitrate BITRATE
                            Bitrate to use for the CAN bus.
      --ignore-timestamps   Ignore timestamps (send all frames immediately with
                            minimum gap between frames)
      -g GAP, --gap GAP     <s> minimum time between replayed frames
      -s SKIP, --skip SKIP  <s> skip gaps greater than 's' seconds



can.server
----------

Command line help (``python -m can.server --help``)::

    usage: python -m can.server [-h] [-v] [-c CHANNEL]
                                [-i {kvaser,nican,vector,iscan,virtual,socketcan,socketcan_ctypes,usb2can,socketcan_native,neovi,serial,pcan,ixxat,remote,slcan}]
                                [-b BITRATE] [-H HOST] [-p PORT]

    Remote CAN server

    optional arguments:
      -h, --help            show this help message and exit
      -v                    How much information do you want to see at the command
                            line? You can add several of these e.g., -vv is DEBUG
      -c CHANNEL, --channel CHANNEL
                            Most backend interfaces require some sort of channel.
                            For example with the serial interface the channel
                            might be a rfcomm device: "/dev/rfcomm0" With the
                            socketcan interfaces valid channel examples include:
                            "can0", "vcan0". The server will only serve this
                            channel. Start additional servers at different ports
                            to share more channels.
      -i {kvaser,nican,vector,iscan,virtual,socketcan,socketcan_ctypes,usb2can,socketcan_native,neovi,serial,pcan,ixxat,remote,slcan}, --interface {kvaser,nican,vector,iscan,virtual,socketcan,socketcan_ctypes,usb2can,socketcan_native,neovi,serial,pcan,ixxat,remote,slcan}
                            Specify the backend CAN interface to use. If left
                            blank, fall back to reading from configuration files.
      -b BITRATE, --bitrate BITRATE
                            Force to use a specific bitrate. This will override
                            any requested bitrate by the clients.
      -H HOST, --host HOST  Host to listen to (default 0.0.0.0).
      -p PORT, --port PORT  TCP port to listen on (default 54701).
