rmdir /Q /S .\html
coverage erase
nosetests --with-coverage --cover-inclusive --cover-package=CAN --cover-package=canlib --cover-package=canstat --cover-package=CANLIBErrorHandlers
coverage html -d./html
pause