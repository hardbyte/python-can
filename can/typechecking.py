"""Types for mypy type-checking
"""
import gzip
import typing

if typing.TYPE_CHECKING:
    import os

import typing_extensions

CanFilter: typing_extensions = typing_extensions.TypedDict(
    "CanFilter", {"can_id": int, "can_mask": int}
)
CanFilterExtended = typing_extensions.TypedDict(
    "CanFilterExtended", {"can_id": int, "can_mask": int, "extended": bool}
)
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

AutoDetectedConfig = typing_extensions.TypedDict(
    "AutoDetectedConfig", {"interface": str, "channel": Channel}
)

ReadableBytesLike = typing.Union[bytes, bytearray, memoryview]
