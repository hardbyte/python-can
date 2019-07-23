"""Types for mypy type-checking
"""
import typing

CanFilter = typing.Dict[str, typing.Union[bool, int, str]]
CanFilters = typing.Iterable[CanFilter]
