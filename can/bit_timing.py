from typing import Optional, Union


def _get_cia_sample_point(bitrate):
    if bitrate > 800000:
        sampl_pt = 75.0
    elif bitrate > 500000:
        sampl_pt = 80.0
    else:
        sampl_pt = 87.5

    return sampl_pt


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
        sample_point: Optional[Union[int, float]] = None,
        calc_tolerance: float = 0.5
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
        self._calc_tolerance = calc_tolerance

        self._prop_seg = None
        self._phase_seg1 = None
        self._phase_seg2 = None

    def __can_calc_bittiming(self, timing_const):
        nominal_bitrate = self._bitrate

        nominal_sample_point = self._sample_point

        if nominal_sample_point is None:
            nominal_sample_point = _get_cia_sample_point(nominal_bitrate)

        match = None

        tmp = timing_const.f_clock / nominal_bitrate
        for brp in range(timing_const.brp_min, timing_const.brp_max + 1, timing_const.brp_inc):
            tmp2 = tmp / brp
            btq = int(round(tmp2))

            if 4 <= btq <= 32:
                err = -(tmp2 / btq - 1)
                err = round(err * 10000) / 100.0

                if abs(err) > self._calc_tolerance:
                    continue

                for tseg1 in range(timing_const.tseg1_min, timing_const.tseg1_max + 1):
                    tseg2 = btq - tseg1
                    if (
                        tseg1 < tseg2 or
                        tseg2 > timing_const.tseg2_max or
                        tseg2 < timing_const.tseg2_min
                    ):
                        continue

                    tseg2 -= 1

                    sample_point = round(tseg1 / btq * 10000) / 100.0
                    bitrate = round(nominal_bitrate * (1 - err))
                    tq = brp * 1000 * 1000 * 1000
                    tq %= timing_const.f_clock
                    prop_seg = tseg1 // 2
                    phase_seg1 = tseg1 - prop_seg
                    phase_seg2 = tseg2

                    if not self._sjw or not timing_const.sjw_max:
                        sjw = 1
                    else:
                        sjw = self._sjw
                        #  bt->sjw is at least 1 -> sanitize upper bound to sjw_max */
                        if sjw > timing_const.sjw_max:
                            sjw = timing_const.sjw_max
                        #  bt->sjw must not be higher than tseg2 */
                        if tseg2 < sjw:
                            continue

                    if bitrate == nominal_bitrate and sample_point == nominal_sample_point:
                        match = (err, bitrate, prop_seg, phase_seg1, phase_seg2, brp, tseg1, tseg2, sjw)
                        break

                    elif match is None:
                        match = (err, bitrate, prop_seg, phase_seg1, phase_seg2, brp, tseg1, tseg2, sjw)

                    elif match[0] > err:
                        match = (err, bitrate, prop_seg, phase_seg1, phase_seg2, brp, tseg1, tseg2, sjw)

                else:
                    continue

                break

        if match is None:
            return False

        (
            bitrate,
            prop_seg,
            phase_seg1,
            phase_seg2,
            brp,
            tseg1,
            tseg2,
            sjw
        ) = match[1:]

        self._bitrate = bitrate
        self._prop_seg = prop_seg
        self._phase_seg1 = phase_seg1
        self._phase_seg2 = phase_seg2
        self._brp = brp
        self._tseg1 = tseg1
        self._tseg2 = tseg2
        self._sjw = sjw
        self._f_clock = timing_const.f_clock

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
        return self.__can_calc_bittiming(timing_const)

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
        tmp = self.f_clock / self.bitrate
        tmp2 = tmp / self.brp
        btq = int(round(tmp2))
        return round(self.tseg1 / btq * 10000) / 100.0

    @property
    def btr0(self) -> int:
        sjw = self.sjw
        brp = self.brp

        if None in (self._prop_seg, self._phase_seg1, self._phase_seg2):
            if brp < 1 or brp > 64:
                raise ValueError("brp must be 1 - 64")
            if sjw < 1 or sjw > 4:
                raise ValueError("sjw must be 1 - 4")

            btr0 = (sjw - 1) << 6 | brp - 1

        else:
            btr0 = (
                ((brp - 1) & 0x3f) |
                (((sjw - 1) & 0x3) << 6)
            )

        return btr0

    @property
    def btr1(self) -> int:
        sam = 1 if self.nof_samples == 3 else 0
        tseg1 = self.tseg1
        tseg2 = self.tseg2

        if None in (self._prop_seg, self._phase_seg1, self._phase_seg2):
            if tseg1 < 1 or tseg1 > 16:
                raise ValueError("tseg1 must be 1 - 16")
            if tseg2 < 1 or tseg2 > 8:
                raise ValueError("tseg2 must be 1 - 8")

            btr1 = sam << 7 | (tseg2 - 1) << 4 | tseg1 - 1
        else:
            btr1 = (
                ((self._prop_seg + self._phase_seg1 - 1) & 0xf) |
                (((self._phase_seg2 - 1) & 0x7) << 4)
            )

        return btr1

    @property
    def can_br(self):
        if None in (self._phase_seg1, self._phase_seg2, self._prop_seg, self._sjw, self._brp):
            return

        br = (
            (self._phase_seg2 - 1) |
            ((self._phase_seg1 - 1) << 4) |
            ((self._prop_seg - 1) << 8) |
            ((self._sjw - 1) << 12) |
            ((self._brp - 1) << 16)
        )
        return br

    @property
    def can_ctrl(self):
        if None in (self._phase_seg1, self._phase_seg2, self._prop_seg, self._sjw, self._brp):
            return

        ctrl = (
            ((self._brp - 1) << 24) |
            ((self._sjw - 1) << 22) |
            ((self._phase_seg1 - 1) << 19) |
            ((self._phase_seg2 - 1) << 16) |
            ((self._prop_seg - 1) << 0)
        )

        return ctrl

    @property
    def cnf1(self):
        if None in (self._brp, self._sjw):
            return

        return ((self._sjw - 1) << 6) | (self._brp - 1)

    @property
    def cnf2(self):
        if None in (self._phase_seg1, self._prop_seg):
            return

        return 0x80 | ((self._phase_seg1 - 1) << 3) | (self._prop_seg - 1)

    @property
    def cnf3(self):
        if self._phase_seg2 is not None:
            return self._phase_seg2 - 1

    @property
    def canbtc(self):
        if None in (self._phase_seg1, self._phase_seg2, self._prop_seg, self._sjw, self._brp):
            return

        can_btc = (self._phase_seg2 - 1) & 0x7
        can_btc |= ((self._phase_seg1 + self._prop_seg - 1) & 0xF) << 3
        can_btc |= ((self._sjw - 1) & 0x3) << 8
        can_btc |= ((self._brp - 1) & 0xFF) << 16

        return can_btc

    @property
    def cibcr(self):
        if None in (self._phase_seg1, self._phase_seg2, self._prop_seg, self._sjw, self._brp):
            return

        def _bcr_tseg1(x):
            return (x & 0x0f) << 20

        def _bcr_bpr(x):
            return (x & 0x3ff) << 8

        def _bcr_sjw(x):
            return (x & 0x3) << 4

        def _bcr_tseg2(x):
            return x & 0x07

        bcr = (
            _bcr_tseg1(self._phase_seg1 + self._prop_seg - 1) |
            _bcr_bpr(self._brp - 1) |
            _bcr_sjw(self._sjw - 1) |
            _bcr_tseg2(self._phase_seg2 - 1)
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
        # mscan_32Const,
        # mscan_33Const,
        # mscan_333Const,
        # mscan_33333333Const,
        # mscan_mpc5121_1Const,
        # mscan_mpc5121_2Const,
        # at91_ronetixConst,
        # at91_100Const,
        # flexcan_mx28Const,
        # flexcan_mx6Const,
        # flexcan_49Const,
        # flexcan_66Const,
        # flexcan_665Const,
        # flexcan_666Const,
        # flexcan_vybridConst,
        # mcp251x_8Const,
        # mcp251x_16Const,
        # ti_heccConst,
        # rcar_canConst
    ]

    TIMING_DICT = {
        5000: (0xBF, 0xFF, 64.00),
        10000: (0x31, 0x1C, 81.25),
        20000: (0x18, 0x1C, 81.25),
        33330: (0x09, 0x6F, 66.67),
        40000: (0x87, 0xFF, 64.00),
        50000: (0x09, 0x1C, 81.25),
        66660: (0x04, 0x6F, 66.67),
        80000: (0x83, 0xFF, 64.00),
        83330: (0x03, 0x6F, 66.67),
        100000: (0x04, 0x1C, 81.25),
        125000: (0x03, 0x1C, 81.25),
        200000: (0x81, 0xFA, 55.0),
        250000: (0x01, 0x1C, 81.25),
        400000: (0x80, 0xFA, 55.0),
        500000: (0x00, 0x1C, 81.25),
        666000: (0x80, 0xB6, 58.33),
        800000: (0x00, 0x16, 70.0),
        1000000: (0x00, 0x14, 62.5),
    }

    for cls in classes:
        name = cls.__name__.replace('Const', '')
        for brate, (t0, t1, smpl) in TIMING_DICT.items():
            btiming = BitTiming(bitrate=brate, sample_point=smpl)
            btiming2 = BitTiming(f_clock=cls.f_clock, bitrate=brate, btr0=t0, btr1=t1)
            if btiming.calc_bit_timing(cls()):
                print(name, 'calculated', btiming)
                print(name, 'from table', btiming2)

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
                print(name, btiming2)
                print(smpl, btiming2.sample_point)


            print()
