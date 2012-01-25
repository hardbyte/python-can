"""
setup.py: contains the functionality used to create installer packages
for pycanlib, as well as installing it from source. It requires the
setuptools package to be installed.

Copyright (C) 2010 Dynamic Controls

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Contact details
---------------

Postal address:
    Dynamic Controls
    17 Print Place
    Addington
    Christchurch 8024
    New Zealand

E-mail: bpowell AT dynamiccontrols DOT com
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
    py_modules = ['ipy_profile_pycanlib'],
    author="Ben Powell",
    author_email="bpowell AT dynamiccontrols DOT com",
    description="Python wrapper for Kvaser's CANLIB SDK",
    license="GPL v3",
    keywords="CAN Kvaser CANLIB",
    package_data={"pycanlib": ["version.txt"], "": ["CONTRIBUTORS.txt", "LICENSE.txt"], "doc": ["*.*"]},
    scripts=["./bin/can_logger.py", "./bin/dat2tdv.py"],#, "./bin/ipy_profile_pycanlib.py"]
    )
