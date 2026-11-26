"""Discover IO plugins once without changing the selected log implementations."""

from unittest.mock import Mock, patch

import pytest

import can
from can.io import logger, player


@pytest.mark.parametrize(
    "module,factory,updater,registry,implementation,group",
    [
        (
            logger,
            can.Logger,
            "_update_writer_plugins",
            "MESSAGE_WRITERS",
            can.ASCWriter,
            "can.io.message_writer",
        ),
        (
            player,
            can.LogReader,
            "_update_reader_plugins",
            "MESSAGE_READERS",
            can.ASCReader,
            "can.io.message_reader",
        ),
    ],
)
@pytest.mark.parametrize("with_plugin", [False, True])
def test_discover_plugins_once(
    tmp_path, module, factory, updater, registry, implementation, group, with_plugin
):
    update = getattr(module, updater)
    if hasattr(update, "cache_clear"):
        update.cache_clear()
    plugin = Mock(key=".custom", load=Mock(return_value=implementation))
    entries = [plugin] if with_plugin else []
    filename = tmp_path / ("record.custom" if with_plugin else "record.asc")
    filename.touch()
    try:
        with (
            patch.dict(getattr(module, registry)),
            patch.object(module, "read_entry_points", return_value=entries) as discover,
        ):
            for _ in range(3):
                handler = factory(filename)
                assert isinstance(handler, implementation)
                handler.stop()
            discover.assert_called_once_with(group)
            if with_plugin:
                plugin.load.assert_called_once_with()
    finally:
        if hasattr(update, "cache_clear"):
            update.cache_clear()
