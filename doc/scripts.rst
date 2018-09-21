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

can.viewer
----------

A screenshot of the application can be seen below:

.. image:: ../images/viewer.png
    :width: 100%

The first column is the number of times a frame with the particular ID that has been received, next is the timestamp of the frame relative to the first received message. The third column is the time between the current frame relative to the previous one. Next is the length of the frame, the data and then the decoded data converted according to the ``-d`` argument. The top red row indicates an error frame.

Command line arguments
^^^^^^^^^^^^^^^^^^^^^^

By default it will be using the :doc:`/interfaces/socketcan` interface. All interfaces supported are supported and can be specified using the ``-i`` argument.

The full usage page can be seen below::

    Usage: python -m can.viewer [-h] [--version] [-b BITRATE] [-c CHANNEL]
                                [-d {<id>:<format>,<id>:<format>:<scaling1>:...:<scalingN>,file.txt}]
                                [-f {<can_id>:<can_mask>,<can_id>~<can_mask>}]
                                [-i {iscan,ixxat,kvaser,neovi,nican,pcan,serial,slcan,socketcan,socketcan_ctypes,socketcan_native,usb2can,vector,virtual}]

    A simple CAN viewer terminal application written in Python

    Optional arguments:
      -h, --help            Show this help message and exit
      --version             Show program's version number and exit
      -b, --bitrate BITRATE
                            Bitrate to use for the given CAN interface
      -c, --channel CHANNEL
                            Most backend interfaces require some sort of channel.
                            For example with the serial interface the channel
                            might be a rfcomm device: "/dev/rfcomm0" with the
                            socketcan interfaces valid channel examples include:
                            "can0", "vcan0". (default: use default for the
                            specified interface)
      -d, --decode {<id>:<format>,<id>:<format>:<scaling1>:...:<scalingN>,file.txt}
                            Specify how to convert the raw bytes into real values.
                            The ID of the frame is given as the first argument and the format as the second.
                            The Python struct package is used to unpack the received data
                            where the format characters have the following meaning:
                                  < = little-endian, > = big-endian
                                  x = pad byte
                                  c = char
                                  ? = bool
                                  b = int8_t, B = uint8_t
                                  h = int16, H = uint16
                                  l = int32_t, L = uint32_t
                                  q = int64_t, Q = uint64_t
                                  f = float (32-bits), d = double (64-bits)
                            Fx to convert six bytes with ID 0x100 into uint8_t, uint16 and uint32_t:
                              $ python -m can.viewer -d "100:<BHL"
                            Note that the IDs are always interpreted as hex values.
                            An optional conversion from integers to real units can be given
                            as additional arguments. In order to convert from raw integer
                            values the values are multiplied with the corresponding scaling value,
                            similarly the values are divided by the scaling value in order
                            to convert from real units to raw integer values.
                            Fx lets say the uint8_t needs no conversion, but the uint16 and the uint32_t
                            needs to be divided by 10 and 100 respectively:
                              $ python -m can.viewer -d "101:<BHL:1:10.0:100.0"
                            Be aware that integer division is performed if the scaling value is an integer.
                            Multiple arguments are separated by spaces:
                              $ python -m can.viewer -d "100:<BHL" "101:<BHL:1:10.0:100.0"
                            Alternatively a file containing the conversion strings separated by new lines
                            can be given as input:
                              $ cat file.txt
                                  100:<BHL
                                  101:<BHL:1:10.0:100.0
                              $ python -m can.viewer -d file.txt
      -f, --filter {<can_id>:<can_mask>,<can_id>~<can_mask>}
                            Comma separated CAN filters for the given CAN interface:
                                  <can_id>:<can_mask> (matches when <received_can_id> & mask == can_id & mask)
                                  <can_id>~<can_mask> (matches when <received_can_id> & mask != can_id & mask)
                            Fx to show only frames with ID 0x100 to 0x103:
                                  python -m can.viewer -f 100:7FC
                            Note that the ID and mask are alway interpreted as hex values
      -i, --interface {iscan,ixxat,kvaser,neovi,nican,pcan,serial,slcan,socketcan,socketcan_ctypes,socketcan_native,usb2can,vector,virtual}
                            Specify the backend CAN interface to use.

    Shortcuts:
            +---------+-------------------------+
            |   Key   |       Description       |
            +---------+-------------------------+
            | ESQ/q   | Exit the viewer         |
            | c       | Clear the stored frames |
            | s       | Sort the stored frames  |
            | SPACE   | Pause the viewer        |
            | UP/DOWN | Scroll the viewer       |
            +---------+-------------------------+
