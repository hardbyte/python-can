import can_calc_bittiming


def test_baud100k():

    bt = can_calc_bittiming.bt()
    bt.bitrate = 100 * 1000
    btc = can_calc_bittiming.btc()
    bt = can_calc_bittiming.CAN_CALC_BITTIMING(bt, btc)
    assert bt.brp == 60
    assert bt.bitrate == 100000


def test_baud250k():

    bt = can_calc_bittiming.bt()
    bt.bitrate = 250 * 1000
    btc = can_calc_bittiming.btc()
    bt = can_calc_bittiming.CAN_CALC_BITTIMING(bt, btc)
    assert bt.brp == 36
    assert bt.bitrate == 250000


def test_baud1000k():

    bt = can_calc_bittiming.bt()
    bt.bitrate = 1000 * 1000
    btc = can_calc_bittiming.btc()
    bt = can_calc_bittiming.CAN_CALC_BITTIMING(bt, btc)
    assert bt.brp == 9
    assert bt.tq == 62
    assert bt.prop_seg == 5
    assert bt.phase_seg1 == 6
    assert bt.phase_seg2 == 4
    assert bt.bitrate == 1000 * 1000
