import os
from setuptools import setup, find_packages
import sys

sys.path.append(".")

from pycanlib import CAN

if __name__ == "__main__":
    _version = CAN.get_version_number()
    _versionNumberFileName = "./pycanlib/version.txt"
    _versionFile = open(_versionNumberFileName, "w")
    _versionFile.write(_version)
    _versionFile.close()
    setup(
        name="pycanlib",
        version=_version,
        packages=find_packages(exclude=["test"]),
        package_data={"pycanlib": ["version.txt"]},
        scripts=["./bin/can_logger.py", "./bin/xml2tdv.py",
          "./bin/dat2tdv.py", "./bin/ipy_profile_pycanlib.py",
          "./examples/getchanneldata.py"],
    )
