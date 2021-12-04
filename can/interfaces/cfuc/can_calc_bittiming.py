# from _typeshed import HasFileno
import math

INT_MAX = 2147483647
UINT_MAX = INT_MAX * 2 + 1

CAN_CALC_MAX_ERROR  = 50 # in one-tenth of a percent */
CAN_CALC_SYNC_SEG  = 1

class btc(object):
    tseg1_min = 1	# Time segement 1 = prop_seg + phase_seg1 */
    tseg1_max = 16
    tseg2_min = 1	# Time segement 2 = phase_seg2 */
    tseg2_max = 8
    sjw_max	 = 4	# Synchronisation jump width */
    brp_min	 = 1	# Bit-rate prescaler */
    brp_max = 64
    brp_inc = 1

class bt(object):
    bitrate = 0		# Bit-rate in bits/second */
    sample_point = 0	# Sample point in one-tenth of a percent */
    tq = 0		# Time quanta (TQ) in nanoseconds */
    prop_seg = 0		# Propagation segment in TQs */
    phase_seg1 = 0	# Phase buffer segment 1 in TQs */
    phase_seg2 = 0	# Phase buffer segment 2 in TQs */
    sjw = 0		# Synchronisation jump width in TQs */
    brp = 0		# Bit-rate prescaler */

def clamp(val, lo, hi):
    if (val < lo): val = lo
    if (val > hi): val = hi
    return val



def can_update_spt(btc, spt_nominal, tseg, tseg1_ptr, tseg2_ptr, spt_error_ptr):
    spt_error = 0
    best_spt_error = UINT_MAX
    spt = 0
    best_spt = 0
    tseg1 = 0
    tseg2 = 0
    i = 0

    while (i <= 1):
        
        tseg2 = tseg + CAN_CALC_SYNC_SEG -  math.floor((spt_nominal * (tseg + CAN_CALC_SYNC_SEG)) / 1000) - i
        tseg2 = clamp(tseg2, btc.tseg2_min, btc.tseg2_max)
        tseg1 = tseg - tseg2
        if (tseg1 > btc.tseg1_max):
            tseg1 = btc.tseg1_max
            tseg2 = tseg - tseg1
        spt = 1000 *  (tseg + CAN_CALC_SYNC_SEG - tseg2) / (tseg + CAN_CALC_SYNC_SEG)
        spt_error = abs(spt_nominal - spt)

        if ((spt <= spt_nominal) & (spt_error < best_spt_error)) :
            best_spt_ptr = spt
            best_spt_error = spt_error
            tseg1_ptr = tseg1
            tseg2_ptr = tseg2
        i = i + 1

    spt_error_ptr = best_spt_error

    return tseg1_ptr,tseg2_ptr,spt_error_ptr, best_spt_ptr



def CAN_CALC_BITTIMING(bt, btc):
    clock_freq = 144000000
    spt_nominal = 0
    best_tseg = 0	#' current best value for tseg */
    best_brp = 0	# current best value for brp */
    brp = 0 
    tsegall = 0 
    tseg = 0 
    tseg1 = 0
    tseg2 = 0
    rate_error = 0	# difference between current and nominal value */
    best_rate_error = UINT_MAX
    spt_error = 0	# difference between current and nominal value */
    best_spt_error = UINT_MAX

    if (bt.bitrate > 800000):
        spt_nominal = 750
    else: 
        if (bt.bitrate > 500000):
            spt_nominal = 800
        else:
            spt_nominal = 875

    # tseg even = round down, odd = round up 
    tsegall = 0
    tseg = (btc.tseg1_max + btc.tseg2_max) * 2 + 2
    while tseg >= (btc.tseg1_min + btc.tseg2_min) * 2:
        tseg = tseg - 1
        tsegall = math.floor(CAN_CALC_SYNC_SEG + tseg / 2)

        # Compute all possible tseg choices (tseg=tseg1+tseg2) 
        brp = math.floor(clock_freq / (tsegall * bt.bitrate) + tseg % 2)

        # choose brp step which is possible in system */
        brp = math.floor((brp / btc.brp_inc) * btc.brp_inc)
        if (brp < btc.brp_min) | (brp > btc.brp_max):
            continue

        rate = math.floor(clock_freq / (brp * tsegall))
        rate_error = abs(bt.bitrate - rate)

        # tseg brp biterror 
        if (rate_error > best_rate_error):
            continue
	    # reset sample point error if we have a better bitrate */
        if (rate_error < best_rate_error):
            best_spt_error = UINT_MAX

        tseg1,tseg2,spt_error, spt = can_update_spt(btc, spt_nominal, math.floor(tseg / 2), tseg1, tseg2, spt_error)
        if (spt_error > best_spt_error):
            continue

        best_spt_error = spt_error
        best_rate_error = rate_error
        best_tseg = tseg / 2
        best_brp = brp

        if ((rate_error == 0) & (spt_error == 0)):
            break

    if (best_rate_error != 0) :
        # Error in one-tenth of a percent */
        rate_error = (best_rate_error * 1000) / bt.bitrate
        if (rate_error > CAN_CALC_MAX_ERROR):
            return -33

    bt.sample_point = can_update_spt(btc, spt_nominal, best_tseg,tseg1, tseg2, 0)[3]
    v64 = best_brp * 1000 * 1000 * 1000
    #do_div(v64, clock_freq)
    v64 = v64 / clock_freq
    # eof do_div

    bt.tq = math.floor(v64)
    bt.prop_seg = math.floor(tseg1 / 2)
    bt.phase_seg1 = tseg1 - bt.prop_seg
    bt.phase_seg2 = tseg2

    if ((bt.sjw == 0) | (btc.sjw_max == 0)):
        bt.sjw = 1
    else:
        # bt->sjw is at least 1 -> sanitize upper bound to sjw_max */
        if (bt.sjw > btc.sjw_max):
            bt.sjw = btc.sjw_max
        # bt->sjw must not be higher than tseg2 */
        if (tseg2 < bt.sjw):
            bt.sjw = tseg2

    bt.brp = best_brp

    # real bit-rate */
    bt.bitrate = math.floor(clock_freq / (bt.brp * (CAN_CALC_SYNC_SEG + tseg1 + tseg2)))

    return bt







