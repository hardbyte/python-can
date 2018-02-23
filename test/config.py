#!/usr/bin/env python
# coding: utf-8

"""
This module contains some configuration for the tests.

Some tests are skipped when run on a CI server because they are not
reproducible, see #243 (https://github.com/hardbyte/python-can/issues/243).
"""

from os import environ as environment

# see here for the environment variables that are set on the CI servers:
#   - https://docs.travis-ci.com/user/environment-variables/
#   - https://www.appveyor.com/docs/environment-variables/

IS_TRAVIS = environment.get('TRAVIS', '').lower() == 'true'
IS_APPVEYOR = environment.get('APPVEYOR', '').lower() == 'true'

IS_CI = IS_TRAVIS or IS_APPVEYOR or \
        environment.get('CI', '').lower() == 'true' or \
        environment.get('CONTINUOUS_INTEGRATION', '').lower() == 'true'

TEST_CAN_FD = True
