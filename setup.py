"""
python-can requires the setuptools package to be installed.
"""

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

__version__ = 1.1

# TODO
# This dict will be updated as we try to select the best option during
# the build process. However, values in setup.cfg will be used, if
# defined.
rc = {'backend': 'socketcan'}

setup(
    name="python-can",
    url="https://bitbucket.org/hardbyte/python-can",
    version=__version__,
    packages=find_packages(),
    author="Brian Thorne",
    author_email="bthorne@dynamiccontrols.com",
    description="Controller Area Network interface module for Python",
    license="LGPL v3",
    package_data={
        "": ["CONTRIBUTORS.txt", "LICENSE.txt"],
        "doc": ["*.*"]
    },

    scripts=["./bin/can_logger.py", "./bin/can_printer.py", './bin/j1939_logger.py'],
)
