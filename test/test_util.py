import unittest
import warnings

import pytest

from can.util import _rename_kwargs, create_filter


class RenameKwargsTest(unittest.TestCase):
    expected_kwargs = dict(a=1, b=2, c=3, d=4)

    def _test(self, kwargs, aliases):

        # Test that we do get the DeprecationWarning when called with deprecated kwargs
        with self.assertWarnsRegex(DeprecationWarning, "is deprecated"):
            _rename_kwargs("unit_test", kwargs, aliases)

        # Test that the aliases contains the deprecated values and
        # the obsolete kwargs have been removed
        assert kwargs == self.expected_kwargs

        # Test that we do not get a DeprecationWarning when we call
        # without deprecated kwargs

        # Cause all warnings to always be triggered.
        warnings.simplefilter("error", DeprecationWarning)
        try:
            _rename_kwargs("unit_test", kwargs, aliases)
        finally:
            warnings.resetwarnings()

    def test_rename(self):
        kwargs = dict(old_a=1, old_b=2, c=3, d=4)
        aliases = {"old_a": "a", "old_b": "b"}
        self._test(kwargs, aliases)

    def test_obsolete(self):
        kwargs = dict(a=1, b=2, c=3, d=4, z=10)
        aliases = {"z": None}
        self._test(kwargs, aliases)

    def test_rename_and_obsolete(self):
        kwargs = dict(old_a=1, old_b=2, c=3, d=4, z=10)
        aliases = {"old_a": "a", "old_b": "b", "z": None}
        self._test(kwargs, aliases)

    def test_with_new_and_alias_present(self):
        kwargs = dict(old_a=1, a=1, b=2, c=3, d=4, z=10)
        aliases = {"old_a": "a", "old_b": "b", "z": None}
        with self.assertRaises(TypeError):
            self._test(kwargs, aliases)


def test_create_filter():
    # test exceptions
    with pytest.raises(ValueError):
        create_filter(
            accepted_std_ids=[-1],
            accepted_ext_ids=[100],
        )
    with pytest.raises(ValueError):
        create_filter(
            accepted_std_ids=[100],
            accepted_ext_ids=[-1],
        )
    with pytest.raises(ValueError):
        create_filter(
            accepted_std_ids=[0x7FF + 1],
            accepted_ext_ids=[100],
        )
    with pytest.raises(ValueError):
        create_filter(
            accepted_std_ids=[100],
            accepted_ext_ids=[0x1FFFFFFF + 1],
        )

    accepted_std_range = range(200, 205)
    accepted_ext_range = range(105_000, 105_005)

    can_filters = create_filter(
        accepted_std_ids=accepted_std_range,
        accepted_ext_ids=accepted_ext_range,
    )
    std_code = can_filters[0]["can_id"]
    std_mask = can_filters[0]["can_mask"]
    ext_code = can_filters[1]["can_id"]
    ext_mask = can_filters[1]["can_mask"]

    """
    Standard ID proof:
    b00011001000 | id:    200
    b00011001001 | id:    201
    b00011001010 | id:    202
    b00011001011 | id:    203
    b00011001100 | id:    204
    -------------------------
    b00011001000 | code:  200
    b11111111000 | mask: 2040
    """
    assert std_code == 200
    assert std_mask == 2040

    """
    Extended ID proof:
    b00000000000011001101000101000 | id:      105000
    b00000000000011001101000101001 | id:      105001
    b00000000000011001101000101010 | id:      105002
    b00000000000011001101000101011 | id:      105003
    b00000000000011001101000101100 | id:      105004
    -------------------------
    b00000000000011001101000101000 | code:    105000
    b11111111111111111111111111000 | mask: 536870904
    """
    assert ext_code == 105000
    assert ext_mask == 536870904

    # test that standard IDs in given range are accepted
    for can_id in accepted_std_range:
        assert 0 == (can_id ^ std_code) & std_mask

    # test that extended IDs in given range are accepted
    for can_id in accepted_ext_range:
        assert 0 == (can_id ^ ext_code) & ext_mask

    # test non-consecutive IDs
    can_filters = create_filter(
        accepted_std_ids=[333, 444],
        accepted_ext_ids=[33333, 44444],
    )
    std_code = can_filters[0]["can_id"]
    std_mask = can_filters[0]["can_mask"]
    ext_code = can_filters[1]["can_id"]
    ext_mask = can_filters[1]["can_mask"]

    """
    Standard ID proof (non-consecutive):
    b00101001101 | id:    333
    b00110111100 | id:    444
    -------------------------
    b00100001100 | code:  268
    b11100001110 | mask: 1806
    """
    assert std_code == 268
    assert std_mask == 1806

    """
    Extended ID proof (non-consecutive):
    b00000000000001000001000110101 | id:       33333
    b00000000000001010110110011100 | id:       44444
    -------------------------
    b00000000000001000000000010100 | code:     32788
    b11111111111111101000001010110 | mask: 536858710
    """
    assert ext_code == 32788
    assert ext_mask == 536858710

    # test that standard IDs in given sequence are accepted
    for can_id in [333, 444]:
        assert 0 == (can_id ^ std_code) & std_mask

    # test that extended IDs in given sequence are accepted
    for can_id in [33333, 44444]:
        assert 0 == (can_id ^ ext_code) & ext_mask
