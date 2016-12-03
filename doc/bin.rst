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



