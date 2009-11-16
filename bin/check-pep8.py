import os


def _CheckDirectory(arg, dirname, names):
    for _name in names:
        if os.path.splitext(_name)[1] == ".py":
            os.system("pep8-script.py %s --repeat" %
                      os.path.join(dirname, _name))

if __name__ == "__main__":
    os.path.walk("..", _CheckDirectory, None)
