"""
Contains the functionality used to create installer packages
for pycanlib, as well as installing it from source. It requires the
setuptools package to be installed.
"""
from setuptools import setup # for the devel command
__version__ = 1.0
setup(
    name="pycanlib",
    version=__version__,
    packages=['pycanlib'],
    author=["Ben Powell", "Brian Thorne", "Rose Lu"],
    author_email="bthorne@dynamiccontrols.com",
    description="Python wrapper for Kvaser's CANLIB SDK",
    license="GPL v3",
    keywords="CAN Kvaser CANLIB",
    package_data={"pycanlib": ["version.txt"], 
                  "": ["CONTRIBUTORS.txt", "LICENSE.txt"],
                  "doc": ["*.*"]},
    scripts=["./bin/can_logger.py", "./bin/dat2tdv.py"],
    )
