#!/usr/bin/env python
# coding: utf-8

"""
python-can requires the setuptools package to be installed.
"""

from __future__ import absolute_import

from os import listdir
from os.path import isfile, join
import re
import logging
import sys
from setuptools import setup, find_packages

logging.basicConfig(level=logging.WARNING)

with open('can/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

with open('README.rst', 'r') as f:
    long_description = f.read()

# Dependencies
extras_require = {
    'serial':   ['pyserial~=3.0'],
    'neovi':    ['python-ics>=2.12', 'filelock']
}

tests_require = [
    'mock~=2.0',
    'pytest~=4.6',
    'pytest-timeout~=1.3',
    'pytest-cov~=2.8',
    # coveragepy==5.0 fails with `Safety level may not be changed inside a transaction`
    # on python 3.6 on MACOS
    'coverage<5',
    'codecov~=2.0',
    'future',
    'six',
    'hypothesis~=4.56'
] + extras_require['serial']

extras_require['test'] = tests_require

# Check for 'pytest-runner' only if setup.py was invoked with 'test'.
# This optimizes setup.py for cases when pytest-runner is not needed,
# using the approach that is suggested upstream.
#
# See https://pypi.org/project/pytest-runner/#conditional-requirement
needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
pytest_runner = ["pytest-runner"] if needs_pytest else []

setup(
    # Description
    name="python-can",
    url="https://github.com/hardbyte/python-can",
    description="Controller Area Network interface module for Python",
    long_description=long_description,
    classifiers=[
        # a list of all available ones: https://pypi.org/classifiers/
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Telecommunications Industry",
        "Natural Language :: English",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: Utilities"
    ],

    # Code
    version=version,
    packages=find_packages(exclude=["test*", "doc", "scripts", "examples"]),
    scripts=list(filter(isfile, (join("scripts/", f) for f in listdir("scripts/")))),

    # Author
    author="Brian Thorne",
    author_email="brian@thorne.link",

    # License
    license="LGPL v3",

    # Package data
    package_data={
        "": ["README.rst", "CONTRIBUTORS.txt", "LICENSE.txt", "CHANGELOG.txt"],
        "doc": ["*.*"],
        "examples": ["*.py"]
    },

    # Installation
    # see https://www.python.org/dev/peps/pep-0345/#version-specifiers
    python_requires=">=2.7",
    install_requires=[
        'wrapt~=1.10',
        'aenum',
        'typing;python_version<"3.5"',
        'windows-curses;platform_system=="Windows"',
    ],
    setup_requires=pytest_runner,
    extras_require=extras_require,
    tests_require=tests_require
)
