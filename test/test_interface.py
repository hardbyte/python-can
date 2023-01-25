import importlib
from unittest.mock import patch

import pytest

import can
from can.interfaces import BACKENDS


@pytest.fixture(params=(BACKENDS.keys()))
def constructor(request):
    mod, cls = BACKENDS[request.param]

    try:
        module = importlib.import_module(mod)
        constructor = getattr(module, cls)
    except:
        pytest.skip("Unable to load interface")

    return constructor


@pytest.fixture
def interface(constructor):
    class MockInterface(constructor):
        def __init__(self):
            pass

        def __del__(self):
            pass

    return MockInterface()


@patch.object(can.bus.BusABC, "shutdown")
def test_interface_calls_parent_shutdown(mock_shutdown, interface):
    try:
        interface.shutdown()
    except:
        pass
    finally:
        mock_shutdown.assert_called()
