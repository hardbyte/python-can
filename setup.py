"""
Contains the functionality used to create installer packages
for pycanlib, as well as installing it from source. It requires the
setuptools package to be installed.
"""

import os
from setuptools import setup, find_packages, Extension


try:
    import hgversionutils
except ImportError:
    _version = "unknown"
else:
    _version = hgversionutils.get_version_number(os.path.dirname(__file__))
    hgversionutils.write_version_number_file(os.path.join(os.path.dirname(__file__), "pycanlib"))


setup(
    name="pycanlib",
    version=_version,
    packages=find_packages(exclude=["test"]),
    py_modules = ['pycanlib'],
    author="Ben Powell",
    author_email="bpowell AT dynamiccontrols DOT com",
    description="Python wrapper for Kvaser's CANLIB SDK",
    license="GPL v3",
    keywords="CAN Kvaser CANLIB",
    package_data={"pycanlib": ["version.txt"], "": ["CONTRIBUTORS.txt", "LICENSE.txt"], "doc": ["*.*"]},
    scripts=["./bin/can_logger.py", "./bin/dat2tdv.py"],#, "./bin/ipy_profile_pycanlib.py"]
    )
