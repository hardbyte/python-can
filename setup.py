import os
from setuptools import setup, find_packages


def GetVersionNumber():
    os.system("hg id > id.tmp")
    tagFile = open("id.tmp", "r")
    tagLine = tagFile.readline()
    tag = tagLine.split(" ")[1].replace("\n", "")
    if tag != "tip":
        retVal = tag
    else:
        retVal = "dev_%s" % tagLine.split(" ")[0]
    tagFile.close()
    os.unlink("id.tmp")
    return retVal

if __name__ == "__main__":
    setup(
        name="pycanlib",
        version=GetVersionNumber(),
        packages=find_packages(exclude=["test"]),
        scripts=["./bin/can_logger.py"],
    )
