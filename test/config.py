#!/usr/bin/env python

"""
This module contains various configuration for the tests.

Some tests are skipped when run on a CI server because they are not
reproducible, see for example #243 and #940.
"""

import platform
from os import environ as environment


def env(name: str) -> bool:
    return environment.get(name, "").lower() in ("yes", "true", "t", "1")


# ############################## Continuous integration

# see here for the environment variables that are set on the CI servers:
#   - https://docs.travis-ci.com/user/environment-variables/
#   - https://docs.github.com/en/actions/reference/environment-variables#default-environment-variables

IS_TRAVIS = env("TRAVIS")
IS_GITHUB_ACTIONS = env("GITHUB_ACTIONS")

IS_CI = IS_TRAVIS or IS_GITHUB_ACTIONS or env("CI") or env("CONTINUOUS_INTEGRATION")

if IS_TRAVIS and IS_GITHUB_ACTIONS:
    raise EnvironmentError(
        f"only one of IS_TRAVIS ({IS_TRAVIS}) and IS_GITHUB_ACTIONS ({IS_GITHUB_ACTIONS}) may be True at the "
        "same time"
    )


# ############################## Platforms

_sys = platform.system().lower()
IS_WINDOWS = "windows" in _sys or ("win" in _sys and "darwin" not in _sys)
IS_LINUX = "linux" in _sys
IS_OSX = "darwin" in _sys
IS_UNIX = IS_LINUX or IS_OSX
del _sys

if (IS_WINDOWS and IS_LINUX) or (IS_LINUX and IS_OSX) or (IS_WINDOWS and IS_OSX):
    raise EnvironmentError(
        f"only one of IS_WINDOWS ({IS_WINDOWS}), IS_LINUX ({IS_LINUX}) and IS_OSX ({IS_OSX}) "
        f'can be True at the same time (platform.system() == "{platform.system()}")'
    )


# ############################## Implementations

IS_PYPY = platform.python_implementation() == "PyPy"


# ############################## What tests to run

TEST_CAN_FD = True

TEST_INTERFACE_SOCKETCAN = IS_LINUX and env("TEST_SOCKETCAN")
