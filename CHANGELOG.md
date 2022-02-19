Version 4.0.0
====

TL;DR: This release includes a ton of improvements from 2.5 years of development! 🎉 Test thoroughly after switching.

For more than two years, there was no major release of *python-can*.
However, development was very much active over most of this time, and many parts were switched out and improved.
Over this time, over 530 issues and PRs have been resolved or merged, and discussions took place in even more.
Statistics of the final diff: About 200 files changed due to ~22k additions and ~7k deletions from more than thirty contributors.

This changelog diligently lists the major changes but does not promise to be the complete list of changes.
Therefore, users are strongly advised to thoroughly test their programs against this new version.
Re-reading the documentation for your interfaces might be helpful too as limitations and capabilities might have changed or are more explicit.
While we did try to avoid breaking changes, in some cases it was not feasible and in particular, many implementation details have changed.

Major features
--------------

* Type hints for the core library and some interfaces (#652 and many others)
* Support for Python 3.7-3.10+ only (dropped support for Python 2.* and 3.5-3.6) (#528 and many others)
* [Granular and unified exceptions](https://python-can.readthedocs.io/en/develop/api.html#errors) (#356, #562, #1025; overview in #1046)
* [Support for automatic configuration detection](https://python-can.readthedocs.io/en/develop/api.html#can.detect_available_configs) in most interfaces (#303, #640, #641, #811, #1077, #1085)
* Better alignment of interfaces and IO to common conventions and semantics

New interfaces
--------------

* udp_multicast (#644)
* robotell (#731)
* cantact (#853)
* gs_usb (#905)
* nixnet (#968, #1154)
* neousys (#980, #1076)
* socketcand (#1140)
* etas (#1144)

Improved interfaces
-------------------

* socketcan
  * Support for multiple Cyclic Messages in Tasks (#610)
  * Socketcan crash when attempting to stop CyclicSendTask with same arbitration ID (#605, #638, #720)
  * Relax restriction of arbitration ID uniqueness for CyclicSendTask (#721, #785, #930)
  * Add nanosecond resolution time stamping to socketcan (#938, #1015)
  * Add support for changing the loopback flag (#960)
  * Socketcan timestamps are missing sub-second precision (#1021, #1029)
  * Add parameter to ignore CAN error frames (#1128)
* socketcan_ctypes
  * Removed and replaced by socketcan after deprecation period
* socketcan_native
  * Removed and replaced by socketcan after deprecation period
* vector
  * Add chip state API (#635)
  * Add methods to handle non message events (#708)
  * Implement XLbusParams (#718)
  * Add support for VN8900 xlGetChannelTime function (#732, #733)
  * Add vector hardware config popup (#774)
  * Fix Vector CANlib treatment of empty app name (#796, #814)
  * Make VectorError pickleable (#848)
  * Add methods get_application_config(), set_application_config() and set_timer_rate() to VectorBus (#849)
  * Interface arguments are now lowercase (#858)
  * Fix errors using multiple Vector devices (#898, #971, #977)
  * Add more interface information to channel config (#917)
  * Improve timestamp accuracy on Windows (#934, #936)
  * Fix error with VN8900 (#1184)
  * Add static typing (#1229)
* PCAN
  * Do not incorrectly reset CANMsg.MSGTYPE on remote frame (#659, #681)
  * Add support for error frames (#711)
  * Added keycheck for windows platform for better error message (#724)
  * Added status_string method to return simple status strings (#725)
  * Fix timestamp timezone offset (#777, #778)
  * Add [Cygwin](https://www.cygwin.com/) support (#840) 
  * Update PCAN basic Python file to February 7, 2020 (#929)
  * Fix compatibility with the latest macOS SDK (#947, #948, #957, #976)
  * Allow numerical channel specifier (#981, #982)
  * macOS: Try to find libPCBUSB.dylib before loading it (#983, #984)
  * Disable command PCAN_ALLOW_ERROR_FRAMES on macOS (#985)
  * Force english error messages (#986, #993, #994)
  * Add set/get device number (#987)
  * Timestamps are silently incorrect on Windows without uptime installed (#1053, #1093)
  * Implement check for minimum version of pcan library (#1065, #1188)
  * Handle case where uptime is imported successfully but returns None (#1102, #1103)
* slcan
  * Fix bitrate setting (#691)
  * Fix fileno crash on Windows (#924)
* ics_neovi
  * Filter out Tx error messages (#854)
  * Adding support for send timeout (#855)
  * Raising more precise API error when set bitrate fails (#865)
  * Avoid flooding the logger with many errors when they are the same (#1125)
  * Omit the transmit exception cause for brevity (#1086)
  * Raise ValueError if message data is over max frame length (#1177, #1181)
  * Setting is_error_frame message property (#1189)
* ixxat
  * Raise exception on busoff in recv() (#856)
  * Add support for 666 kbit/s bitrate (#911)
  * Add function to list hwids of available devices (#926)
  * Add CAN FD support (#1119)
* seeed
  * Fix fileno crash on Windows (#902)
* kvaser
  * Improve timestamp accuracy on Windows (#934, #936)
* usb2can
  * Fix "Error 8" on Windows and provide better error messages (#989)
  * Fix crash on initialization (#1248, #1249)
  * Pass flags instead of flags_t type upon initialization (#1252)
* serial
  * Fix "TypeError: cannot unpack non-iterable NoneType" and more robust error handling (#1000, #1010)
* canalystii
  * Fix is_extended_id (#1006)
  * Fix transmitting onto a busy bus (#1114)
  * Replace binary library with python driver (#726, #1127)

Other API changes and improvements
----------------------------------

* CAN FD frame support is pretty complete (#963)
  * ASCWriter (#604) and ASCReader (#741)
  * Canutils reader and writer (#1042)
  * Logger, viewer and player tools can handle CAN FD (#632)
  * Many bugfixes and more testing coverage
* IO
  * [Log rotation](https://python-can.readthedocs.io/en/develop/listeners.html#can.SizedRotatingLogger) (#648, #874, #881, #1147)
  * Transparent (de)compression of [gzip](https://docs.python.org/3/library/gzip.html) files for all formats (#1221)
  * Add [plugin support to can.io Reader/Writer](https://python-can.readthedocs.io/en/develop/listeners.html#listener) (#783)
  * ASCReader/Writer enhancements like increased robustness (#820, #1223, #1256, #1257)
  * Adding absolute timestamps to ASC reader (#761)
  * Support other base number (radix) at ASCReader (#764)
  * Add [logconvert script](https://python-can.readthedocs.io/en/develop/scripts.html#can-logconvert) (#1072, #1194)
  * Adding support for gzipped ASC logging file (.asc.gz) (#1138)
  * Improve [IO class hierarchy](https://python-can.readthedocs.io/en/develop/internal-api.html#module-can.io.generic) (#1147)
* An [overview over various "virtual" interfaces](https://python-can.readthedocs.io/en/develop/interfaces/virtual.html#other-virtual-interfaces) (#644)
* Make ThreadBasedCyclicSendTask event based & improve timing accuracy (#656)
* Ignore error frames in can.player by default, add --error-frames option (#690)
* Add an error callback to ThreadBasedCyclicSendTask (#743, #781)
* Add direction to CAN messages (#773, #779, #780, #852, #966)
* Notifier no longer raises handled exceptions in rx_thread (#775, #789) but does so if no listener handles them (#1039, #1040)
* Changes to serial device number decoding (#869)
* Add a default fileno function to the BusABC (#877)
* Disallow Messages to simultaneously be "FD" and "remote" (#1049)
* Speed up interface plugin imports by avoiding pkg_resources (#1110)
* Allowing for extra config arguments in can.logger (#1142, #1170)
* Add changed byte highlighting to viewer.py (#1159)
* Change DLC to DL in Message.\_\_str\_\_() (#1212)

Other Bugfixes
--------------

* BLF PDU padding (#459)
* stop_all_periodic_tasks skipping every other task (#634, #637, #645)
* Preserve capitalization when reading config files (#702, #1062)
* ASCReader: Skip J1939Tp messages (#701)
* Fix crash in Canutils Log Reader when parsing RTR frames (#713)
* Various problems with the installation of the library
* ASCWriter: Fix date format to show correct day of month (#754)
* Fixes that some BLF files can't be read ( #763, #765)
* Seek for start of object instead of calculating it (#786, #803, #806)
* Only import winreg when on Windows (#800, #802)
* Find the correct Reader/Writer independently of the file extension case (#895)
* RecursionError when unpickling message object (#804, #885, #904)
* Move "filelock" to neovi dependencies (#943)
* Bus() with "fd" parameter as type bool always resolved to fd-enabled configuration (#954, #956)
* Asyncio code hits error due to deprecated loop parameter (#1005, #1013)
* Catch time before 1970 in ASCReader (#1034)
* Fix a bug where error handlers were not called correctly (#1116)
* Improved user interface of viewer script (#1118)
* Correct app_name argument in logger (#1151)
* Calling stop_all_periodic_tasks() in BusABC.shutdown() and all interfaces call it on shutdown (#1174)
* Timing configurations do not allow int (#1175)
* Some smaller bugfixes are not listed here since the problems were never part of a proper release
* ASCReader & ASCWriter using DLC as data length (#1245, #1246)

Behind the scenes & Quality assurance
-------------------------------------

* We publish both source distributions (`sdist`) and binary wheels (`bdist_wheel`) (#1059, #1071)
* Many interfaces were partly rewritten to modernize the code or to better handle errors
* Performance improvements
* Dependencies have changed
* Derive type information in Sphinx docs directly from type hints (#654)
* Better documentation in many, many places; This includes the examples, README and python-can developer resources
* Add issue templates (#1008, #1017, #1018, #1178)
* Many continuous integration (CI) discussions & improvements (for example: #951, #940, #1032)
  * Use the [mypy](https://github.com/python/mypy) static type checker (#598, #651)
  * Use [tox](https://tox.wiki/en/latest/) for testing (#582, #833, #870)
  * Use [Mergify](https://mergify.com/) (#821, #835, #937)
  * Switch between various CI providers, abandoned [AppVeyor](https://www.appveyor.com/) (#1009) and partly [Travis CI](https://travis-ci.org/), ended up with mostly [GitHub Actions](https://docs.github.com/en/actions) (#827, #1224)
  * Use the [black](https://black.readthedocs.io/en/stable/) auto-formatter (#950)
  * [Good test coverage](https://app.codecov.io/gh/hardbyte/python-can/branch/develop) for all but the interfaces
* Testing: Many of the new features directly added tests, and coverage of existing code was improved too (for example: #1031, #581, #585, #586, #942, #1196, #1198)

Version 3.3.4
====

Last call for Python2 support.

* #850 Fix socket.error is a deprecated alias of OSError used on Python versions lower than 3.3.

Version 3.3.3
====

Backported fixes from 4.x development branch which targets Python 3.

* #798 Backport caching msg.data value in neovi interface.
* #796 Fix Vector CANlib treatment of empty app name.
* #771 Handle empty CSV file.
* #741 ASCII reader can now handle FD frames.
* #740 Exclude test packages from distribution.
* #713 RTR crash fix in canutils log reader parsing RTR frames.
* #701 Skip J1939 messages in ASC Reader.
* #690 Exposes a configuration option to allow the CAN message player to send error frames
  (and sets the default to not send error frames).
* #638 Fixes the semantics provided by periodic tasks in SocketCAN interface.
* #628 Avoid padding CAN_FD_MESSAGE_64 objects to 4 bytes.
* #617 Fixes the broken CANalyst-II interface.
* #605 Socketcan BCM status fix.


Version 3.3.2
====

Minor bug fix release addressing issue in PCAN RTR.

Version 3.3.1
====

Minor fix to setup.py to only require pytest-runner when necessary.

Version 3.3.0
====

* Adding CAN FD 64 frame support to blf reader
* Updates to installation instructions
* Clean up bits generator in PCAN interface #588
* Minor fix to use latest tools when building wheels on travis.

Version 3.2.1
====

* CAN FD 64 frame support to blf reader
* Minor fix to use latest tools when building wheels on travis.
* Updates links in documentation.

Version 3.2.0
====


Major features
--------------

* FD support added for Pcan by @bmeisels with input from
  @markuspi, @christiansandberg & @felixdivo in PR #537
* This is the last version of python-can which will support Python 2.7
  and Python 3.5. Support has been removed for Python 3.4 in this
  release in PR #532

Other notable changes
---------------------

* #533 BusState is now an enum.
* #535 This release should automatically be published to PyPi by travis.
* #577 Travis-ci now uses stages.
* #548 A guide has been added for new io formats.
* #550 Finish moving from nose to pytest.
* #558 Fix installation on Windows.
* #561 Tests for MessageSync added.

General fixes, cleanup and docs changes can be found on the GitHub milestone
https://github.com/hardbyte/python-can/milestone/7?closed=1

Pulls: #522, #526, #527, #536, #540, #546, #547, #548, #533, #559, #569, #571, #572, #575

Backend Specific Changes
------------------------

pcan
~~~~

* FD

slcan
~~~~

* ability to set custom can speed instead of using predefined speed values. #553

socketcan
~~~~

* Bug fix to properly support 32bit systems. #573

usb2can
~~~~

* slightly better error handling
* multiple serial devices can be found
* support for the `_detect_available_configs()` API

Pulls #511, #535

vector
~~~~

* handle `app_name`. #525

Version 3.1.1
====

Major features
--------------

Two new interfaces this release:

- SYSTEC contributed by @idaniel86 in PR #466
- CANalyst-II contributed by @smeng9 in PR #476


Other notable changes
---------------------

* #477 The kvaser interface now supports bus statistics via a custom bus method.
* #434 neovi now supports receiving own messages
* #490 Adding option to override the neovi library name
* #488 Allow simultaneous access to IXXAT cards
* #447 Improvements to serial interface:
  * to allow receiving partial messages
  * to fix issue with  DLC of remote frames
  * addition of unit tests
* #497 Small API changes to `Message` and added unit tests
* #471 Fix CAN FD issue in kvaser interface
* #462 Fix `Notifier` issue with asyncio
* #481 Fix PCAN support on OSX
* #455 Fix to `Message` initializer
* Small bugfixes and improvements

Version 3.1.0
====

Version 3.1.0 was built with old wheel and/or setuptools
packages and was replaced with v3.1.1 after an installation
but was discovered.

Version 3.0.0
====

Major features
--------------

* Adds support for developing `asyncio` applications with `python-can` more easily. This can be useful
  when implementing protocols that handles simultaneous connections to many nodes since you can write
  synchronous looking code without handling multiple threads and locking mechanisms. #388
* New can viewer terminal application. (`python -m can.viewer`) #390
* More formally adds task management responsibility to the `Bus`. By default tasks created with
  `bus.send_periodic` will have a reference held by the bus - this means in many cases the user
  doesn't need to keep the task in scope for their periodic messages to continue being sent. If
  this behavior isn't desired pass `store_task=False` to the `send_periodic` method. Stop all tasks
  by calling the bus's new `stop_all_periodic_tasks` method. #412


Breaking changes
----------------

* Interfaces should no longer override `send_periodic` and instead implement
  `_send_periodic_internal` to allow the Bus base class to manage tasks. #426
* writing to closed writers is not supported any more (it was supported only for some)
* the file in the reader/writer is now always stored in the attribute uniformly called `file`, and not in
  something like `fp`, `log_file` or `output_file`. Changed the name of the first parameter of the
  read/writer constructors from `filename` to `file`.


Other notable changes
---------------------

* can.Message class updated #413
    - Addition of a `Message.equals` method.
    - Deprecate id_type in favor of is_extended_id
    - Initializer parameter extended_id deprecated in favor of is_extended_id
    - documentation, testing and example updates
    - Addition of support for various builtins: __repr__, __slots__, __copy__
* IO module updates to bring consistency to the different CAN message writers and readers. #348
    - context manager support for all readers and writers
    - they share a common super class called `BaseIOHandler`
    - all file handles can now be closed with the `stop()` method
    - the table name in `SqliteReader`/`SqliteWriter` can be adjusted
    - append mode added in `CSVWriter` and `CanutilsLogWriter`
    - [file-like](https://docs.python.org/3/glossary.html#term-file-like-object) and
      [path-like](https://docs.python.org/3/glossary.html#term-path-like-object) objects can now be passed to
      the readers and writers (except to the Sqlite handlers)
    - add a `__ne__()` method to the `Message` class (this was required by the tests)
    - added a `stop()` method for `BufferedReader`
    - `SqliteWriter`: this now guarantees that all messages are being written, exposes some previously internal metrics
      and only buffers messages up to a certain limit before writing/committing to the database.
    - the unused `header_line` attribute from `CSVReader` has been removed
    - privatized some attributes that are only to be  used internally in the classes
    - the method `Listener.on_message_received()` is now abstract (using `@abc.abstractmethod`)
* Start testing against Python 3.7 #380
* All scripts have been moved into `can/scripts`. #370, #406
* Added support for additional sections to the config #338
* Code coverage reports added. #346, #374
* Bug fix to thread safe bus. #397

General fixes, cleanup and docs changes: (#347, #348, #367, #368, #370, #371, #373, #420, #417, #419, #432)

Backend Specific Changes
------------------------

3rd party interfaces
~~~~~~~~~~~~~~~~~~~~

* Deprecated `python_can.interface` entry point instead use `can.interface`. #389

neovi
~~~~~

* Added support for CAN-FD #408
* Fix issues checking if bus is open. #381
* Adding multiple channels support. #415

nican
~~~~~

* implements reset instead of custom `flush_tx_buffer`. #364

pcan
~~~~

* now supported on OSX. #365


serial
~~~~~~

* Removed TextIOWrapper from serial. #383
* switch to `serial_for_url` enabling using remote ports via `loop://`, ``socket://` and `rfc2217://` URLs. #393
* hardware handshake using `rtscts` kwarg #402

socketcan
~~~~~~~~~

* socketcan tasks now reuse a bcm socket #404, #425, #426,
* socketcan bugfix to receive error frames #384

vector
~~~~~~

* Vector interface now implements `_detect_available_configs`. #362
* Added support to select device by serial number. #387

Version 2.2.1 (2018-07-12)
=====

* Fix errors and warnings when importing library on Windows
* Fix Vector backend raising ValueError when hardware is not connected

Version 2.2.0 (2018-06-30)
=====

* Fallback message filtering implemented in Python for interfaces that don't offer better accelerated mechanism.
* SocketCAN interfaces have been merged (Now use `socketcan` instead of either `socketcan_native` and `socketcan_ctypes`),
  this is now completely transparent for the library user.
* automatic detection of available configs/channels in supported interfaces.
* Added synchronized (thread-safe) Bus variant.
* context manager support for the Bus class.
* Dropped support for Python 3.3 (officially reached end-of-life in Sept. 2017)
* Deprecated the old `CAN` module, please use the newer `can` entry point (will be removed in an upcoming major version)

Version 2.1.0 (2018-02-17)
=====

* Support for out of tree can interfaces with pluggy.
* Initial support for CAN-FD for socketcan_native and kvaser interfaces.
* Neovi interface now uses Intrepid Control Systems's own interface library.
* Improvements and new documentation for SQL reader/writer.
* Fix bug in neovi serial number decoding.
* Add testing on OSX to TravisCI
* Fix non english decoding error on pcan
* Other misc improvements and bug fixes


Version 2.0.0 (2018-01-05
=====

After an extended baking period we have finally tagged version 2.0.0!

Quite a few major changes from v1.x:

* New interfaces:
  * Vector
  * NI-CAN
  * isCAN
  * neoVI
* Simplified periodic send API with initial support for SocketCAN
* Protocols module including J1939 support removed
* Logger script moved to module `can.logger`
* New `can.player` script to replay log files
* BLF, ASC log file support added in new `can.io` module

You can install from [PyPi](https://pypi.python.org/pypi/python-can/2.0.0) with pip:

```
pip install python-can==2.0.0
```

The documentation for v2.0.0 is available at http://python-can.readthedocs.io/en/2.0.0/
