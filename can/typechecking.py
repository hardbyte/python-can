"""Types for mypy type-checking
"""
import typing

import mypy_extensions

CanFilter = mypy_extensions.TypedDict(
    "CanFilter", {"can_id": int, "can_mask": int, "extended": bool}
)
CanFilters = typing.Iterable[CanFilter]
