"""Types for mypy type-checking
"""

import gzip
import struct
import sys
import typing

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias


if typing.TYPE_CHECKING:
    import os


class CanFilter(typing.TypedDict):
    """
    CAN filter configuration.

    :param can_id: CAN ID to filter.
    :param can_mask: CAN mask to apply.
    """
    can_id: int
    can_mask: int


class CanFilterExtended(typing.TypedDict):
    """
    Extended CAN filter configuration.

    :param can_id: CAN ID to filter.
    :param can_mask: CAN mask to apply.
    :param extended: Indicates if filter is for extended CAN.
    """
    can_id: int
    can_mask: int
    extended: bool


CanFilters = typing.Sequence[typing.Union[CanFilter, CanFilterExtended]]

# TODO: Once buffer protocol support lands in typing, we should switch to that,
# since can.message.Message attempts to call bytearray() on the given data, so
# this should have the same typing info.
#
# See: https://github.com/python/typing/issues/593
CanData = typing.Union[bytes, bytearray, int, typing.Iterable[int]]

# Used for the Abstract Base Class
ChannelStr = str
ChannelInt = int
Channel = typing.Union[ChannelInt, ChannelStr]

# Used by the IO module
FileLike = typing.Union[typing.TextIO, typing.BinaryIO, gzip.GzipFile]
StringPathLike = typing.Union[str, "os.PathLike[str]"]
AcceptedIOType = typing.Union[FileLike, StringPathLike]

BusConfig = typing.NewType("BusConfig", typing.Dict[str, typing.Any])

# Used by CLI scripts
TAdditionalCliArgs: TypeAlias = typing.Dict[str, typing.Union[str, int, float, bool]]
TDataStructs: TypeAlias = typing.Dict[
    typing.Union[int, typing.Tuple[int, ...]],
    typing.Union[struct.Struct, typing.Tuple, None],
]


class AutoDetectedConfig(typing.TypedDict):
    """
    Auto-detected CAN interface configuration.

    :param interface: Name of CAN interface.
    : param channel: Channel on CAN interface.
    """
    interface: str
    channel: Channel


ReadableBytesLike = typing.Union[bytes, bytearray, memoryview]


class BitTimingDict(typing.TypedDict):
    """
    Bit timing CAN configuration.

    :param f_clock: Frequency of CAN controller clock.
    :param brp: Baud rate prescaler.
    :param tseg1: Time segment 1.
    :param tseg2: Time segment 2.
    :param sjw: Synchronization jump width.
    :param nof_samples: Number of samples.
    """
    f_clock: int
    brp: int
    tseg1: int
    tseg2: int
    sjw: int
    nof_samples: int


class BitTimingFdDict(typing.TypedDict):
    """
    Bit timing CAN FD configuration.

    :param f_clock: Frequency of CAN controller clock.
    :param brp: Baud rate prescaler.
    :param nom_tseg1: Nominal time segment 1.
    :param nom_tseg2: Nominal time segment 2.
    :param nom_sjw: Nominal synchronization jump width.
    :param data_brp: Data phase baud rate prescaler.
    :param data_tseg1: Data time segment 1.
    :param data_tseg2: Data time segment 2.
    :param data_sjw: Data synchronization jump width.
    """
    f_clock: int
    nom_brp: int
    nom_tseg1: int
    nom_tseg2: int
    nom_sjw: int
    data_brp: int
    data_tseg1: int
    data_tseg2: int
    data_sjw: int
