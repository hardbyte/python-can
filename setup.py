import os
from setuptools import setup, find_packages

import hgversionutils

if __name__ == "__main__":
    hgversionutils.write_version_number_file(os.path.join(os.path.dirname(__file__), "pycanlib"))
    setup(name="pycanlib", version=hgversionutils.get_version_number(os.path.dirname(__file__)), packages=find_packages(exclude=["test"]), package_data={"pycanlib": ["version.txt"]}, scripts=["./bin/can_logger.py", "./bin/dat2tdv.py", "./bin/ipy_profile_pycanlib.py", "./examples/getchanneldata.py", "./examples/busload.py"])
