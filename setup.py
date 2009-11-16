import os
import re
from setuptools import setup, find_packages


def GetVersionNumber():
    os.system("hg tip > version.tmp")
    versionInfoFile = open("version.tmp", "r")
    infoDict = {}
    for line in versionInfoFile:
        line = line.replace("\n", "")
        print line
        if ":" in line:
            (name, value) = line.split(": ")
            infoDict[name] = value
    if re.match(infoDict["tag"], "/S./S") != None:
        retVal = infoDict["tag"]
    else:
        _changeSet = infoDict["changeset"]
        retVal = "dev_" + _changeSet[(_changeSet.index(":") + 1):]
    versionInfoFile.close()
    os.unlink("version.tmp")
    return retVal

if __name__ == "__main__":
    setup(
        name="pycanlib",
        version=GetVersionNumber(),
        packages=find_packages(),
    )
