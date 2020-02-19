"""Types for mypy type-checking
"""

import typing

if typing.TYPE_CHECKING:
    import os

import mypy_extensions

CanFilter = mypy_extensions.TypedDict("CanFilter", {"can_id": int, "can_mask": int})
CanFilterExtended = mypy_extensions.TypedDict(
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
Channel = typing.Union[int, str]

# Used by the IO module
FileLike = typing.IO[typing.Any]
StringPathLike = typing.Union[str, "os.PathLike[str]"]
AcceptedIOType = typing.Optional[typing.Union[FileLike, StringPathLike]]

BusConfig = typing.NewType("BusConfig", dict)

AutoDetectedConfig = mypy_extensions.TypedDict(
    "AutoDetectedConfig", {"interface": str, "channel": Channel}
)
