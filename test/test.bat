rmdir /Q /S .\html
coverage erase
nosetests -v --with-coverage --cover-inclusive --cover-package=CAN --cover-package=canlib --cover-package=canstat --cover-package=CANLIBErrorHandlers
coverage html -d./html
pause