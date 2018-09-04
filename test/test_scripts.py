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
        # clean out the argument list
        sys.argv = sys.argv[:1]

    __test__ = False

    __metaclass__ = ABCMeta

    #@unittest.skipUnless(IS_UNIX, "commands may only be available on unix")
    def test_do_commands_exist(self):
        """This test calls each scripts once and veifies that the help
        can be read without any errors.
        """
        for command in self._commands():
            try:
                subprocess.check_output(command.split(), stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                self.assertEqual(e.returncode, errno.EINVAL,
                    'Calling "{}" failed (exit code was {} and not EINVAL/22):\n{}'
                    .format(command, e.returncode, e.output))

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
        pass

    @abstractmethod
    def _import(self):
        pass


class TestLoggerScript(CanScriptTest):

    __test__ = True

    def _commands(self):
        return (
            "can_logger.py --help",
            "python -m can.logger --help",
            "python -m can.scripts.logger --help"
        )

    def _import(self):
        import can.scripts.logger as module
        return module


class TestPlayerScript(CanScriptTest):

    __test__ = True

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
