Scripts
=======

The following scripts are installed along with python-can.

can_logger.py
-------------

Command line help (``--help``)::

    usage: can_logger.py [-h] [-f LOG_FILE] [-v] [-i {socketcan,kvaser,serial,ixxat}]
                         channel ...

    Log CAN traffic, printing messages to stdout or to a given file

    positional arguments:
      channel               Most backend interfaces require some sort of channel.
                            For example with the serial interface the channel
                            might be a rfcomm device: /dev/rfcomm0 Other channel
                            examples are: can0, vcan0
      filter                Comma separated filters can be specified for the given
                            CAN interface: <can_id>:<can_mask> (matches when
                            <received_can_id> & mask == can_id & mask)
                            <can_id>~<can_mask> (matches when <received_can_id> &
                            mask != can_id & mask)

    optional arguments:
      -h, --help            show this help message and exit
      -f LOG_FILE, --file_name LOG_FILE
                            Path and base log filename, extension can be .txt,
                            .csv, .db, .npz
      -v                    How much information do you want to see at the command
                            line? You can add several of these e.g., -vv is DEBUG
      -i {socketcan,kvaser,serial,ixxat}, --interface {socketcan,kvaser,serial,ixxat}
                            Which backend do you want to use?


can_server.py
-------------

Command line help (``--help``)::

      usage: can_server.py [-h] [-v] [-c CHANNEL]
                          [-i {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}]
                          [-p PORT]

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
                              "can0", "vcan0"
        -i {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}, --interface {pcan,remote,ixxat,socketcan_ctypes,virtual,usb2can,nican,serial,kvaser,socketcan,socketcan_native}
                              Specify the backend CAN interface to use. If left
                              blank, fall back to reading from configuration files.
        -p PORT, --port PORT  TCP port to listen on (default 54701).

