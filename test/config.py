#!/usr/bin/env python
# coding: utf-8

"""
This module contains various configuration for the tests.

Some tests are skipped when run on a CI server because they are not
reproducible, see #243 (https://github.com/hardbyte/python-can/issues/243).
"""

import platform
from os import environ as environment


def env(name): # type: bool
    return environment.get(name, '').lower() in ("yes", "true", "t", "1")


# ############################## Continuos integration

# see here for the environment variables that are set on the CI servers:
#   - https://docs.travis-ci.com/user/environment-variables/
#   - https://www.appveyor.com/docs/environment-variables/

IS_TRAVIS = env('TRAVIS')
IS_APPVEYOR = env('APPVEYOR')

IS_CI = IS_TRAVIS or IS_APPVEYOR or env('CI') or env('CONTINUOUS_INTEGRATION')

if IS_APPVEYOR and IS_TRAVIS:
    raise EnvironmentError("IS_APPVEYOR and IS_TRAVIS cannot be both True at the same time")


# ############################## Platforms

_sys = platform.system().lower()
IS_WINDOWS = "windows" in _sys or ("win" in _sys and "darwin" not in _sys)
IS_LINUX = "linux" in _sys
IS_OSX = "darwin" in _sys
IS_UNIX = IS_LINUX or IS_OSX

if (IS_WINDOWS and IS_LINUX) or (IS_LINUX and IS_OSX) or (IS_WINDOWS and IS_OSX):
    raise EnvironmentError(
        "only one of IS_WINDOWS ({}), IS_LINUX ({}) and IS_OSX ({}) ".format(IS_WINDOWS, IS_LINUX, IS_OSX) +
        "can be True at the same time " +
        '(platform.system() == "{}")'.format(platform.system())
    )


# ############################## What tests to run

TEST_CAN_FD = True

TEST_INTERFACE_SOCKETCAN = IS_LINUX and env('TEST_SOCKETCAN')
