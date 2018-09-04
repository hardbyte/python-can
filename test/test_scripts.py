#!/usr/bin/env python
# coding: utf-8

"""
This module tests that the scripts are all callable.
"""

from __future__ import absolute_import

import subprocess
import unittest
import errno


class TestCanScript(object):

    def do_commands_exist(self):
        """This test calls each scripts once and veifies that the help
        can be read without any errors.
        """
        for command in self._commands():
            try:
                subprocess.check_output(COMMANDS.spli(), stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                self.assertEqual(e.returncode, errno.EINVAL,
                    'Calling "{}" failed:\n{}'.format(command, e.output))

    def does_not_crash(self):
        # test import
        module = self._import()
        # test main method
        module.main()


class TestLoggerScript(unittest.TestCase, TestCanScript):

    def _commands(self):
        return (
            "can_logger.py --help",
            "python -m can.logger --help",
            "python -m can.scripts.logger --help"
        )

    def _import(self):
        import can.scripts.logger as module
        return module


class TestPlayerScript(unittest.TestCase, TestCanScript):

    def _commands(self):
        return (
            "can_player.py --help",
            "python -m can.player --help",
            "python -m can.scripts.player --help"
        )

    def _import(self):
        import can.scripts.player as module
        return module


# TODO add #390


if __name__ == '__main__':
    unittest.main()
