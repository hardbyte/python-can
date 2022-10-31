#!/usr/bin/env python

"""
Setup script for the `can` package.
Learn more at https://github.com/hardbyte/python-can/
"""

# pylint: disable=invalid-name

from os import listdir
from os.path import isfile, join
import re
import logging
from setuptools import setup, find_packages

logging.basicConfig(level=logging.WARNING)

with open("can/__init__.py", "r", encoding="utf-8") as fd:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)

with open("README.rst", "r", encoding="utf-8") as f:
    long_description = f.read()

# Dependencies
extras_require = {
    "seeedstudio": ["pyserial>=3.0"],
    "serial": ["pyserial~=3.0"],
    "neovi": ["filelock", "python-ics>=2.12"],
    "canalystii": ["canalystii>=0.1.0"],
    "cantact": ["cantact>=0.0.7"],
    "gs_usb": ["gs_usb>=0.2.1"],
    "nixnet": ["nixnet>=0.3.1"],
    "pcan": ["uptime~=3.0.1"],
    "viewer": [
        'windows-curses;platform_system=="Windows" and platform_python_implementation=="CPython"'
    ],
}

setup(
    # Description
    name="python-can",
    url="https://github.com/hardbyte/python-can",
    description="Controller Area Network interface module for Python",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        # a list of all available ones: https://pypi.org/classifiers/
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Natural Language :: English",
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
        "Topic :: Utilities",
    ],
    version=version,
    packages=find_packages(exclude=["test*", "doc", "scripts", "examples"]),
    scripts=list(filter(isfile, (join("scripts/", f) for f in listdir("scripts/")))),
    author="python-can contributors",
    license="LGPL v3",
    package_data={
        "": ["README.rst", "CONTRIBUTORS.txt", "LICENSE.txt", "CHANGELOG.md"],
        "doc": ["*.*"],
        "examples": ["*.py"],
        "can": ["py.typed"],
    },
    # Installation
    # see https://www.python.org/dev/peps/pep-0345/#version-specifiers
    python_requires=">=3.7",
    install_requires=[
        "setuptools",
        "wrapt~=1.10",
        "typing_extensions>=3.10.0.0",
        'pywin32;platform_system=="Windows" and platform_python_implementation=="CPython"',
        'msgpack~=1.0.0;platform_system!="Windows"',
        "packaging",
    ],
    extras_require=extras_require,
)
