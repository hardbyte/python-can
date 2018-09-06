#!/usr/bin/env python
# coding: utf-8

"""
This module tests that the scripts are all callable.
"""

from __future__ import absolute_import

import subprocess
import unittest
import sys
import errno
from abc import ABCMeta, abstractmethod

from .config import *

class CanScriptTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # clean up the argument list so the call to the main() functions
        # in test_does_not_crash() succeeds
        sys.argv = sys.argv[:1]

    #: this is overridden by the subclasses
    __test__ = False

    __metaclass__ = ABCMeta

    def test_do_commands_exist(self):
        """This test calls each scripts once and veifies that the help
        can be read without any other errors, like the script not being
        found.
        """
        for command in self._commands():
            try:
                subprocess.check_output(command.split(), stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                return_code = e.returncode
                output = e.output
            else:
                return_code = 0
                output = "-- NO OUTPUT --"

            allowed = [0, errno.EINVAL]
            self.assertIn(return_code, allowed,
                    'Calling "{}" failed (exit code was {} and not SUCCESS/0 or EINVAL/22):\n{}'
                    .format(command, return_code, output))

    def test_does_not_crash(self):
        # test import
        module = self._import()
        # test main method
        with self.assertRaises(SystemExit) as cm:
            module.main()
            self.assertEqual(cm.exception.code, errno.EINVAL,
                    'Calling main failed:\n{}'.format(command, e.output))

    @abstractmethod
    def _commands(self):
        """Returns an Iterable of commands that should "succeed", meaning they exit
        normally (exit code 0) or with the exit code for invalid arguments: EINVAL/22.
        """
        pass

    @abstractmethod
    def _import(self):
        """Returns the modue of the script that has a main() function.
        """
        pass


class TestLoggerScript(CanScriptTest):

    __test__ = True

    def _commands(self):
        commands = [
            "python -m can.logger --help",
            "python scripts/can_logger.py --help"
        ]
        if IS_UNIX:
            commands += ["can_logger.py --help"]
        return commands

    def _import(self):
        import can.logger as module
        return module


class TestPlayerScript(CanScriptTest):

    __test__ = True

    def _commands(self):
        commands = [
            "python -m can.player --help",
            "python scripts/can_player.py --help"
        ]
        if IS_UNIX:
            commands += ["can_player.py --help"]
        return commands

    def _import(self):
        import can.player as module
        return module


# TODO add #390


if __name__ == '__main__':
    unittest.main()
