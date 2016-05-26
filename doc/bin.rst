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


j1939_logger.py
---------------

command line help (``--help``)::

    usage: j1939_logger.py [-h] [-v] [-i {socketcan,kvaser,serial}]
                           [--pgn PGN | --source SOURCE | --filter FILTER]
                           channel

    Log J1939 traffic, printing messages to stdout or to a given file

    positional arguments:
      channel
                            Most backend interfaces require some sort of channel. For example with the serial
                            interface the channel might be a rfcomm device: /dev/rfcomm0
                            Other channel examples are: can0, vcan0

    optional arguments:
      -h, --help            show this help message and exit
      -v
                                How much information do you want to see at the command line?
                                You can add several of these e.g., -vv is DEBUG
      -i {socketcan,kvaser,serial}, --interface {socketcan,kvaser,serial}
                            Which backend do you want to use?
      --pgn PGN
                            Only listen for messages with given Parameter Group Number (PGN).
                            Can be used more than once. Give either hex 0xEE00 or decimal 60928
      --source SOURCE
                            Only listen for messages from the given Source address
                            Can be used more than once. Give either hex 0x0E or decimal.
      --filter FILTER
                            A json file with more complicated filtering rules.

                            An example file that subscribes to all messages from SRC=0
                            and two particular PGNs from SRC=1:

                            [
                              {
                                "source": 1,
                                "pgn": 61475
                              }
                              {
                                "source": 1,
                                "pgn": 61474
                              }
                              {
                                "source": 0
                              }
                            ]



Pull requests welcome!
    https://bitbucket.org/hardbyte/python-can