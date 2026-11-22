import gc
from unittest.mock import patch

import pytest

import can
from can.interfaces.virtual import VirtualBus


def test_bus_ignore_config():
    with patch.object(
        target=can.util, attribute="load_config", side_effect=can.util.load_config
    ):
        with can.Bus(interface="virtual", ignore_config=True):
            assert not can.util.load_config.called

        with can.Bus(interface="virtual"):
            assert can.util.load_config.called


class _KwargsOnlyBus(can.BusABC):
    """A plugin-style bus that passes everything on to BusABC."""

    instances = 0

    def __init__(self, channel, **kwargs):
        _KwargsOnlyBus.instances += 1
        super().__init__(channel, **kwargs)

    def send(self, msg, timeout=None):
        pass

    def _recv_internal(self, timeout):
        return None, False


def test_bus_listen_only_rejected_if_not_declared():
    """
    Test Scope:
        A bus class whose constructor only takes **kwargs.
    Preconditions:
        A bus class without a listen_only parameter is registered as interface
        "kwargs_only".
    Events:
        Create the bus with listen_only=True through can.Bus and directly, then
        with listen_only=False through can.Bus.
    Evaluate:
        listen_only=True raises CanInterfaceNotImplementedError both ways
        before the bus constructor runs; listen_only=False creates the bus.
    """
    with patch.dict(
        "can.interfaces.BACKENDS", {"kwargs_only": (__name__, "_KwargsOnlyBus")}
    ):
        _KwargsOnlyBus.instances = 0
        with pytest.raises(can.CanInterfaceNotImplementedError):
            can.Bus("ch", interface="kwargs_only", ignore_config=True, listen_only=True)
        with pytest.raises(can.CanInterfaceNotImplementedError):
            _KwargsOnlyBus("ch", listen_only=True)
        assert _KwargsOnlyBus.instances == 0

        with can.Bus("ch", interface="kwargs_only", ignore_config=True) as bus:
            assert not bus.listen_only
        assert _KwargsOnlyBus.instances == 1


class _ForwardingVirtualBus(VirtualBus):
    """A subclass that forwards all arguments to a listen-only capable bus."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def test_bus_listen_only_accepted_if_forwarded():
    """
    Test Scope:
        A bus subclass whose constructor forwards **kwargs to a base class
        that declares listen_only.
    Preconditions:
        A subclass of VirtualBus with an __init__(*args, **kwargs).
    Events:
        Create the subclass with listen_only=True and send a message.
    Evaluate:
        The bus is created in listen-only mode and send raises
        CanOperationError.
    """
    with _ForwardingVirtualBus("ch", listen_only=True) as bus:
        assert bus.listen_only
        with pytest.raises(can.CanOperationError):
            bus.send(can.Message())


class _PositionalOnlyBus(can.BusABC):
    """A plugin-style bus whose constructor takes neither listen_only nor **kwargs."""

    def __init__(self, channel):
        super().__init__(channel)

    def send(self, msg, timeout=None):
        pass

    def _recv_internal(self, timeout):
        return None, False


def test_bus_without_listen_only_or_kwargs():
    """
    Test Scope:
        can.Bus with an interface whose constructor accepts neither
        listen_only nor **kwargs.
    Preconditions:
        A bus class with signature __init__(self, channel) is registered as
        interface "positional_only".
    Events:
        Create the bus through can.Bus without listen_only and with
        listen_only=False.
    Evaluate:
        Both buses are created and are not in listen-only mode.
    """
    with patch.dict(
        "can.interfaces.BACKENDS",
        {"positional_only": (__name__, "_PositionalOnlyBus")},
    ):
        with can.Bus("ch", interface="positional_only", ignore_config=True) as bus:
            assert not bus.listen_only
        with can.Bus(
            "ch", interface="positional_only", ignore_config=True, listen_only=False
        ) as bus:
            assert not bus.listen_only


@patch.object(can.bus.BusABC, "shutdown")
def test_bus_attempts_self_cleanup(mock_shutdown):
    bus = can.Bus(interface="virtual")
    del bus
    gc.collect()
    mock_shutdown.assert_called()
