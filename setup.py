"""
Contains the functionality used to create installer packages
for pycanlib, as well as installing it from source. It requires the
setuptools package to be installed.
"""
from setuptools import setup

__version__ = 1.0
setup(
    name="python-can",
    version=__version__,
    packages=['can'],
    author=["Ben Powell", "Brian Thorne", "Rose Lu"],
    author_email="bthorne@dynamiccontrols.com",
    description="Controller Area Network interface module for Python",
    license="LGPL v3",
    
    package_data={
        "": ["CONTRIBUTORS.txt", "LICENSE.txt"],
        "doc": ["*.*"]
        },

    scripts=["./bin/can_logger.py", "./bin/dat2tdv.py"],
    )
