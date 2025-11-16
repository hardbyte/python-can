from contextlib import nullcontext
from threading import RLock
from typing import TYPE_CHECKING, Any, cast

from . import typechecking
from .bus import BusState, CanProtocol
from .interface import Bus
from .message import Message

if TYPE_CHECKING:
    from .bus import BusABC

try:
    # Only raise an exception on instantiation but allow module
    # to be imported
    from wrapt import ObjectProxy

    import_exc = None
except ImportError as exc:
    ObjectProxy = None  # type: ignore[misc,assignment]
    import_exc = exc


class ThreadSafeBus(
    ObjectProxy
):  # pylint: disable=abstract-method  # type: ignore[assignment]
    """
    Contains a thread safe :class:`can.BusABC` implementation that
    wraps around an existing interface instance. All public methods
    of that base class are now safe to be called from multiple threads.
    The send and receive methods are synchronized separately.

    Use this as a drop-in replacement for :class:`~can.BusABC`.

    .. note::

        This approach assumes that both :meth:`~can.BusABC.send` and
        :meth:`~can.BusABC._recv_internal` of the underlying bus instance can be
        called simultaneously, and that the methods use :meth:`~can.BusABC._recv_internal`
        instead of :meth:`~can.BusABC.recv` directly.
    """

    def __init__(
        self,
        channel: typechecking.Channel | None = None,
        interface: str | None = None,
        config_context: str | None = None,
        ignore_config: bool = False,
        **kwargs: Any,
    ) -> None:
        if import_exc is not None:
            raise import_exc

        super().__init__(
            Bus(
                channel=channel,
                interface=interface,
                config_context=config_context,
                ignore_config=ignore_config,
                **kwargs,
            )
        )

        # store wrapped bus as a proxy-local attribute. Name it with the
        # `_self_` prefix so wrapt won't forward it onto the wrapped object.
        self._self_wrapped = cast(
            "BusABC", object.__getattribute__(self, "__wrapped__")
        )

        # now, BusABC.send_periodic() does not need a lock anymore, but the
        # implementation still requires a context manager
        self._self_wrapped._lock_send_periodic = nullcontext()  # type: ignore[assignment]

        # init locks for sending and receiving separately
        self._self_lock_send = RLock()
        self._self_lock_recv = RLock()

    def recv(self, timeout: float | None = None) -> Message | None:
        with self._self_lock_recv:
            return self._self_wrapped.recv(timeout=timeout)

    def send(self, msg: Message, timeout: float | None = None) -> None:
        with self._self_lock_send:
            return self._self_wrapped.send(msg=msg, timeout=timeout)

    @property
    def filters(self) -> typechecking.CanFilters | None:
        with self._self_lock_recv:
            return self._self_wrapped.filters

    @filters.setter
    def filters(self, filters: typechecking.CanFilters | None) -> None:
        with self._self_lock_recv:
            self._self_wrapped.filters = filters

    def set_filters(self, filters: typechecking.CanFilters | None = None) -> None:
        with self._self_lock_recv:
            return self._self_wrapped.set_filters(filters=filters)

    def flush_tx_buffer(self) -> None:
        with self._self_lock_send:
            return self._self_wrapped.flush_tx_buffer()

    def shutdown(self) -> None:
        with self._self_lock_send, self._self_lock_recv:
            return self._self_wrapped.shutdown()

    @property
    def state(self) -> BusState:
        with self._self_lock_send, self._self_lock_recv:
            return self._self_wrapped.state

    @state.setter
    def state(self, new_state: BusState) -> None:
        with self._self_lock_send, self._self_lock_recv:
            self._self_wrapped.state = new_state

    @property
    def protocol(self) -> CanProtocol:
        with self._self_lock_send, self._self_lock_recv:
            return self._self_wrapped.protocol
