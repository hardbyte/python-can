from typing import Optional, Union

_UINT_MAX = 65535


def _clamp(val, lo, hi):
    return min(max(val, lo), hi)


def _do_div(n, base):
    res = n % base
    return res


def _get_cia_sample_point(bitrate):
    if bitrate > 800000:
        sampl_pt = 750
    elif bitrate > 500000:
        sampl_pt = 800
    else:
        sampl_pt = 875

    return sampl_pt
    

class _BT(object):
    """Internal use"""

    def __init__(
        self,
        bitrate,
        sample_point=0.0
    ):
        self.tq = 0
        self.prop_seg = 0
        self.phase_seg1 = 0
        self.phase_seg2 = 0
        self.sjw = 0
        self.brp = 0
        self.bitrate = bitrate
        self.sp = 0
        self.nbr = bitrate

        if sample_point:
            self.nsp = sample_point
        else:
            self.nsp = _get_cia_sample_point(bitrate)

    @property
    def nominal_bitrate(self):
        return self.nbr

    @property
    def nominal_sample_point(self):
        return self.nsp / 10.0

    @property
    def sample_point(self):
        return self.sp / 10.0

    @property
    def sample_point_error(self):
        spt_error = abs(self.nsp - self.sample_point)
        return 100.0 * spt_error / self.nsp

    @property
    def bitrate_error(self):
        rate_error = abs(self.nbr - self.bitrate)
        return 100.0 * rate_error / self.nbr


class TimingConst(object):
    """
    Constants class for calculating bit timings, advanced users 
    
    This class is mainly used internally but can be used 
    externally depending on the use case.
    """
    tseg1_min = 4
    tseg1_max = 16
    tseg2_min = 2
    tseg2_max = 8
    sjw_max = 4
    brp_min = 1
    brp_max = 64
    brp_inc = 1
    f_clock = 8000000


class BitTiming:
    """Representation of a bit timing configuration.

    The class can be constructed in various ways, depending on the information
    available or the capabilities of the interfaces that need to be supported.

    The preferred way is using bitrate, CAN clock frequency, TSEG1, TSEG2, SJW::

        can.BitTiming(bitrate=1000000, f_clock=8000000, tseg1=5, tseg2=1, sjw=1)

    If the clock frequency is unknown it may be omitted but some interfaces may
    require it.

    Alternatively the BRP can be given instead of bitrate and clock frequency but this
    will limit the number of supported interfaces.

    It is also possible specify BTR registers directly,
    but will not work for all interfaces::

        can.BitTiming(btr0=0x00, btr1=0x14)
    """

    sync_seg = 1
    can_calc_max_error = 50

    TimingConst = TimingConst

    def __init__(
        self,
        bitrate: Optional[int] = None,
        f_clock: Optional[int] = None,
        brp: Optional[int] = None,
        tseg1: Optional[int] = None,
        tseg2: Optional[int] = None,
        sjw: Optional[int] = None,
        nof_samples: int = 1,
        btr0: Optional[int] = None,
        btr1: Optional[int] = None,
        sample_point: Optional[Union[int, float]] = None
    ):
        """
        Calculates the timings needed for most interfaces

        >>>import can
        >>>from can.interfaces.canalystii import CANalystIIBus
        >>>btiming = can.BitTiming(500000, f_clock=8000000)
        >>>print(btiming)
        500000 bits/s, sample point: 93.75%, BRP: 1, TSEG1: 14, TSEG2: 1, SJW: 1, BTR: 000Dh
        >>>btiming = can.BitTiming(500000, f_clock=8000000, sample_point=87.5)
        >>>print(btiming)
        500000 bits/s, sample point: 87.50%, BRP: 1, TSEG1: 13, TSEG2: 2, SJW: 1, BTR: 001Ch
        >>>can_interface = CANalystIIBus(0, Timing0=btiming.btr0, Timing1=btiming.btr1)

        :param int bitrate:
            Bitrate in bits/s.
        :param int f_clock:
            The CAN system clock frequency in Hz.
            Usually the oscillator frequency divided by 2.
        :param int brp:
            Bit Rate Prescaler. Prefer to use bitrate and f_clock instead.
        :param int tseg1:
            Time segment 1, that is, the number of quanta from (but not including)
            the Sync Segment to the sampling point.
        :param int tseg2:
            Time segment 2, that is, the number of quanta from the sampling
            point to the end of the bit.
        :param int sjw:
            The Synchronization Jump Width. Decides the maximum number of time quanta
            that the controller can resynchronize every bit.
        :param int nof_samples:
            Either 1 or 3. Some CAN controllers can also sample each bit three times.
            In this case, the bit will be sampled three quanta in a row,
            with the last sample being taken in the edge between TSEG1 and TSEG2.
            Three samples should only be used for relatively slow baudrates.
        :param int btr0:
            The BTR0 register value used by many CAN controllers.
        :param int btr1:
            The BTR1 register value used by many CAN controllers.
        """

        self._bitrate = bitrate
        self._brp = brp
        self._sjw = sjw
        self._tseg1 = tseg1
        self._tseg2 = tseg2
        self._nof_samples = nof_samples
        self._f_clock = f_clock
        self._bt = None

        if btr0 is not None:
            self._brp = (btr0 & 0x3F) + 1
            self._sjw = (btr0 >> 6) + 1
        if btr1 is not None:
            self._tseg1 = (btr1 & 0xF) + 1
            self._tseg2 = ((btr1 >> 4) & 0x7) + 1
            self._nof_samples = 3 if btr1 & 0x80 else 1

        if nof_samples not in (1, 3):
            raise ValueError("nof_samples must be 1 or 3")

        self._sample_point = sample_point

    def __can_update_spt(
            self,
            timing_const,
            spt_nominal,
            tseg,
            tseg1_ptr,
            tseg2_ptr,
            spt_error_ptr
    ):
        best_spt_error = _UINT_MAX
        best_spt = 0
        i = 0

        while i <= 1:
            i += 1
            tseg2 = tseg + self.sync_seg - (spt_nominal * (tseg + self.sync_seg)) / 1000 - i
            tseg2 = _clamp(tseg2, timing_const.tseg2_min, timing_const.tseg2_max)
            tseg1 = tseg - tseg2
            if tseg1 > timing_const.tseg1_max:
                tseg1 = timing_const.tseg1_max
                tseg2 = tseg - tseg1

            spt = 1000 * (tseg + self.sync_seg - tseg2) / (tseg + self.sync_seg)
            spt_error = abs(spt_nominal - spt)

            if spt <= spt_nominal and spt_error < best_spt_error:
                best_spt = spt
                best_spt_error = spt_error
                tseg1_ptr = tseg1
                tseg2_ptr = tseg2

        if spt_error_ptr:
            spt_error_ptr = best_spt_error

        return best_spt, int(tseg1_ptr), int(tseg2_ptr), spt_error_ptr

    def __can_calc_bittiming(self, bt, timing_const):
        best_rate_error = _UINT_MAX
        spt_error = 0  # difference between current and nominal value */
        best_spt_error = _UINT_MAX
        best_tseg = 0  # current best value for tseg */
        best_brp = 0  # current best value for brp */
        tseg1 = 0
        tseg2 = 0

        #  tseg even = round down, odd = round up */
        tseg = (timing_const.tseg1_max + timing_const.tseg2_max) * 2 + 1

        while tseg >= (timing_const.tseg1_min + timing_const.tseg2_min) * 2:
            tseg -= 1
            tsegall = self.sync_seg + tseg / 2

            #  Compute all possible tseg choices (tseg=tseg1+tseg2) */
            brp = timing_const.f_clock / (tsegall * bt.nbr) + tseg % 2

            #  choose brp step which is possible in system */
            brp = (brp / timing_const.brp_inc) * timing_const.brp_inc
            if brp < timing_const.brp_min or brp > timing_const.brp_max:
                continue

            rate = timing_const.f_clock / (brp * tsegall)
            rate_error = abs(bt.nbr - rate)

            #  tseg brp biterror */
            if rate_error > best_rate_error:
                continue

            #  reset sample point error if we have a better bitrate */
            if rate_error < best_rate_error:
                best_spt_error = _UINT_MAX

            tseg1, tseg2, spt_error = self.__can_update_spt(
                timing_const,
                bt.nsp,
                tseg / 2,
                tseg1,
                tseg2,
                spt_error
            )[1:]

            if spt_error > best_spt_error:
                continue

            best_spt_error = spt_error
            best_rate_error = rate_error
            best_tseg = tseg / 2
            best_brp = brp

            if rate_error == 0 and spt_error == 0:
                break

        if best_rate_error:
            #  Error in one-tenth of a percent */
            rate_error = (best_rate_error * 1000) / bt.bitrate
            if rate_error > self.can_calc_max_error:
                return False

        #  real sample point */
        bt.sp = self.__can_update_spt(
            timing_const,
            bt.nsp,
            best_tseg,
            tseg1,
            tseg2,
            None
        )[0]

        v64 = best_brp * 1000 * 1000 * 1000
        v64 = _do_div(v64, timing_const.f_clock)
        bt.tq = int(v64)
        bt.prop_seg = int(tseg1 / 2)
        bt.phase_seg1 = tseg1 - bt.prop_seg
        bt.phase_seg2 = tseg2

        #  check for sjw user settings */
        if not bt.sjw or not timing_const.sjw_max:
            bt.sjw = 1
        else:
            #  bt->sjw is at least 1 -> sanitize upper bound to sjw_max */
            if bt.sjw > timing_const.sjw_max:
                bt.sjw = timing_const.sjw_max
            #  bt->sjw must not be higher than tseg2 */
            if tseg2 < bt.sjw:
                bt.sjw = int(tseg2)

        bt.brp = int(best_brp)

        #  real bit-rate */
        bt.bitrate = int(timing_const.f_clock / (bt.brp * (self.sync_seg + tseg1 + tseg2)))

        return True

    def calc_bit_timing(self, timing_const: TimingConst):
        """
        Calculate Bit Timings
        
        WARNING: this will overwrite and settings passed to the constructor of this class.
        
        Mainly used internally for calculating timings from a bitrate and optionally a sample point
        
        :param timing_const: subclass of :class: `can.BitTiming.TimingConst`
        :return: None
        
        :raises: ValueError if not able to calculate the timings
        """
        if self._bitrate is None:
            return
        
        if self._bt is not None:
            return True
                
        bitrate_nominal = self._bitrate
        spt_nominal = self._sample_point
        
        if spt_nominal is None:
            spt_nominal = 0
        
        bt = _BT(
            bitrate=bitrate_nominal,
            sample_point=spt_nominal
        )

        if not self.__can_calc_bittiming(bt, timing_const):
            return False

        if not bt.sample_point:
            return False

        self._bitrate = bt.bitrate
        self._sample_point = bt.sample_point

        self._tseg1 = bt.prop_seg + bt.phase_seg1
        self._tseg2 = bt.phase_seg2
        self._brp = bt.brp
        self._sjw = bt.sjw
        self._f_clock = timing_const.f_clock
        
        self._bt = bt

        return True

    @property
    def nbt(self) -> int:
        """Nominal Bit Time."""
        return self.sync_seg + self.tseg1 + self.tseg2

    @property
    def bitrate(self) -> Union[int, float]:
        """Bitrate in bits/s."""
        if self._bitrate:
            return self._bitrate
        if self._f_clock and self._brp:
            return self._f_clock / (self._brp * self.nbt)
        raise ValueError("bitrate must be specified")

    @property
    def brp(self) -> int:
        """Bit Rate Prescaler."""
        if self._brp:
            return self._brp
        if self._f_clock and self._bitrate:
            return round(self._f_clock / (self._bitrate * self.nbt))
        raise ValueError("Either bitrate and f_clock or brp must be specified")

    @property
    def sjw(self) -> int:
        """Synchronization Jump Width."""
        if not self._sjw:
            raise ValueError("sjw must be specified")
        return self._sjw

    @property
    def tseg1(self) -> int:
        """Time segment 1.

        The number of quanta from (but not including) the Sync Segment to the sampling point.
        """
        if self._tseg1 is None:
            raise ValueError("tseg1 must be specified")
        return self._tseg1

    @property
    def tseg2(self) -> int:
        """Time segment 2.

        The number of quanta from the sampling point to the end of the bit.
        """
        if self._tseg2 is None:
            raise ValueError("tseg2 must be specified")
        return self._tseg2

    @property
    def nof_samples(self) -> int:
        """Number of samples (1 or 3)."""
        if not self._nof_samples:
            raise ValueError("nof_samples must be specified")
        return self._nof_samples

    @property
    def f_clock(self) -> int:
        """The CAN system clock frequency in Hz.

        Usually the oscillator frequency divided by 2.
        """
        if not self._f_clock:
            raise ValueError("f_clock must be specified")
        return self._f_clock

    @property
    def sample_point(self) -> float:
        """Sample point in percent."""
        return 100.0 * (self.nbt - self.tseg2) / self.nbt

    @property
    def btr0(self) -> int:
        sjw = self.sjw
        brp = self.brp

        if self._bt is None:
            if brp < 1 or brp > 64:
                raise ValueError("brp must be 1 - 64")
            if sjw < 1 or sjw > 4:
                raise ValueError("sjw must be 1 - 4")

            btr0 = (sjw - 1) << 6 | brp - 1

        else:
            btr0 = (
                ((int(self._bt.brp) - 1) & 0x3f) |
                (((int(self._bt.sjw) - 1) & 0x3) << 6)
            )

        return btr0

    @property
    def btr1(self) -> int:
        sam = 1 if self.nof_samples == 3 else 0
        tseg1 = self.tseg1
        tseg2 = self.tseg2

        if self._bt is None:
            if tseg1 < 1 or tseg1 > 16:
                raise ValueError("tseg1 must be 1 - 16")
            if tseg2 < 1 or tseg2 > 8:
                raise ValueError("tseg2 must be 1 - 8")

            btr1 = sam << 7 | (tseg2 - 1) << 4 | tseg1 - 1
        else:
            btr1 = (
                ((int(self._bt.prop_seg) + int(self._bt.phase_seg1) - 1) & 0xf) |
                (((int(self._bt.phase_seg2) - 1) & 0x7) << 4)
            )

        return btr1

    @property
    def can_br(self):
        if self._bt is not None:
            br = (
                (int(self._bt.phase_seg2) - 1) |
                ((int(self._bt.phase_seg1) - 1) << 4) |
                ((int(self._bt.prop_seg) - 1) << 8) |
                ((int(self._bt.sjw) - 1) << 12) |
                ((int(self._bt.brp) - 1) << 16)
            )
            return br

    @property
    def can_ctrl(self):
        if self._bt is not None:
            ctrl = (
                ((int(self._bt.brp) - 1) << 24) |
                ((int(self._bt.sjw) - 1) << 22) |
                ((int(self._bt.phase_seg1) - 1) << 19) |
                ((int(self._bt.phase_seg2) - 1) << 16) |
                ((int(self._bt.prop_seg) - 1) << 0)
            )

            return ctrl

    @property
    def cnf1(self):
        if self._bt is not None:
            return ((int(self._bt.sjw) - 1) << 6) | (int(self._bt.brp) - 1)

    @property
    def cnf2(self):
        if self._bt is not None:
            return 0x80 | ((int(self._bt.phase_seg1) - 1) << 3) | (int(self._bt.prop_seg) - 1)

    @property
    def cnf3(self):
        if self._bt is not None:
            return int(self._bt.phase_seg2) - 1

    @property
    def canbtc(self):
        if self._bt is not None:
            can_btc = (int(self._bt.phase_seg2) - 1) & 0x7
            can_btc |= ((int(self._bt.phase_seg1) + int(self._bt.prop_seg) - 1) & 0xF) << 3
            can_btc |= ((int(self._bt.sjw) - 1) & 0x3) << 8
            can_btc |= ((int(self._bt.brp) - 1) & 0xFF) << 16

            return can_btc

    @property
    def cibcr(self):
        if self._bt is not None:
            def _bcr_tseg1(x):
                return (x & 0x0f) << 20

            def _bcr_bpr(x):
                return (x & 0x3ff) << 8

            def _bcr_sjw(x):
                return (x & 0x3) << 4

            def _bcr_tseg2(x):
                return x & 0x07

            bcr = (
                _bcr_tseg1(int(self._bt.phase_seg1) + int(self._bt.prop_seg) - 1) |
                _bcr_bpr(int(self._bt.brp) - 1) |
                _bcr_sjw(int(self._bt.sjw) - 1) |
                _bcr_tseg2(int(self._bt.phase_seg2) - 1)
            )
            return bcr << 8

    def __str__(self) -> str:
        segments = []
        try:
            segments.append(f"sample point: {self.sample_point:.2f}%")
        except ValueError:
            pass
        try:
            segments.append(f"BRP: {self.brp}")
        except ValueError:
            pass
        try:
            segments.append(f"TSEG1: {self.tseg1}")
        except ValueError:
            pass
        try:
            segments.append(f"TSEG2: {self.tseg2}")
        except ValueError:
            pass
        try:
            segments.append(f"SJW: {self.sjw}")
        except ValueError:
            pass
        try:
            segments.append(f"BTR: {self.btr0:02X}{self.btr1:02X}h")
        except ValueError:
            pass

        try:
            segments.insert(0, f"{self.bitrate} bits/s")
        except ValueError:
            pass

        return ", ".join(segments)

    def __repr__(self) -> str:
        kwargs = {}
        if self._f_clock:
            kwargs["f_clock"] = self._f_clock
        try:
            kwargs["brp"] = self.brp
        except ValueError:
            pass
        try:
            kwargs["tseg1"] = self.tseg1
        except ValueError:
            pass
        try:
            kwargs["tseg2"] = self.tseg2
        except ValueError:
            pass
        try:
            kwargs["sjw"] = self.sjw
        except ValueError:
            pass

        if self._bitrate:
            kwargs["bitrate"] = self._bitrate

        if self._nof_samples != 1:
            kwargs["nof_samples"] = self._nof_samples
        args = ", ".join(f"{key}={value}" for key, value in kwargs.items())
        return f"can.BitTiming({args})"


if __name__ == '__main__':
    class sja1000Const(TimingConst):
        tseg1_min = 1
        tseg1_max = 16
        tseg2_min = 1
        tseg2_max = 8
        sjw_max = 4
        brp_min = 1
        brp_max = 64
        brp_inc = 1
        f_clock = 8000000


    class mscanConst(TimingConst):
        tseg1_min = 4
        tseg1_max = 16
        tseg2_min = 2
        tseg2_max = 8
        sjw_max = 4
        brp_min = 1
        brp_max = 64
        brp_inc = 1


    class mscan_32Const(mscanConst):
        f_clock = 32000000


    class mscan_33Const(mscanConst):
        f_clock = 33000000


    class mscan_333Const(mscanConst):
        f_clock = 33300000


    class mscan_33333333Const(mscanConst):
        f_clock = 33333333


    class mscan_mpc5121_1Const(mscanConst):
        f_clock = 66660000


    class mscan_mpc5121_2Const(mscanConst):
        f_clock = 66666666


    class at91Const(TimingConst):
        tseg1_min = 4
        tseg1_max = 16
        tseg2_min = 2
        tseg2_max = 8
        sjw_max = 4
        brp_min = 2
        brp_max = 128
        brp_inc = 1


    class at91_ronetixConst(at91Const):
        f_clock = 99532800


    class at91_100Const(at91Const):
        f_clock = 100000000


    class flexcanConst(TimingConst):
        tseg1_min = 4
        tseg1_max = 16
        tseg2_min = 2
        tseg2_max = 8
        sjw_max = 4
        brp_min = 1
        brp_max = 256
        brp_inc = 1


    class flexcan_mx28Const(flexcanConst):
        f_clock = 24000000


    class flexcan_mx6Const(flexcanConst):
        f_clock = 30000000


    class flexcan_49Const(flexcanConst):
        f_clock = 49875000


    class flexcan_66Const(flexcanConst):
        f_clock = 66000000


    class flexcan_665Const(flexcanConst):
        f_clock = 66500000


    class flexcan_666Const(flexcanConst):
        f_clock = 66666666


    class flexcan_vybridConst(flexcanConst):
        f_clock = 83368421


    class mcp251xConst(TimingConst):
        tseg1_min = 3
        tseg1_max = 16
        tseg2_min = 2
        tseg2_max = 8
        sjw_max = 4
        brp_min = 1
        brp_max = 64
        brp_inc = 1


    class mcp251x_8Const(mcp251xConst):
        f_clock = 8000000


    class mcp251x_16Const(mcp251xConst):
        f_clock = 16000000


    class ti_heccConst(TimingConst):
        tseg1_min = 1
        tseg1_max = 16
        tseg2_min = 1
        tseg2_max = 8
        sjw_max = 4
        brp_min = 1
        brp_max = 256
        brp_inc = 1
        f_clock = 13000000


    class rcar_canConst(TimingConst):
        tseg1_min = 4
        tseg1_max = 16
        tseg2_min = 2
        tseg2_max = 8
        sjw_max = 4
        brp_min = 1
        brp_max = 1024
        brp_inc = 1
        f_clock = 65000000


    common_bitrates = [
        1000000,
        800000,
        500000,
        250000,
        125000,
        100000,
        50000,
        33000,
        20000,
        10000,
    ]

    classes = [
        sja1000Const,
        mscan_32Const,
        mscan_33Const,
        mscan_333Const,
        mscan_33333333Const,
        mscan_mpc5121_1Const,
        mscan_mpc5121_2Const,
        at91_ronetixConst,
        at91_100Const,
        flexcan_mx28Const,
        flexcan_mx6Const,
        flexcan_49Const,
        flexcan_66Const,
        flexcan_665Const,
        flexcan_666Const,
        flexcan_vybridConst,
        mcp251x_8Const,
        mcp251x_16Const,
        ti_heccConst,
        rcar_canConst
    ]

    for brate in common_bitrates:
        for cls in classes:
            name = cls.__name__.replace('Const', '')
            btiming = BitTiming(brate)
            if btiming.calc_bit_timing(cls):
                print(name, btiming)

                print(
                    'BTR0 BTR1',
                    hex(btiming.btr0)[2:].upper().zfill(2),
                    hex(btiming.btr1)[2:].upper().zfill(2)
                )
                print(
                    'CAN_BR',
                    hex(btiming.can_br)[2:].upper().zfill(8)
                )
                print(
                    'CAN_CTRL',
                    hex(btiming.can_ctrl)[2:].upper().zfill(8)
                )
                print(
                    'CNF1 CNF2 CNF3',
                    hex(btiming.cnf1)[2:].upper().zfill(2),
                    hex(btiming.cnf2)[2:].upper().zfill(2),
                    hex(btiming.cnf3)[2:].upper().zfill(2)
                )
                print(
                    'CANBTC',
                    hex(btiming.canbtc)[2:].upper().zfill(8)
                )
                print(
                    'CiBCR',
                    hex(btiming.cibcr)[2:].upper().zfill(8)
                )
            else:
                print(name, 'timings could not be calculated')

            print()
