#!/usr/bin/env python
# coding: utf-8

"""
python-can requires the setuptools package to be installed.
"""

from sys import version_info
import re
import logging
from setuptools import setup, find_packages

logging.basicConfig(level=logging.WARNING)

with open('can/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

with open('README.rst', 'r') as f:
    long_description = f.read()

# Dependencies
tests_require = [
    'mock ~= 2.0',
    'nose ~= 1.3.7',
    'pytest ~= 3.6',
    'pytest-timeout ~= 1.2',
    'pyserial ~= 3.0'
]

setup(
    # Description
    name="python-can",
    url="https://github.com/hardbyte/python-can",
    description="Controller Area Network interface module for Python",
    long_description=long_description,

    # Code
    version=version,
    packages=find_packages(exclude=["test", "test.*"]),

    # Author
    author="Brian Thorne",
    author_email="brian@thorne.link",

    # License
    license="LGPL v3",

    # Package data
    package_data={
        "": ["CONTRIBUTORS.txt", "LICENSE.txt", "CHANGELOG.txt"],
        "doc": ["*.*"]
    },

    # Installation
    # see https://www.python.org/dev/peps/pep-0345/#version-specifiers
    python_requires=">=2.7,!=3.0,!=3.1,!=3.2,!=3.3",
    install_requires=[
        'wrapt ~= 1.10',
    ],
    extras_require={
        'serial': ['pyserial >= 3.0'],
        'neovi': ['python-ics >= 2.12'],
        'test': tests_require
    },

    # Testing
    test_suite="nose.collector",
    tests_require=tests_require,
)
