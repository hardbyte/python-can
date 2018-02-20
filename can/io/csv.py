#!/usr/bin/env python
# coding: utf-8

"""
This modules contains the handler for CSV (comma seperated values) files.
"""

import base64

from can.listener import Listener


# TODO allow other seperators in CSVWriter
# TODO add a CSVReader

class CSVWriter(Listener):
    """Writes a comma separated text file of

       * timestamp,
       * arbitration id,
       * flags (extended, remote, error),
       * dlc and
       * data

    for each messages received. Each line is terminated with a '\\n'.
    """

    def __init__(self, filename):
        self.csv_file = open(filename, 'wt')

        # Write a header row
        self.csv_file.write("timestamp, arbitration id, extended, remote, error, dlc, data\n")

    def on_message_received(self, msg):
        row = ','.join([
            str(msg.timestamp),
            hex(msg.arbitration_id),
            '1' if msg.id_type else '0',
            '1' if msg.is_remote_frame else '0',
            '1' if msg.is_error_frame else '0',
            str(msg.dlc),
            base64.b64encode(msg.data).decode('utf8')
        ])
        self.csv_file.write(row + '\n')

    def stop(self):
        self.csv_file.flush()
        self.csv_file.close()
