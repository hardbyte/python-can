#!/usr/bin/env python

"""
This module tests that the scripts are all callable.
"""

import errno
import subprocess
import sys
import unittest
from abc import ABCMeta, abstractmethod
from pathlib import Path

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
                args = command if isinstance(command, (list, tuple)) else command.split()
                subprocess.check_output(
                    args,
                    stderr=subprocess.STDOUT,
                    encoding="utf-8",
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

    def _console_command(self, name: str) -> list[str]:
        executable = Path(sys.executable).parent / name
        if IS_WINDOWS:
            executable = executable.with_suffix(".exe")
        return [str(executable), "--help"]

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
            [sys.executable, "-m", "can.logger", "--help"],
            self._console_command("can_logger"),
        ]
        return commands

    def _import(self):
        import can.logger as module

        return module


class TestPlayerScript(CanScriptTest):
    def _commands(self):
        commands = [
            [sys.executable, "-m", "can.player", "--help"],
            self._console_command("can_player"),
        ]
        return commands

    def _import(self):
        import can.player as module

        return module


class TestBridgeScript(CanScriptTest):
    def _commands(self):
        commands = [
            [sys.executable, "-m", "can.bridge", "--help"],
            self._console_command("can_bridge"),
        ]
        return commands

    def _import(self):
        import can.bridge as module

        return module


class TestLogconvertScript(CanScriptTest):
    def _commands(self):
        commands = [
            [sys.executable, "-m", "can.logconvert", "--help"],
            self._console_command("can_logconvert"),
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
