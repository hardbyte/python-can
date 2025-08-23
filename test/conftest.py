import pytest

from can.interfaces import virtual


@pytest.fixture(autouse=True)
def check_unclosed_virtual_channel():
    """
    Pytest fixture for detecting leaked virtual CAN channels.

    - The fixture yields control to the test.
    - After the test completes, it acquires `virtual.channels_lock` and asserts
    that `virtual.channels` is empty.
    - If a test leaves behind any unclosed virtual CAN channels, the assertion
    will fail, surfacing resource leaks early.

    This helps maintain test isolation and prevents subtle bugs caused by
    leftover state between tests.
    """

    yield

    with virtual.channels_lock:
        assert len(virtual.channels) == 0
