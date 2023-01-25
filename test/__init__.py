#!/usr/bin/env python

import pytest

# Ignore exceptions being raised as a result of BusABC.__del__
pytestmark = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnraisableExceptionWarning"
)
