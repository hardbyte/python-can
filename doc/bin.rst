Scripts
=======

The following scripts are installed along with python-can.

canlogger
---------

Command line help (``canlogger --help`` or ``python -m can.io.logger --help``)::

    usage: canlogger [-h] [-f LOG_FILE] [-v] [-c CHANNEL]
                    [-i {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}]
                    [--filter ...]

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
      -i {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}, --interface {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}
                            Specify the backend CAN interface to use. If left
                            blank, fall back to reading from configuration files.
      --filter ...          Comma separated filters can be specified for the given
                            CAN interface: <can_id>:<can_mask> (matches when
                            <received_can_id> & mask == can_id & mask)
                            <can_id>~<can_mask> (matches when <received_can_id> &
                            mask != can_id & mask)


canplayer
---------

Command line help (``canplayer --help`` or ``python -m can.io.player --help``)::

    usage: canplayer [-h] [-f LOG_FILE] [-v] [-c CHANNEL]
                    [-i {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}]
                    [--ignore-timestamps] [-g GAP] [-s SKIP]
                    input-file

    Replay CAN traffic

    positional arguments:
      input-file            The file to replay. Supported types: .db

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
      -i {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}, --interface {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}
                            Specify the backend CAN interface to use. If left
                            blank, fall back to reading from configuration files.
      --ignore-timestamps   Ignore timestamps (send all frames immediately with
                            minimum gap between frames)
      -g GAP, --gap GAP     <ms> minimum time between replayed frames
      -s SKIP, --skip SKIP  <s> skip gaps greater than 's' seconds



canserver
---------

Command line help (``canserver --help`` or ``python -m can.interfaces.remote --help``)::

      usage: canserver [-h] [-v] [-c CHANNEL]
                      [-i {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}]
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
        -i {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}, --interface {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}
                              Specify the backend CAN interface to use. If left
                              blank, fall back to reading from configuration files.
        -b BITRATE, --bitrate BITRATE
                              Force to use a specific bitrate. This will override
                              any requested bitrate by the clients.
        -H HOST, --host HOST  Host to listen to (default 0.0.0.0).
        -p PORT, --port PORT  TCP port to listen on (default 54701).

