"""
python-can requires the setuptools package to be installed.
"""

import logging
from setuptools import setup, find_packages

__version__ = "2.0.0-alpha.1"

logging.basicConfig(level=logging.WARNING)

setup(
    name="python-can",
    url="https://github.com/hardbyte/python-can",
    version=__version__,
    packages=find_packages(),
    author="Brian Thorne",
    author_email="hardbyte@gmail.com",
    description="Controller Area Network interface module for Python",
    long_description=open('README.rst').read(),
    license="LGPL v3",
    package_data={
        "": ["CONTRIBUTORS.txt", "LICENSE.txt"],
        "doc": ["*.*"]
    },

    scripts=[
        "./bin/can_logger.py",
        "./bin/can_player.py",
        "./bin/can_server.py"
    ],

    # Tests can be run using `python setup.py test`
    test_suite="nose.collector",
    tests_require=['mock', 'nose']
)
