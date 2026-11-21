#!/usr/bin/env python

"""
This module contains various configuration for the tests.

Some tests are skipped when run on a CI server because they are not
reproducible, see for example #243 and #940.
"""

import platform
import socket
import struct
from os import environ as environment


def env(name: str) -> bool:
    return environment.get(name, "").lower() in ("yes", "true", "t", "1")


# ############################## Continuous integration

# see here for the environment variables that are set on the CI servers:
#   - https://docs.travis-ci.com/user/environment-variables/
#   - https://docs.github.com/en/actions/reference/environment-variables#default-environment-variables

IS_TRAVIS = env("TRAVIS")
IS_GITHUB_ACTIONS = env("GITHUB_ACTIONS")

IS_CI = IS_TRAVIS or IS_GITHUB_ACTIONS or env("CI") or env("CONTINUOUS_INTEGRATION")

if IS_TRAVIS and IS_GITHUB_ACTIONS:
    raise OSError(
        f"only one of IS_TRAVIS ({IS_TRAVIS}) and IS_GITHUB_ACTIONS ({IS_GITHUB_ACTIONS}) may be True at the "
        "same time"
    )


# ############################## Platforms

_sys = platform.system().lower()
IS_WINDOWS = "windows" in _sys or ("win" in _sys and "darwin" not in _sys)
IS_LINUX = "linux" in _sys
IS_OSX = "darwin" in _sys
IS_UNIX = IS_LINUX or IS_OSX
del _sys

if (IS_WINDOWS and IS_LINUX) or (IS_LINUX and IS_OSX) or (IS_WINDOWS and IS_OSX):
    raise OSError(
        f"only one of IS_WINDOWS ({IS_WINDOWS}), IS_LINUX ({IS_LINUX}) and IS_OSX ({IS_OSX}) "
        f'can be True at the same time (platform.system() == "{platform.system()}")'
    )


# ############################## Implementations

IS_PYPY = platform.python_implementation() == "PyPy"


# ############################## What tests to run

TEST_CAN_FD = True

TEST_INTERFACE_SOCKETCAN = IS_LINUX and env("TEST_SOCKETCAN")


def _can_use_multicast(group: str) -> bool:
    """Check whether the host can send a datagram to the multicast ``group`` and receive it back.

    This mirrors what :class:`~can.interfaces.udp_multicast.UdpMulticastBus` does: join the group
    on an interface chosen by the kernel and rely on multicast loopback. It fails, for example, in
    containers without an IPv6 multicast route or on hosts whose firewall drops incoming multicast.
    """
    is_ipv6 = ":" in group
    family = socket.AF_INET6 if is_ipv6 else socket.AF_INET
    probe = b"python-can multicast probe"
    try:
        with socket.socket(family, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0.5)
            sock.bind(("", 0))
            port = sock.getsockname()[1]
            if is_ipv6:
                # interface index 0 lets the kernel choose the interface by route lookup
                request = socket.inet_pton(family, group) + struct.pack("@I", 0)
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, request)
            else:
                request = socket.inet_aton(group) + struct.pack("@I", socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, request)
            sock.sendto(probe, (group, port))
            return sock.recv(len(probe)) == probe
    except OSError:  # includes the timeout
        return False


# UDP multicast doesn't work on macOS CI, not even for loopback addresses.
# The probe groups are arbitrary: the kernel picks the interface by a route lookup for the whole
# multicast range, so every group of the same family and scope gives the same result.
TEST_UDP_MULTICAST_IPv4 = not (IS_CI and IS_OSX) and _can_use_multicast("239.255.0.1")
TEST_UDP_MULTICAST_IPv6 = not (IS_CI and IS_OSX) and _can_use_multicast("ff11::1")
