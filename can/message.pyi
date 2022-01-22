from typing import Optional, Any

class Message:
    timestamp: float
    arbitration_id: int
    is_extended_id: bool
    is_remote_frame: bool
    is_error_frame: bool
    channel: str
    is_fd: bool
    is_rx: bool
    bitrate_switch: bool
    error_state_indicator: bool
    data: bytearray
    dlc: int
    def __init__(self,
                 timestamp: float = ...,
                 arbitration_id: int = ...,
                 is_extended_id: bool = ...,
                 is_remote_frame: bool = ...,
                 is_error_frame: bool = ...,
                 channel: Optional[str] = ...,
                 dlc: int = ...,
                 data: Optional[bytearray] = ...,
                 is_fd: bool = ...,
                 is_rx: bool = ...,
                 bitrate_switch: bool = ...,
                 error_state_indicator: bool = ...,
                 check: bool = ...) -> None: ...
    def __str__(self) -> str: ...
    def __len__(self) -> int: ...
    def __bool__(self) -> bool: ...
    def __repr__(self) -> str: ...
    def __format__(self, format_spec: Optional[str]) -> str: ...
    def __bytes__(self) -> bytes: ...
    def __copy__(self) -> Message: ...
    def __deepcopy__(self, memo: Any) -> Message: ...
    def _check(self) -> None: ...
    def equals(self,
               other: Message,
               timestamp_delta: Optional[float | int]) -> bool: ...
