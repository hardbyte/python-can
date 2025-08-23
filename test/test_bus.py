import gc
from unittest.mock import patch

import can


def test_bus_ignore_config():
    with patch.object(
        target=can.util, attribute="load_config", side_effect=can.util.load_config
    ):
        with can.Bus(interface="virtual", ignore_config=True):
            assert not can.util.load_config.called

        with can.Bus(interface="virtual"):
            assert can.util.load_config.called


@patch.object(can.bus.BusABC, "shutdown")
def test_bus_attempts_self_cleanup(mock_shutdown):
    bus = can.Bus(interface="virtual")
    del bus
    gc.collect()
    mock_shutdown.assert_called()
