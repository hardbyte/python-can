#!/usr/bin/env python

"""
"""
import pickle
import unittest
from can.interfaces.ics_neovi import ICSApiError


class ICSApiErrorTest(unittest.TestCase):
    def test_error_pickling(self):
        iae = ICSApiError(
            0xF00,
            "description_short",
            "description_long",
            severity=ICSApiError.ICS_SPY_ERR_CRITICAL,
            restart_needed=1,
        )
        pickled_iae = pickle.dumps(iae)
        un_pickled_iae = pickle.loads(pickled_iae)
        assert iae.__dict__ == un_pickled_iae.__dict__


if __name__ == "__main__":
    unittest.main()
