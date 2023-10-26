#!/usr/bin/env python

"""
This module tests that the scripts are all callable.
"""

import errno
import subprocess
import sys
import unittest
from abc import ABCMeta, abstractmethod

from .config import *


class CanScriptTest(unittest.TestCase, metaclass=ABCMeta):
    @classmethod
    def setUpClass(cls):
        # clean up the argument list so the call to the main() functions
        # in test_does_not_crash() succeeds
        sys.argv = sys.argv[:1]

    def test_do_commands_exist(self):
        """This test calls each scripts once and verifies that the help
        can be read without any other errors, like the script not being
        found.
        """
        for command in self._commands():
            try:
                subprocess.check_output(
                    command.split(),
                    stderr=subprocess.STDOUT,
                    encoding="utf-8",
                    shell=IS_WINDOWS,
                )
            except subprocess.CalledProcessError as e:
                return_code = e.returncode
                output = e.output
            else:
                return_code = 0
                output = "-- NO OUTPUT --"

            allowed = [0, errno.EINVAL]
            self.assertIn(
                return_code,
                allowed,
                'Calling "{}" failed (exit code was {} and not SUCCESS/0 or EINVAL/22):\n{}'.format(
                    command, return_code, output
                ),
            )

    def test_does_not_crash(self):
        # test import
        module = self._import()
        # test main method
        with self.assertRaises(SystemExit) as cm:
            module.main()
        self.assertEqual(cm.exception.code, errno.EINVAL)

    @abstractmethod
    def _commands(self):
        """Returns an Iterable of commands that should "succeed", meaning they exit
        normally (exit code 0) or with the exit code for invalid arguments: EINVAL/22.
        """
        pass

    @abstractmethod
    def _import(self):
        """Returns the modue of the script that has a main() function."""
        pass


class TestLoggerScript(CanScriptTest):
    def _commands(self):
        commands = [
            "python -m can.logger --help",
            "can_logger --help",
        ]
        return commands

    def _import(self):
        import can.logger as module

        return module


class TestPlayerScript(CanScriptTest):
    def _commands(self):
        commands = [
            "python -m can.player --help",
            "can_player --help",
        ]
        return commands

    def _import(self):
        import can.player as module

        return module


class TestLogconvertScript(CanScriptTest):
    def _commands(self):
        commands = [
            "python -m can.logconvert --help",
            "can_logconvert --help",
        ]
        return commands

    def _import(self):
        import can.logconvert as module

        return module


# TODO add #390


# this excludes the base class from being executed as a test case itself
del CanScriptTest


if __name__ == "__main__":
    unittest.main()
