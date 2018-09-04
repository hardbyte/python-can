#!/usr/bin/env python
# coding: utf-8

"""
This module tests that the scripts are callable.
"""

from __future__ import absolute_import

import subprocess
import unittest


#: these are commands that should return successfully
COMMANDS = (
    "can_logger.py --help",
    "python -m can.logger --help",
    "python -m can.scripts.logger --help",

    "can_player.py --help",
    "python -m can.player --help",
    "python -m can.scripts.player --help",

    # TODO add #390
)


class TestCanScripts(unittest.TestCase):

    def do_commands_exist(self):
        """This test calls each scripts once and veifies that the help
        can be read without any errors.
        """
        for command in COMMANDS:
            try:
                subprocess.check_output(COMMANDS.spli(), stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                self.fail('Calling "{}" failed:\n{}'.format(command, e.output))


if __name__ == '__main__':
    unittest.main()
