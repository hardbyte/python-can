Changelog
=========

.. towncrier-draft-entries::

.. towncrier release notes start

Version `v4.6.1 <https://github.com/hardbyte/python-can/tree/v4.6.1>`_ - 2025-08-12
-----------------------------------------------------------------------------------


Fixed
~~~~~

- Fix initialisation of an slcan bus, when setting a bitrate. When using CAN 2.0 (not FD), the default setting for ``data_bitrate`` was invalid, causing an exception. (:issue:`1978`)



Version `v4.6.0 <https://github.com/hardbyte/python-can/tree/v4.6.0>`_ - 2025-08-09
-----------------------------------------------------------------------------------


Removed
~~~~~~~

- Remove support for Python 3.8. (:issue:`1931`)
- Unknown command line arguments ("extra args") are no longer passed down to ``can.Bus()`` instantiation. Use the ``--bus-kwargs`` argument instead. (:issue:`1949`)
- Remove ``can.io.generic.BaseIOHandler`` class. Improve ``can.io.*`` type annotations by using ``typing.Generic``. (:issue:`1951`)


Added
~~~~~

- Support 11-bit identifiers in the ``serial`` interface. (:issue:`1758`)
- Keep track of active Notifiers and make Notifier usable as a context manager. Add function ``Notifier.find_instances(bus)`` to find the active Notifier for a given bus instance. (:issue:`1890`)
- Add Windows support to ``udp_multicast`` interface. (:issue:`1914`)
- Add FD support to ``slcan`` according to CANable 2.0 implementation. (:issue:`1920`)
- Add support for error messages to the ``socketcand`` interface. (:issue:`1941`)
- Add support for remote and error frames in the ``serial`` interface. (:issue:`1948`)
- Add public functions ``can.cli.add_bus_arguments`` and ``can.cli.create_bus_from_namespace`` for creating bus command line options. Currently downstream packages need to implement their own logic to configure *python-can* buses. Now *python-can* can create and parse bus options for third party packages. (:issue:`1949`)
- Add support for remote frames to ``TRCReader``. (:issue:`1953`)
- Mention the ``python-can-candle`` package in the plugin interface section of the documentation. (:issue:`1954`)
- Add new CLI tool ``python -m can.bridge`` (or just ``can_bridge``) to create a software bridge between two physical buses. (:issue:`1961`)


Changed
~~~~~~~

- Allow sending Classic CAN frames with a DLC value larger than 8 using the ``socketcan`` interface. (:issue:`1851`)
- The ``gs_usb`` extra dependency was renamed to ``gs-usb``.
  The ``lint`` extra dependency was removed and replaced with new PEP 735 dependency groups ``lint``, ``docs`` and ``test``. (:issue:`1945`)
- Update dependency name from ``zlgcan-driver-py`` to ``zlgcan``. (:issue:`1946`)
- Use ThreadPoolExecutor in ``detect_available_configs()`` to reduce runtime and add ``timeout`` parameter. (:issue:`1947`)
- Update contribution guide. (:issue:`1960`)


Fixed
~~~~~

- Fix a bug in ``slcanBus.get_version()`` and ``slcanBus.get_serial_number()``: If any other data was received during the function call, then ``None`` was returned. (:issue:`1904`)
- Fix incorrect padding of CAN FD payload in ``BlfReader``. (:issue:`1906`)
- Set correct message direction for messages received with ``kvaser`` interface and ``receive_own_messages=True``. (:issue:`1908`)
- Fix timestamp rounding error in ``BlfWriter``. (:issue:`1921`)
- Fix timestamp rounding error in ``BlfReader``. (:issue:`1927`)
- Handle timer overflow message and build timestamp according to the epoch in the ``ixxat`` interface. (:issue:`1934`)
- Avoid unsupported ``ioctl`` function call to allow usage of the ``udp_multicast`` interface on MacOS. (:issue:`1940`)
- Fix configuration file parsing for the ``state`` bus parameter. (:issue:`1957`)
- Mf4Reader: support non-standard ``CAN_DataFrame.Dir`` values in mf4 files created by `ihedvall/mdflib <https://github.com/ihedvall/mdflib>`_. (:issue:`1967`)
- PcanBus: Set ``Message.channel`` attribute in ``PcanBus.recv()``. (:issue:`1969`)



Version `v4.5.0 <https://github.com/hardbyte/python-can/tree/v4.5.0>`_ - 2024-11-28
-----------------------------------------------------------------------------------

Features
~~~~~~~~

- gs_usb command-line support (and documentation updates and stability fixes) (:issue:`1790`)
- Faster and more general MF4 support (:issue:`1892`)
- ASCWriter speed improvement (:issue:`1856`)
- Faster Message string representation (:issue:`1858`)
- Added Netronic's CANdo and CANdoISO adapters interface (:issue:`1887`)
- Add autostart option to BusABC.send_periodic() to fix issue :issue:`1848` (:issue:`1853`)
- Improve TestBusConfig (:issue:`1804`)
- Improve speed of TRCReader (:issue:`1893`)


Bug Fixes
~~~~~~~~~

- Fix Kvaser timestamp (:issue:`1878`)
- Set end_time in ThreadBasedCyclicSendTask.start() (:issue:`1871`)
- Fix regex in _parse_additional_config() (:issue:`1868`)
- Fix for :issue:`1849` (PCAN fails when PCAN_ERROR_ILLDATA is read via ReadFD) (:issue:`1850`)
- Period must be >= 1ms for BCM using Win32 API (:issue:`1847`)
- Fix ASCReader Crash on "Start of Measurement" Line (:issue:`1811`)
- Resolve AttributeError within NicanError (:issue:`1806`)



Miscellaneous
~~~~~~~~~~~~~

- Fix CI (:issue:`1889`)
- Update msgpack dependency (:issue:`1875`)
- Add tox environment for doctest (:issue:`1870`)
- Use typing_extensions.TypedDict on python < 3.12 for pydantic support (:issue:`1845`)
- Replace PyPy3.8 with PyPy3.10 (:issue:`1838`)
- Fix slcan tests (:issue:`1834`)
- Test on Python 3.13 (:issue:`1833`)
- Stop notifier in examples (:issue:`1814`)
- Use setuptools_scm (:issue:`1810`)
- Added extra info for Kvaser dongles (:issue:`1797`)
- Socketcand: show actual response as well as expected in error (:issue:`1807`)
- Refactor CLI filter parsing, add tests (:issue:`1805`)
- Add zlgcan to docs (:issue:`1839`)



Version `v4.4.2 <https://github.com/hardbyte/python-can/tree/v4.4.2>`_ - 2024-06-23
-----------------------------------------------------------------------------------

Bug Fixes
~~~~~~~~~

- Remove ``abstractmethod`` decorator from ``Listener.stop()`` (:issue:`1770`, :issue:`1795`)
- Fix ``SizedRotatingLogger`` file suffix bug (:issue:`1792`, :issue:`1793`)
- gs_usb: Use ``BitTiming`` class internally to configure bitrate (:issue:`1747`, :issue:`1748`)
- pcan: Fix unpack error in ``PcanBus._detect_available_configs()`` (:issue:`1767`)
- socketcan: Improve error handling in ``SocketcanBus.__init__()`` (:issue:`1771`)
- socketcan: Do not log exception on non-linux platforms (:issue:`1800`)
- vector, kvaser: Activate channels after CAN filters were applied (:issue:`1413`, :issue:`1708`, :issue:`1796`)


Features
~~~~~~~~

- kvaser: Add support for non-ISO CAN FD (:issue:`1752`)
- neovi: Return timestamps relative to epoch (:issue:`1789`)
- slcan: Support CANdapter extended length arbitration ID (:issue:`1506`, :issue:`1528`)
- slcan: Add support for ``listen_only`` mode (:issue:`1496`)
- vector: Add support for ``listen_only`` mode (:issue:`1764`)



Version `v4.4.0 <https://github.com/hardbyte/python-can/tree/v4.4.0>`_ - 2024-06-08
-----------------------------------------------------------------------------------

Features
~~~~~~~~

- TRC 1.3 Support: Added support for .trc log files as generated by PCAN Explorer v5 and other tools, expanding compatibility with common log file formats (:issue:`1753`).
- ASCReader refactor: improved the ASCReader code (:issue:`1717`).
- SYSTEC Interface Enhancements: Added the ability to pass an explicit DLC value to the send() method when using the SYSTEC interface, enhancing flexibility for message definitions (:issue:`1756`).
- Socketcand Beacon Detection: Introduced a feature for detecting socketcand beacons, facilitating easier connection and configuration with socketcand servers (:issue:`1687`).
- PCAN Driver Echo Frames: Enabled echo frames in the PCAN driver when receive_own_messages is set, improving feedback for message transmissions (:issue:`1723`).
- CAN FD Bus Connection for VectorBus: Enabled connecting to CAN FD buses without specifying bus timings, simplifying the connection process for users (:issue:`1716`).
- Neousys Configs Detection: Updated the detection mechanism for available Neousys configurations, ensuring more accurate and comprehensive configuration discovery (:issue:`1744`).


Bug Fixes
~~~~~~~~~

- Send Periodic Messages: Fixed an issue where fixed-duration periodic messages were sent one extra time beyond their intended count (:issue:`1713`).
- Vector Interface on Windows 11: Addressed compatibility issues with the Vector interface on Windows 11, ensuring stable operation across the latest OS version (:issue:`1731`).
- ASCWriter Millisecond Handling: Corrected the handling of milliseconds in ASCWriter, ensuring accurate time representation in log files (:issue:`1734`).
- Various minor bug fixes: Addressed several minor bugs to improve overall stability and performance.


Miscellaneous
~~~~~~~~~~~~~

- Invert default value logic for BusABC._is_shutdown. (:issue:`1774`)
- Implemented various logging enhancements to provide more detailed and useful operational insights (:issue:`1703`).
- Updated CI to use OIDC for connecting GitHub Actions to PyPi, improving security and access control for CI workflows.
- Fix CI to work for MacOS (:issue:`1772`).
- The release also includes various other minor enhancements and bug fixes aimed at improving the reliability and performance of the software.



Version `v4.3.1 <https://github.com/hardbyte/python-can/tree/v4.3.1>`_ - 2023-12-12
-----------------------------------------------------------------------------------

Bug Fixes
~~~~~~~~~

- Fix socketcand erroneously discarding frames (:issue:`1700`)
- Fix initialization order in EtasBus (:issue:`1693`, :issue:`1704`)


Documentation
~~~~~~~~~~~~~

- Fix install instructions for neovi (:issue:`1694`, :issue:`1697`)



Version `v4.3.0 <https://github.com/hardbyte/python-can/tree/v4.3.0>`_ - 2023-11-17
-----------------------------------------------------------------------------------

Breaking Changes
~~~~~~~~~~~~~~~~

- Raise Minimum Python Version to 3.8 (:issue:`1597`)
- Do not stop notifier if exception was handled (:issue:`1645`)


Bug Fixes
~~~~~~~~~

- Vector: channel detection fails, if there is an active flexray channel  (:issue:`1634`)
- ixxat: Fix exception in 'state' property on bus coupling errors (:issue:`1647`)
- NeoVi: Fixed serial number range (:issue:`1650`)
- PCAN: Fix timestamp offset due to timezone (:issue:`1651`)
- Catch ``pywintypes.error`` in broadcast manager (:issue:`1659`)
- Fix BLFReader error for incomplete or truncated stream (:issue:`1662`)
- PCAN: remove Windows registry check to fix 32bit compatibility (:issue:`1672`)
- Vector: Skip the ``can_op_mode check`` if the device reports ``can_op_mode=0`` (:issue:`1678`)
- Vector: using the config from ``detect_available_configs`` might raise XL_ERR_INVALID_CHANNEL_MASK error (:issue:`1681`)


Features
~~~~~~~~


API
^^^

- Add ``modifier_callback`` parameter to ``BusABC.send_periodic`` for auto-modifying cyclic tasks (:issue:`703`)
- Add ``protocol`` property to BusABC to determine active CAN Protocol (:issue:`1532`)
- Change Bus constructor implementation and typing (:issue:`1557`)
- Add optional ``strict`` parameter to relax BitTiming & BitTimingFd Validation (:issue:`1618`)
- Add ``BitTiming.iterate_from_sample_point`` static methods (:issue:`1671`)


IO
^^

- Can Player compatibility with interfaces that use additional configuration (:issue:`1610`)


Interface Improvements
^^^^^^^^^^^^^^^^^^^^^^

- Kvaser: Add BitTiming/BitTimingFd support to KvaserBus (:issue:`1510`)
- Ixxat: Implement ``detect_available_configs`` for the Ixxat bus. (:issue:`1607`)
- NeoVi: Enable send and receive on network ID above 255 (:issue:`1627`)
- Vector: Send HighPriority Message to flush Tx buffer (:issue:`1636`)
- PCAN: Optimize send performance (:issue:`1640`)
- PCAN: Support version string of older PCAN basic API (:issue:`1644`)
- Kvaser: add parameter exclusive and ``override_exclusive`` (:issue:`1660`)
- socketcand: Add parameter ``tcp_tune`` to reduce latency (:issue:`1683`)


Miscellaneous
^^^^^^^^^^^^^

- Distinguish Text/Binary-IO for Reader/Writer classes. (:issue:`1585`)
- Convert setup.py to pyproject.toml (:issue:`1592`)
- activate ruff pycodestyle checks (:issue:`1602`)
- Update linter instructions in development.rst (:issue:`1603`)
- remove unnecessary script files (:issue:`1604`)
- BigEndian test fixes (:issue:`1625`)
- align ``ID:`` in can.Message string (:issue:`1635`)
- Use same configuration file as Linux on macOS (:issue:`1657`)
- We do not need to account for drift when we ``USE_WINDOWS_EVENTS`` (:issue:`1666`, :issue:`1679`)
- Update linters, activate more ruff rules (:issue:`1669`)
- Add Python 3.12 Support / Test Python 3.12 (:issue:`1673`)



Version `v4.2.2 <https://github.com/hardbyte/python-can/tree/v4.2.2>`_ - 2023-06-18
-----------------------------------------------------------------------------------

Bug Fixes
~~~~~~~~~

- Fix socketcan KeyError (:issue:`1598`, :issue:`1599`).
- Fix IXXAT not properly shutdown message (:issue:`1606`).
- Fix Mf4Reader and TRCReader incompatibility with extra CLI args (:issue:`1610`).
- Fix decoding error in Kvaser constructor for non-ASCII product name (:issue:`1613`). 



Version `v4.2.1 <https://github.com/hardbyte/python-can/tree/v4.2.1>`_ - 2023-05-15
-----------------------------------------------------------------------------------

Bug Fixes
~~~~~~~~~

- The ASCWriter now logs the correct channel for error frames (:issue:`1578`, :issue:`1583`).
- Fix PCAN library detection (:issue:`1579`, :issue:`1580`).
- On Windows, the first two periodic frames were sent without delay (:issue:`1590`).



Version `v4.2.0 <https://github.com/hardbyte/python-can/tree/v4.2.0>`_ - 2023-04-26
-----------------------------------------------------------------------------------

Breaking Changes
~~~~~~~~~~~~~~~~

- The ``can.BitTiming`` class was replaced with the new 
  ``can.BitTiming`` and ``can.BitTimingFd`` classes (:issue:`1468`, :issue:`1515`). 
  Early adopters of ``can.BitTiming`` will need to update their code. Check the 
  `documentation <https://python-can.readthedocs.io/en/v4.2.0/bit_timing.html>`_
  for more information. Currently, the following interfaces support the new classes:

  * canalystii (:issue:`1468`)
  * cantact (:issue:`1468`)
  * nixnet (:issue:`1520`)
  * pcan (:issue:`1514`)
  * vector (:issue:`1470`, :issue:`1516`)

  There are open pull requests for kvaser (:issue:`1510`), slcan (:issue:`1512`) and usb2can (:issue:`1511`). Testing
  and reviewing of these open PRs would be most appreciated.


Features
~~~~~~~~


IO
^^
- Add support for MF4 files (:issue:`1289`).
- Add support for version 2 TRC files and other TRC file enhancements (:issue:`1530`).


Type Annotations
^^^^^^^^^^^^^^^^
- Export symbols to satisfy type checkers (:issue:`1547`, :issue:`1551`, :issue:`1558`, :issue:`1568`).


Interface Improvements
^^^^^^^^^^^^^^^^^^^^^^
- Add ``__del__`` method to ``can.BusABC`` to automatically release resources (:issue:`1489`, :issue:`1564`).
- pcan: Update PCAN Basic to 4.6.2.753 (:issue:`1481`).
- pcan: Use select instead of polling on Linux (:issue:`1410`).
- socketcan: Use ip link JSON output in ``find_available_interfaces`` (:issue:`1478`).
- socketcan: Enable SocketCAN interface tests in GitHub CI (:issue:`1484`).
- slcan: improve receiving performance (:issue:`1490`).
- usb2can: Stop using root logger (:issue:`1483`).
- usb2can: Faster channel detection on Windows (:issue:`1480`).
- vector: Only check sample point instead of tseg & sjw (:issue:`1486`).
- vector: add VN5611 hwtype (:issue:`1501`).


Documentation
~~~~~~~~~~~~~

- Add new section about related tools to documentation. Add a list of
  plugin interface packages (:issue:`1457`).


Bug Fixes
~~~~~~~~~

- Automatic type conversion for config values (:issue:`1498`, :issue:`1499`).
- pcan: Fix ``Bus.__new__`` for CAN-FD interfaces (:issue:`1458`, :issue:`1460`).
- pcan: Fix Detection of Library on Windows on ARM (:issue:`1463`).
- socketcand: extended ID bug fixes (:issue:`1504`, :issue:`1508`).
- vector: improve robustness against unknown HardwareType values (:issue:`1500`, :issue:`1502`).


Deprecations
~~~~~~~~~~~~

- The ``bustype`` parameter of ``can.Bus`` is deprecated and will be 
  removed in version 5.0, use ``interface`` instead. (:issue:`1462`).
- The ``context`` parameter of ``can.Bus`` is deprecated and will be 
  removed in version 5.0, use ``config_context`` instead. (:issue:`1474`).
- The ``bit_timing`` parameter of ``CantactBus`` is deprecated and will be 
  removed in version 5.0, use ``timing`` instead. (:issue:`1468`).
- The ``bit_timing`` parameter of ``CANalystIIBus`` is deprecated and will be 
  removed in version 5.0, use ``timing`` instead. (:issue:`1468`).
- The ``brs`` and ``log_errors`` parameters of ``NiXNETcanBus`` are deprecated 
  and will be removed in version 5.0. (:issue:`1520`).


Miscellaneous
~~~~~~~~~~~~~

- Use high resolution timer on Windows to improve 
  timing precision for BroadcastManager (:issue:`1449`).
- Improve ThreadBasedCyclicSendTask timing (:issue:`1539`).
- Make code examples executable on Linux (:issue:`1452`).
- Fix CanFilter type annotation (:issue:`1456`).
- Fix ``The entry_points().get`` deprecation warning and improve
  type annotation of ``can.interfaces.BACKENDS`` (:issue:`1465`).
- Add ``ignore_config`` parameter to ``can.Bus`` (:issue:`1474`).
- Add deprecation period to utility function ``deprecated_args_alias`` (:issue:`1477`).
- Add ``ruff`` to the CI system (:issue:`1551`)


Version `v4.1.0 <https://github.com/hardbyte/python-can/tree/v4.1.0>`_ - 2022-11-24
-----------------------------------------------------------------------------------

Breaking Changes
~~~~~~~~~~~~~~~~

- ``windows-curses`` was moved to optional dependencies (:issue:`1395`). 
  Use ``pip install python-can[viewer]`` if you are using the ``can.viewer`` 
  script on Windows.
- The attributes of ``can.interfaces.vector.VectorChannelConfig`` were renamed 
  from camelCase to snake_case (:issue:`1422`).



Features
~~~~~~~~


IO
^^
- The canutils logger preserves message direction (:issue:`1244`) 
  and uses common interface names (e.g. can0) instead of just 
  channel numbers (:issue:`1271`).
- The ``can.logger`` script accepts the ``-a, --append`` option 
  to add new data to an existing log file (:issue:`1326`, :issue:`1327`, :issue:`1361`).
  Currently only the blf-, canutils- and csv-formats are supported.
- All CLI ``extra_args`` are passed to the bus, logger 
  and player initialisation (:issue:`1366`).
- Initial support for TRC files (:issue:`1217`)


Type Annotations
^^^^^^^^^^^^^^^^
- python-can now includes the ``py.typed`` marker to support type checking 
  according to PEP 561 (:issue:`1344`).


Interface Improvements
^^^^^^^^^^^^^^^^^^^^^^
- The gs_usb interface can be selected by device index instead 
  of USB bus/address. Loopback frames are now correctly marked 
  with the ``is_rx`` flag (:issue:`1270`).
- The PCAN interface can be selected by its device ID instead 
  of just the channel name (:issue:`1346`).
- The PCAN Bus implementation supports auto bus-off reset (:issue:`1345`).
- SocketCAN: Make ``find_available_interfaces()`` find slcanX interfaces (:issue:`1369`).
- Vector: Add xlGetReceiveQueueLevel, xlGenerateSyncPulse and 
  xlFlushReceiveQueue to xldriver (:issue:`1387`).
- Vector: Raise a CanInitializationError, if the CAN settings can not 
  be applied according to the arguments of ``VectorBus.__init__`` (:issue:`1426`).
- Ixxat bus now implements BusState api and detects errors (:issue:`1141`)


Bug Fixes
~~~~~~~~~

- Improve robustness of USB2CAN serial number detection (:issue:`1129`).
- Fix channel2int conversion (:issue:`1268`, :issue:`1269`).
- Fix BLF timestamp conversion (:issue:`1266`, :issue:`1273`).
- Fix timestamp handling in udp_multicast on macOS (:issue:`1275`, :issue:`1278`).
- Fix failure to initiate the Neousys DLL (:issue:`1281`).
- Fix AttributeError in IscanError (:issue:`1292`, :issue:`1293`).
- Add missing vector devices (:issue:`1296`).
- Fix error for DLC > 8 in ASCReader (:issue:`1299`, :issue:`1301`).
- Set default mode for FileIOMessageWriter to wt instead of rt (:issue:`1303`).
- Fix conversion for port number from config file (:issue:`1309`).
- Fix fileno error on Windows (:issue:`1312`, :issue:`1313`, :issue:`1333`).
- Remove redundant ``writer.stop()`` call that throws error (:issue:`1316`, :issue:`1317`).
- Detect and cast types of CLI ``extra_args`` (:issue:`1280`, :issue:`1328`).
- Fix ASC/CANoe incompatibility due to timestamp format (:issue:`1315`, :issue:`1362`).
- Fix MessageSync timings (:issue:`1372`, :issue:`1374`).
- Fix file name for compressed files in SizedRotatingLogger (:issue:`1382`, :issue:`1683`).
- Fix memory leak in neoVI bus where message_receipts grows with no limit (:issue:`1427`).
- Raise ValueError if gzip is used with incompatible log formats (:issue:`1429`).
- Allow restarting of transmission tasks for socketcan (:issue:`1440`)


Miscellaneous
~~~~~~~~~~~~~

- Allow ICSApiError to be pickled and un-pickled (:issue:`1341`)
- Sort interface names in CLI API to make documentation reproducible (:issue:`1342`)
- Exclude repository-configuration from git-archive (:issue:`1343`)
- Improve documentation (:issue:`1397`, :issue:`1401`, :issue:`1405`, :issue:`1420`, :issue:`1421`, :issue:`1434`)
- Officially support Python 3.11 (:issue:`1423`)
- Migrate code coverage reporting from Codecov to Coveralls (:issue:`1430`)
- Migrate building docs and publishing releases to PyPi from Travis-CI to GitHub Actions (:issue:`1433`)


Version `v4.0.0 <https://github.com/hardbyte/python-can/tree/4.0.0>`_ - 2022-02-19
----------------------------------------------------------------------------------

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
~~~~~~~~~~~~~~

- Type hints for the core library and some interfaces (:issue:`652` and many others)
- Support for Python 3.7-3.10+ only (dropped support for Python 2.* and 3.5-3.6) (:issue:`528` and many others)
- `Granular and unified exceptions <https://python-can.readthedocs.io/en/4.0.0/api.html#errors>`_ (:issue:`356`, :issue:`562`, :issue:`1025`; overview in :issue:`1046`)
- `Support for automatic configuration detection <https://python-can.readthedocs.io/en/4.0.0/api.html#can.detect_available_configs>`_ in most interfaces (:issue:`303`, :issue:`640`, :issue:`641`, :issue:`811`, :issue:`1077`, :issue:`1085`)
- Better alignment of interfaces and IO to common conventions and semantics


New interfaces
~~~~~~~~~~~~~~

- udp_multicast (:issue:`644`)
- robotell (:issue:`731`)
- cantact (:issue:`853`)
- gs_usb (:issue:`905`)
- nixnet (:issue:`968`, :issue:`1154`)
- neousys (:issue:`980`, :issue:`1076`)
- socketcand (:issue:`1140`)
- etas (:issue:`1144`)


Improved interfaces
~~~~~~~~~~~~~~~~~~~

- socketcan

  * Support for multiple Cyclic Messages in Tasks (:issue:`610`)
  * Socketcan crash when attempting to stop CyclicSendTask with same arbitration ID (:issue:`605`, :issue:`638`, :issue:`720`)
  * Relax restriction of arbitration ID uniqueness for CyclicSendTask (:issue:`721`, :issue:`785`, :issue:`930`)
  * Add nanosecond resolution time stamping to socketcan (:issue:`938`, :issue:`1015`)
  * Add support for changing the loopback flag (:issue:`960`)
  * Socketcan timestamps are missing sub-second precision (:issue:`1021`, :issue:`1029`)
  * Add parameter to ignore CAN error frames (:issue:`1128`)

- socketcan_ctypes

  * Removed and replaced by socketcan after deprecation period

- socketcan_native

  * Removed and replaced by socketcan after deprecation period

- vector

  * Add chip state API (:issue:`635`)
  * Add methods to handle non message events (:issue:`708`)
  * Implement XLbusParams (:issue:`718`)
  * Add support for VN8900 xlGetChannelTime function (:issue:`732`, :issue:`733`)
  * Add vector hardware config popup (:issue:`774`)
  * Fix Vector CANlib treatment of empty app name (:issue:`796`, :issue:`814`)
  * Make VectorError pickleable (:issue:`848`)
  * Add methods get_application_config(), set_application_config() and set_timer_rate() to VectorBus (:issue:`849`)
  * Interface arguments are now lowercase (:issue:`858`)
  * Fix errors using multiple Vector devices (:issue:`898`, :issue:`971`, :issue:`977`)
  * Add more interface information to channel config (:issue:`917`)
  * Improve timestamp accuracy on Windows (:issue:`934`, :issue:`936`)
  * Fix error with VN8900 (:issue:`1184`)
  * Add static typing (:issue:`1229`)

- PCAN

  * Do not incorrectly reset CANMsg.MSGTYPE on remote frame (:issue:`659`, :issue:`681`)
  * Add support for error frames (:issue:`711`)
  * Added keycheck for windows platform for better error message (:issue:`724`)
  * Added status_string method to return simple status strings (:issue:`725`)
  * Fix timestamp timezone offset (:issue:`777`, :issue:`778`)
  * Add `Cygwin <https://www.cygwin.com/>`_ support (:issue:`840`) 
  * Update PCAN basic Python file to February 7, 2020 (:issue:`929`)
  * Fix compatibility with the latest macOS SDK (:issue:`947`, :issue:`948`, :issue:`957`, :issue:`976`)
  * Allow numerical channel specifier (:issue:`981`, :issue:`982`)
  * macOS: Try to find libPCBUSB.dylib before loading it (:issue:`983`, :issue:`984`)
  * Disable command PCAN_ALLOW_ERROR_FRAMES on macOS (:issue:`985`)
  * Force english error messages (:issue:`986`, :issue:`993`, :issue:`994`)
  * Add set/get device number (:issue:`987`)
  * Timestamps are silently incorrect on Windows without uptime installed (:issue:`1053`, :issue:`1093`)
  * Implement check for minimum version of pcan library (:issue:`1065`, :issue:`1188`)
  * Handle case where uptime is imported successfully but returns None (:issue:`1102`, :issue:`1103`)

- slcan

  * Fix bitrate setting (:issue:`691`)
  * Fix fileno crash on Windows (:issue:`924`)

- ics_neovi

  * Filter out Tx error messages (:issue:`854`)
  * Adding support for send timeout (:issue:`855`)
  * Raising more precise API error when set bitrate fails (:issue:`865`)
  * Avoid flooding the logger with many errors when they are the same (:issue:`1125`)
  * Omit the transmit exception cause for brevity (:issue:`1086`)
  * Raise ValueError if message data is over max frame length (:issue:`1177`, :issue:`1181`)
  * Setting is_error_frame message property (:issue:`1189`)

- ixxat

  * Raise exception on busoff in recv() (:issue:`856`)
  * Add support for 666 kbit/s bitrate (:issue:`911`)
  * Add function to list hwids of available devices (:issue:`926`)
  * Add CAN FD support (:issue:`1119`)

- seeed

  * Fix fileno crash on Windows (:issue:`902`)

- kvaser

  * Improve timestamp accuracy on Windows (:issue:`934`, :issue:`936`)

- usb2can

  * Fix "Error 8" on Windows and provide better error messages (:issue:`989`)
  * Fix crash on initialization (:issue:`1248`, :issue:`1249`)
  * Pass flags instead of flags_t type upon initialization (:issue:`1252`)

- serial

  * Fix "TypeError: cannot unpack non-iterable NoneType" and more robust error handling (:issue:`1000`, :issue:`1010`)

- canalystii

  * Fix is_extended_id (:issue:`1006`)
  * Fix transmitting onto a busy bus (:issue:`1114`)
  * Replace binary library with python driver (:issue:`726`, :issue:`1127`)


Other API changes and improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- CAN FD frame support is pretty complete (:issue:`963`)

  * ASCWriter (:issue:`604`) and ASCReader (:issue:`741`)
  * Canutils reader and writer (:issue:`1042`)
  * Logger, viewer and player tools can handle CAN FD (:issue:`632`)
  * Many bugfixes and more testing coverage

- IO

  * `Log rotation <https://python-can.readthedocs.io/en/4.0.0/listeners.html#can.SizedRotatingLogger>`_ (:issue:`648`, :issue:`874`, :issue:`881`, :issue:`1147`)
  * Transparent (de)compression of `gzip <https://docs.python.org/3/library/gzip.html>`_ files for all formats (:issue:`1221`)
  * Add `plugin support to can.io Reader/Writer <https://python-can.readthedocs.io/en/4.0.0/listeners.html#listener>`_ (:issue:`783`)
  * ASCReader/Writer enhancements like increased robustness (:issue:`820`, :issue:`1223`, :issue:`1256`, :issue:`1257`)
  * Adding absolute timestamps to ASC reader (:issue:`761`)
  * Support other base number (radix) at ASCReader (:issue:`764`)
  * Add `logconvert script <https://python-can.readthedocs.io/en/4.0.0/scripts.html#can-logconvert>`_ (:issue:`1072`, :issue:`1194`)
  * Adding support for gzipped ASC logging file (.asc.gz) (:issue:`1138`)
  * Improve `IO class hierarchy <https://python-can.readthedocs.io/en/4.0.0/internal-api.html#module-can.io.generic>`_ (:issue:`1147`)

- An `overview over various "virtual" interfaces <https://python-can.readthedocs.io/en/4.0.0/interfaces/virtual.html#other-virtual-interfaces>`_ (:issue:`644`)
- Make ThreadBasedCyclicSendTask event based & improve timing accuracy (:issue:`656`)
- Ignore error frames in can.player by default, add --error-frames option (:issue:`690`)
- Add an error callback to ThreadBasedCyclicSendTask (:issue:`743`, :issue:`781`)
- Add direction to CAN messages (:issue:`773`, :issue:`779`, :issue:`780`, :issue:`852`, :issue:`966`)
- Notifier no longer raises handled exceptions in rx_thread (:issue:`775`, :issue:`789`) but does so if no listener handles them (:issue:`1039`, :issue:`1040`)
- Changes to serial device number decoding (:issue:`869`)
- Add a default fileno function to the BusABC (:issue:`877`)
- Disallow Messages to simultaneously be "FD" and "remote" (:issue:`1049`)
- Speed up interface plugin imports by avoiding pkg_resources (:issue:`1110`)
- Allowing for extra config arguments in can.logger (:issue:`1142`, :issue:`1170`)
- Add changed byte highlighting to viewer.py (:issue:`1159`)
- Change DLC to DL in ``Message.__str__()`` (:issue:`1212`)


Other Bugfixes
~~~~~~~~~~~~~~

- BLF PDU padding (:issue:`459`)
- stop_all_periodic_tasks skipping every other task (:issue:`634`, :issue:`637`, :issue:`645`)
- Preserve capitalization when reading config files (:issue:`702`, :issue:`1062`)
- ASCReader: Skip J1939Tp messages (:issue:`701`)
- Fix crash in Canutils Log Reader when parsing RTR frames (:issue:`713`)
- Various problems with the installation of the library
- ASCWriter: Fix date format to show correct day of month (:issue:`754`)
- Fixes that some BLF files can't be read ( :issue:`763`, :issue:`765`)
- Seek for start of object instead of calculating it (:issue:`786`, :issue:`803`, :issue:`806`)
- Only import winreg when on Windows (:issue:`800`, :issue:`802`)
- Find the correct Reader/Writer independently of the file extension case (:issue:`895`)
- RecursionError when unpickling message object (:issue:`804`, :issue:`885`, :issue:`904`)
- Move "filelock" to neovi dependencies (:issue:`943`)
- Bus() with "fd" parameter as type bool always resolved to fd-enabled configuration (:issue:`954`, :issue:`956`)
- Asyncio code hits error due to deprecated loop parameter (:issue:`1005`, :issue:`1013`)
- Catch time before 1970 in ASCReader (:issue:`1034`)
- Fix a bug where error handlers were not called correctly (:issue:`1116`)
- Improved user interface of viewer script (:issue:`1118`)
- Correct app_name argument in logger (:issue:`1151`)
- Calling stop_all_periodic_tasks() in BusABC.shutdown() and all interfaces call it on shutdown (:issue:`1174`)
- Timing configurations do not allow int (:issue:`1175`)
- Some smaller bugfixes are not listed here since the problems were never part of a proper release
- ASCReader & ASCWriter using DLC as data length (:issue:`1245`, :issue:`1246`)


Behind the scenes & Quality assurance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- We publish both source distributions (``sdist``) and binary wheels (``bdist_wheel``) (:issue:`1059`, :issue:`1071`)
- Many interfaces were partly rewritten to modernize the code or to better handle errors
- Performance improvements
- Dependencies have changed
- Derive type information in Sphinx docs directly from type hints (:issue:`654`)
- Better documentation in many, many places; This includes the examples, README and python-can developer resources
- Add issue templates (:issue:`1008`, :issue:`1017`, :issue:`1018`, :issue:`1178`)
- Many continuous integration (CI) discussions & improvements (for example: :issue:`951`, :issue:`940`, :issue:`1032`)

  * Use the `mypy <https://github.com/python/mypy>`_ static type checker (:issue:`598`, :issue:`651`)
  * Use `tox <https://tox.wiki/en/latest/>`_ for testing (:issue:`582`, :issue:`833`, :issue:`870`)
  * Use `Mergify <https://mergify.com/>`_ (:issue:`821`, :issue:`835`, :issue:`937`)
  * Switch between various CI providers, abandoned `AppVeyor <https://www.appveyor.com/>`_ (:issue:`1009`) and partly `Travis CI <https://travis-ci.org/>`_, ended up with mostly `GitHub Actions <https://docs.github.com/en/actions>`_ (:issue:`827`, :issue:`1224`)
  * Use the `black <https://black.readthedocs.io/en/stable/>`_ auto-formatter (:issue:`950`)
  * `Good test coverage <https://app.codecov.io/gh/hardbyte/python-can/branch/develop>`_ for all but the interfaces

- Testing: Many of the new features directly added tests, and coverage of existing code was improved too (for example: :issue:`1031`, :issue:`581`, :issue:`585`, :issue:`586`, :issue:`942`, :issue:`1196`, :issue:`1198`)


Version `v3.3.4 <https://github.com/hardbyte/python-can/tree/3.3.4>`_ - 2020-10-04
----------------------------------------------------------------------------------

Last call for Python2 support.

- :issue:`850` Fix socket.error is a deprecated alias of OSError used on Python versions lower than 3.3.


Version `v3.3.3 <https://github.com/hardbyte/python-can/tree/3.3.3>`_ - 2020-05-18
----------------------------------------------------------------------------------

- :issue:`798` Backport caching msg.data value in neovi interface.
- :issue:`796` Fix Vector CANlib treatment of empty app name.
- :issue:`771` Handle empty CSV file.
- :issue:`741` ASCII reader can now handle FD frames.
- :issue:`740` Exclude test packages from distribution.
- :issue:`713` RTR crash fix in canutils log reader parsing RTR frames.
- :issue:`701` Skip J1939 messages in ASC Reader.
- :issue:`690` Exposes a configuration option to allow the CAN message player to send error frames (and sets the default to not send error frames).
- :issue:`638` Fixes the semantics provided by periodic tasks in SocketCAN interface.
- :issue:`628` Avoid padding CAN_FD_MESSAGE_64 objects to 4 bytes.
- :issue:`617` Fixes the broken CANalyst-II interface.
- :issue:`605` Socketcan BCM status fix.


Version `v3.3.2 <https://github.com/hardbyte/python-can/tree/3.3.2>`_ - 2019-08-16
----------------------------------------------------------------------------------
Minor bug fix release addressing issue in PCAN RTR.


Version `v3.3.1 <https://github.com/hardbyte/python-can/tree/3.3.1>`_ - 2019-07-23
----------------------------------------------------------------------------------
Minor fix to setup.py to only require pytest-runner when necessary.


Version `v3.3.0 <https://github.com/hardbyte/python-can/tree/3.3.0>`_ - 2019-06-27
----------------------------------------------------------------------------------

- Adding CAN FD 64 frame support to blf reader
- Updates to installation instructions
- Clean up bits generator in PCAN interface :issue:`588`
- Minor fix to use latest tools when building wheels on travis.


Version `v3.2.1 <https://github.com/hardbyte/python-can/tree/3.2.1>`_ - 2019-06-25
----------------------------------------------------------------------------------

- CAN FD 64 frame support to blf reader
- Minor fix to use latest tools when building wheels on travis.
- Updates links in documentation.


Version `v3.2.0 <https://github.com/hardbyte/python-can/tree/3.2.0>`_ - 2019-05-16
----------------------------------------------------------------------------------

Major features
~~~~~~~~~~~~~~

- FD support added for Pcan by @bmeisels with input from
  @markuspi, @christiansandberg & @felixdivo in PR :issue:`537`
- This is the last version of python-can which will support Python 2.7
  and Python 3.5. Support has been removed for Python 3.4 in this
  release in PR :issue:`532`


Other notable changes
~~~~~~~~~~~~~~~~~~~~~

- :issue:`533` BusState is now an enum.
- :issue:`535` This release should automatically be published to PyPi by travis.
- :issue:`577` Travis-ci now uses stages.
- :issue:`548` A guide has been added for new io formats.
- :issue:`550` Finish moving from nose to pytest.
- :issue:`558` Fix installation on Windows.
- :issue:`561` Tests for MessageSync added.

General fixes, cleanup and docs changes can be found on the GitHub milestone
https://github.com/hardbyte/python-can/milestone/7?closed=1

Pulls: :issue:`522`, :issue:`526`, :issue:`527`, :issue:`536`, :issue:`540`, :issue:`546`, :issue:`547`, :issue:`548`, :issue:`533`, :issue:`559`, :issue:`569`, :issue:`571`, :issue:`572`, :issue:`575`


Backend Specific Changes
~~~~~~~~~~~~~~~~~~~~~~~~


pcan
^^^^

- FD


slcan
^^^^^

- ability to set custom can speed instead of using predefined speed values. :issue:`553`


socketcan
^^^^^^^^^

- Bug fix to properly support 32bit systems. :issue:`573`


usb2can
^^^^^^^

- slightly better error handling
- multiple serial devices can be found
- support for the ``_detect_available_configs()`` API

Pulls :issue:`511`, :issue:`535`


vector
^^^^^^

- handle ``app_name``. :issue:`525`


Version `v3.1.1 <https://github.com/hardbyte/python-can/tree/3.1.1>`_ - 2019-02-24
----------------------------------------------------------------------------------

Major features
~~~~~~~~~~~~~~

Two new interfaces this release:

- SYSTEC contributed by @idaniel86 in PR :issue:`466`
- CANalyst-II contributed by @smeng9 in PR :issue:`476`


Other notable changes
~~~~~~~~~~~~~~~~~~~~~

- :issue:`477` The kvaser interface now supports bus statistics via a custom bus method.
- :issue:`434` neovi now supports receiving own messages
- :issue:`490` Adding option to override the neovi library name
- :issue:`488` Allow simultaneous access to IXXAT cards
- :issue:`447` Improvements to serial interface:

  * to allow receiving partial messages
  * to fix issue with  DLC of remote frames
  * addition of unit tests

- :issue:`497` Small API changes to ``Message`` and added unit tests
- :issue:`471` Fix CAN FD issue in kvaser interface
- :issue:`462` Fix ``Notifier`` issue with asyncio
- :issue:`481` Fix PCAN support on OSX
- :issue:`455` Fix to ``Message`` initializer
- Small bugfixes and improvements


Version `v3.1.0 <https://github.com/hardbyte/python-can/tree/v3.1.0>`_ - 2023-03-01
-----------------------------------------------------------------------------------

Version 3.1.0 was built with old wheel and/or setuptools
packages and was replaced with v3.1.1 after an installation
but was discovered.


Version `v3.0.0 <https://github.com/hardbyte/python-can/tree/3.0.0>`_ - 2019-02-23
----------------------------------------------------------------------------------

Major features
~~~~~~~~~~~~~~

- Adds support for developing ``asyncio`` applications with ``python-can`` more easily. This can be useful
  when implementing protocols that handles simultaneous connections to many nodes since you can write
  synchronous looking code without handling multiple threads and locking mechanisms. :issue:`388`
- New can viewer terminal application. (``python -m can.viewer``) :issue:`390`
- More formally adds task management responsibility to the ``Bus``. By default tasks created with
  ``bus.send_periodic`` will have a reference held by the bus - this means in many cases the user
  doesn't need to keep the task in scope for their periodic messages to continue being sent. If
  this behavior isn't desired pass ``store_task=False`` to the ``send_periodic`` method. Stop all tasks
  by calling the bus's new ``stop_all_periodic_tasks`` method. :issue:`412`



Breaking changes
~~~~~~~~~~~~~~~~

- Interfaces should no longer override ``send_periodic`` and instead implement
  ``_send_periodic_internal`` to allow the Bus base class to manage tasks. :issue:`426`
- writing to closed writers is not supported any more (it was supported only for some)
- the file in the reader/writer is now always stored in the attribute uniformly called ``file``, and not in
  something like ``fp``, ``log_file`` or ``output_file``. Changed the name of the first parameter of the
  read/writer constructors from ``filename`` to ``file``.



Other notable changes
~~~~~~~~~~~~~~~~~~~~~

- can.Message class updated :issue:`413`

  - Addition of a ``Message.equals`` method.
  - Deprecate id_type in favor of is_extended_id
  - Initializer parameter extended_id deprecated in favor of is_extended_id
  - documentation, testing and example updates
  - Addition of support for various builtins: __repr__, __slots__, __copy__

- IO module updates to bring consistency to the different CAN message writers and readers. :issue:`348`

  - context manager support for all readers and writers
  - they share a common super class called ``BaseIOHandler``
  - all file handles can now be closed with the ``stop()`` method
  - the table name in ``SqliteReader``/``SqliteWriter`` can be adjusted
  - append mode added in ``CSVWriter`` and ``CanutilsLogWriter``
  - `file-like <https://docs.python.org/3/glossary.html#term-file-like-object>`_ and
    `path-like <https://docs.python.org/3/glossary.html#term-path-like-object>`_ objects can now be passed to
    the readers and writers (except to the Sqlite handlers)
  - add a ``__ne__()`` method to the ``Message`` class (this was required by the tests)
  - added a ``stop()`` method for ``BufferedReader``
  - ``SqliteWriter``: this now guarantees that all messages are being written, exposes some previously internal metrics
    and only buffers messages up to a certain limit before writing/committing to the database.
  - the unused ``header_line`` attribute from ``CSVReader`` has been removed
  - privatized some attributes that are only to be  used internally in the classes
  - the method ``Listener.on_message_received()`` is now abstract (using ``@abc.abstractmethod``)

- Start testing against Python 3.7 :issue:`380`
- All scripts have been moved into ``can/scripts``. :issue:`370`, :issue:`406`
- Added support for additional sections to the config :issue:`338`
- Code coverage reports added. :issue:`346`, :issue:`374`
- Bug fix to thread safe bus. :issue:`397`

General fixes, cleanup and docs changes: (:issue:`347`, :issue:`348`, :issue:`367`, :issue:`368`, :issue:`370`, :issue:`371`, :issue:`373`, :issue:`420`, :issue:`417`, :issue:`419`, :issue:`432`)


Backend Specific Changes
~~~~~~~~~~~~~~~~~~~~~~~~


3rd party interfaces
^^^^^^^^^^^^^^^^^^^^

- Deprecated ``python_can.interface`` entry point instead use ``can.interface``. :issue:`389`


neovi
^^^^^

- Added support for CAN-FD :issue:`408`
- Fix issues checking if bus is open. :issue:`381`
- Adding multiple channels support. :issue:`415`


nican
^^^^^

- implements reset instead of custom ``flush_tx_buffer``. :issue:`364`


pcan
^^^^

- now supported on OSX. :issue:`365`


serial
^^^^^^

- Removed TextIOWrapper from serial. :issue:`383`
- switch to ``serial_for_url`` enabling using remote ports via ``loop://``, ``socket://`` and ``rfc2217://`` URLs. :issue:`393`
- hardware handshake using ``rtscts`` kwarg :issue:`402`


socketcan
^^^^^^^^^

- socketcan tasks now reuse a bcm socket :issue:`404`, :issue:`425`, :issue:`426`,
- socketcan bugfix to receive error frames :issue:`384`


vector
^^^^^^

- Vector interface now implements ``_detect_available_configs``. :issue:`362`
- Added support to select device by serial number. :issue:`387`


Version `v2.2.1 <https://github.com/hardbyte/python-can/tree/2.2.1>`_ - 2018-07-12
----------------------------------------------------------------------------------

- Fix errors and warnings when importing library on Windows
- Fix Vector backend raising ValueError when hardware is not connected


Version `v2.2.0 <https://github.com/hardbyte/python-can/tree/2.2.0>`_ - 2018-07-03
----------------------------------------------------------------------------------

- Fallback message filtering implemented in Python for interfaces that don't offer better accelerated mechanism.
- SocketCAN interfaces have been merged (Now use ``socketcan`` instead of either ``socketcan_native`` and ``socketcan_ctypes``),
  this is now completely transparent for the library user.
- automatic detection of available configs/channels in supported interfaces.
- Added synchronized (thread-safe) Bus variant.
- context manager support for the Bus class.
- Dropped support for Python 3.3 (officially reached end-of-life in Sept. 2017)
- Deprecated the old ``CAN`` module, please use the newer ``can`` entry point (will be removed in an upcoming major version)


Version `v2.1.0 <https://github.com/hardbyte/python-can/tree/2.1.0>`_ - 2018-02-18
----------------------------------------------------------------------------------

- Support for out of tree can interfaces with pluggy.
- Initial support for CAN-FD for socketcan_native and kvaser interfaces.
- Neovi interface now uses Intrepid Control Systems's own interface library.
- Improvements and new documentation for SQL reader/writer.
- Fix bug in neovi serial number decoding.
- Add testing on OSX to TravisCI
- Fix non english decoding error on pcan
- Other misc improvements and bug fixes


Version `v2.0.0 <https://github.com/hardbyte/python-can/tree/2.0.0>`_ - 2018-01-05
----------------------------------------------------------------------------------

After an extended baking period we have finally tagged version 2.0.0!

Quite a few major changes from v1.x:

- New interfaces:

  * Vector
  * NI-CAN
  * isCAN
  * neoVI

- Simplified periodic send API with initial support for SocketCAN
- Protocols module including J1939 support removed
- Logger script moved to module ``can.logger``
- New ``can.player`` script to replay log files
- BLF, ASC log file support added in new ``can.io`` module

You can install from `PyPi <https://pypi.python.org/pypi/python-can/2.0.0>`_ with pip:

```
pip install python-can==2.0.0
```


Version `v1.5.2 <https://github.com/hardbyte/python-can/tree/1.5.2>`_ - 2016-09-10
----------------------------------------------------------------------------------


Version `v1.4.2 <https://github.com/hardbyte/python-can/tree/1.4.2>`_ - 2016-01-12
----------------------------------------------------------------------------------


Version `v1.0.0 <https://github.com/hardbyte/python-can/tree/1.0.0>`_ - 2010-11-18
----------------------------------------------------------------------------------


Version `v0.4.1 <https://github.com/hardbyte/python-can/tree/0.4.1>`_ - 2010-07-01
----------------------------------------------------------------------------------
