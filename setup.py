"""
python-can requires the setuptools package to be installed.
"""

from setuptools import setup, find_packages

__version__ = 1.4

import logging
logging.basicConfig(level=logging.WARNING)

setup(
    name="python-can",
    url="https://bitbucket.org/hardbyte/python-can",
    version=__version__,
    packages=find_packages(),
    author="Brian Thorne",
    author_email="hardbyte@gmail.com",
    description="Controller Area Network interface module for Python",
    long_description=open('README.md').read(),
    license="LGPL v3",
    package_data={
        "": ["CONTRIBUTORS.txt", "LICENSE.txt"],
        "doc": ["*.*"]
    },

    scripts=["./bin/can_logger.py", './bin/j1939_logger.py'],

    # Tests can be run using `python setup.py test`
    test_suite="nose.collector",
    tests_require=['mock']
)
